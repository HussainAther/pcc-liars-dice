"""Frozen synthetic construct-recovery experiment for Liar's Dice.

The design manipulates Pressure, Control, and Chaos weights orthogonally by
mixing each family with the neutral Bayesian baseline.  Observables use only
public/decision-time information plus aggregate match performance for the
Chaos adequacy floor.  Hidden mixture weights are consulted only after scores
are aggregated for validation.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
import json
import math
from pathlib import Path
import random
import statistics
from typing import Iterable

from .game import Bid, DEFAULT_RULESET, count_face, roll_hands
from .policies import (
    BayesianBaselinePolicy,
    FAMILIES,
    OpponentProfile,
    POLICIES,
    PublicState,
    truth_probability,
)
from .simulate import _profiles_from_history

AXES = ("pressure", "control", "chaos")
LOW_WEIGHT = 0.10
HIGH_WEIGHT = 0.30
BASELINE_NAME = "baseline"
ACTION_CLASSES = ("challenge", "safe_bid", "medium_bid", "bluff_bid")


@dataclass(frozen=True)
class MixtureSpec:
    pressure: float
    control: float
    chaos: float

    @property
    def baseline(self) -> float:
        return 1.0 - self.pressure - self.control - self.chaos

    def as_dict(self) -> dict[str, float]:
        return {
            "pressure": self.pressure,
            "control": self.control,
            "chaos": self.chaos,
            "baseline": self.baseline,
        }


def factorial_specs(low: float = LOW_WEIGHT, high: float = HIGH_WEIGHT) -> tuple[MixtureSpec, ...]:
    specs = []
    for p in (low, high):
        for c in (low, high):
            for h in (low, high):
                spec = MixtureSpec(p, c, h)
                if spec.baseline < 0:
                    raise ValueError("factorial weights exceed one")
                specs.append(spec)
    return tuple(specs)


def _component_names(family: str) -> dict[str, str]:
    names = FAMILIES[family]
    return {axis: name for axis, name in zip(AXES, names)}


def _choose_component(spec: MixtureSpec, rng: random.Random) -> str:
    weights = [spec.pressure, spec.control, spec.chaos, spec.baseline]
    labels = ["pressure", "control", "chaos", "baseline"]
    return rng.choices(labels, weights=weights, k=1)[0]


def _classify_action(action, state: PublicState) -> tuple[str, float | None]:
    if action == "challenge":
        return "challenge", None
    assert isinstance(action, Bid)
    p = truth_probability(state, action)
    if p >= 0.60:
        cls = "safe_bid"
    elif p >= 0.30:
        cls = "medium_bid"
    else:
        cls = "bluff_bid"
    return cls, p


def _state_bin(current_truth: float | None) -> str:
    if current_truth is None:
        return "open"
    if current_truth < 0.20:
        return "lt20"
    if current_truth < 0.35:
        return "20to35"
    if current_truth < 0.55:
        return "35to55"
    return "ge55"


def _profile_bin(profile: OpponentProfile) -> str:
    # Coarse bins fixed prospectively.  They intentionally encode only public
    # opponent history, not opponent identity or hidden policy labels.
    escalation = "highE" if profile.mean_quantity_escalation >= 0.75 else "lowE"
    challenge = "highC" if profile.challenge_rate >= 0.18 else "lowC"
    return f"{escalation}:{challenge}"


def _entropy(counts: Counter[str]) -> float:
    n = sum(counts.values())
    if n <= 1:
        return 0.0
    h = 0.0
    for count in counts.values():
        if count:
            p = count / n
            h -= p * math.log(p)
    return h / math.log(len(ACTION_CLASSES))


def _conditional_entropy(decisions: list[dict]) -> float:
    strata: dict[str, Counter[str]] = defaultdict(Counter)
    for row in decisions:
        strata[row["state_bin"]][row["action_class"]] += 1
    total = len(decisions)
    if total == 0:
        return 0.0
    return sum((sum(c.values()) / total) * _entropy(c) for c in strata.values())


def _conditional_mutual_information(decisions: list[dict]) -> float:
    """I(Action; opponent-profile | current public state bin), normalized.

    The profile is public accumulated opponent behavior.  Conditioning on the
    current-bid truth-probability bin reduces the most obvious state confound.
    """
    by_state: dict[str, list[dict]] = defaultdict(list)
    for row in decisions:
        by_state[row["state_bin"]].append(row)
    total = len(decisions)
    if total == 0:
        return 0.0

    result = 0.0
    norm = math.log(len(ACTION_CLASSES))
    for rows in by_state.values():
        if len(rows) < 4:
            continue
        joint = Counter((r["action_class"], r["profile_bin"]) for r in rows)
        action = Counter(r["action_class"] for r in rows)
        profile = Counter(r["profile_bin"] for r in rows)
        n = len(rows)
        mi = 0.0
        for (a, p), count in joint.items():
            pab = count / n
            pa = action[a] / n
            pp = profile[p] / n
            mi += pab * math.log(pab / (pa * pp))
        result += (n / total) * (mi / norm)
    return result


def _pressure_score(decisions: list[dict], total_dice: int = 10) -> float:
    bids = [r for r in decisions if r["action_class"] != "challenge"]
    if not bids:
        return 0.0
    # Commitment plus upward movement relative to the public bid faced.
    vals = []
    for row in bids:
        commitment = row["bid_quantity"] / total_dice
        escalation = row["quantity_increment"] / total_dice
        vals.append(0.65 * commitment + 0.35 * escalation)
    return sum(vals) / len(vals)


def _adequacy(win_rate: float, floor: float = 0.35, full: float = 0.50) -> float:
    if win_rate <= floor:
        return 0.0
    if win_rate >= full:
        return 1.0
    return (win_rate - floor) / (full - floor)


def score_trajectory(decisions: list[dict], win_rate: float) -> dict[str, float]:
    raw_chaos = _conditional_entropy(decisions)
    adequacy = _adequacy(win_rate)
    return {
        "pressure": _pressure_score(decisions),
        "control": _conditional_mutual_information(decisions),
        "raw_chaos": raw_chaos,
        "chaos": raw_chaos * adequacy,
        "performance_adequacy": adequacy,
        "win_rate": win_rate,
    }


def _play_round_mixture(
    family: str,
    spec: MixtureSpec,
    *,
    mixture_player: int,
    seed: int,
    opener: int,
    prior_public_history: tuple[dict, ...],
) -> tuple[int, list[dict], list[dict]]:
    hands = roll_hands((5, 5), seed, DEFAULT_RULESET.faces)
    rng = random.Random(seed + 991)
    current_bid = None
    history: list[dict] = []
    decisions: list[dict] = []
    actor = opener
    profiles = _profiles_from_history(list(prior_public_history))
    components = _component_names(family)
    baseline = BayesianBaselinePolicy()

    while True:
        opponent = 1 - actor
        state = PublicState(
            actor,
            tuple(hands[actor]),
            (5, 5),
            current_bid,
            tuple(history),
            profiles[opponent],
        )
        current_truth = truth_probability(state, current_bid) if current_bid is not None else None

        if actor == mixture_player:
            component = _choose_component(spec, rng)
            policy = baseline if component == "baseline" else POLICIES[components[component]]
        else:
            component = "baseline-opponent"
            policy = baseline

        action = policy.act(state, rng)
        action_class, selected_truth = _classify_action(action, state)
        if actor == mixture_player:
            increment = 0
            quantity = 0
            if isinstance(action, Bid):
                quantity = action.quantity
                increment = action.quantity - (current_bid.quantity if current_bid is not None else 0)
            decisions.append({
                "state_bin": _state_bin(current_truth),
                "profile_bin": _profile_bin(state.opponent_profile),
                "action_class": action_class,
                "bid_truth_probability": selected_truth,
                "bid_quantity": quantity,
                "quantity_increment": increment,
                # component is diagnostic only and never used by scoring.
                "component": component,
            })

        if action == "challenge":
            if current_bid is None:
                raise RuntimeError("cannot challenge before first bid")
            true_count = count_face(hands, current_bid.face)
            bidder = 1 - actor
            winner = bidder if true_count >= current_bid.quantity else actor
            history.append({"type": "challenge", "player": actor})
            return winner, history, decisions

        if not isinstance(action, Bid):
            raise TypeError("invalid action")
        if current_bid is not None and action <= current_bid:
            raise RuntimeError("policy returned non-increasing bid")
        history.append({"type": "bid", "player": actor, "bid": action})
        current_bid = action
        actor = opponent
        if len(history) > 200:
            raise RuntimeError("round exceeded safety limit")


def evaluate_spec(
    family: str,
    spec: MixtureSpec,
    *,
    rounds_per_order: int,
    seed: int,
) -> dict:
    wins = 0
    total_rounds = 0
    decisions: list[dict] = []

    for mixture_player in (0, 1):
        public_history: list[dict] = []
        for i in range(rounds_per_order):
            opener = i % 2
            winner, round_history, round_decisions = _play_round_mixture(
                family,
                spec,
                mixture_player=mixture_player,
                seed=seed + mixture_player * 1_000_003 + i * 37,
                opener=opener,
                prior_public_history=tuple(public_history),
            )
            wins += int(winner == mixture_player)
            total_rounds += 1
            decisions.extend(round_decisions)
            public_history.extend(round_history)

    win_rate = wins / total_rounds
    scores = score_trajectory(decisions, win_rate)
    return {
        "assigned_weights": spec.as_dict(),
        "rounds": total_rounds,
        "decisions": len(decisions),
        "scores": scores,
    }


def _standardized_effect(rows: list[dict], assigned_axis: str, score_axis: str, low: float, high: float) -> float:
    high_values = [r["scores"][score_axis] for r in rows if r["assigned_weights"][assigned_axis] == high]
    low_values = [r["scores"][score_axis] for r in rows if r["assigned_weights"][assigned_axis] == low]
    mean_diff = statistics.fmean(high_values) - statistics.fmean(low_values)
    all_values = high_values + low_values
    sd = statistics.stdev(all_values) if len(all_values) > 1 else 0.0
    return mean_diff / sd if sd > 1e-12 else 0.0


def _shuffled_null(
    rows: list[dict],
    axis: str,
    score_axis: str,
    *,
    low: float,
    high: float,
    repetitions: int,
    seed: int,
) -> list[float]:
    rng = random.Random(seed)
    labels = [r["assigned_weights"][axis] for r in rows]
    values = [r["scores"][score_axis] for r in rows]
    effects = []
    for _ in range(repetitions):
        shuffled = labels[:]
        rng.shuffle(shuffled)
        high_values = [v for v, label in zip(values, shuffled) if label == high]
        low_values = [v for v, label in zip(values, shuffled) if label == low]
        if not high_values or not low_values:
            effects.append(0.0)
            continue
        diff = statistics.fmean(high_values) - statistics.fmean(low_values)
        sd = statistics.stdev(values) if len(values) > 1 else 0.0
        effects.append(diff / sd if sd > 1e-12 else 0.0)
    return effects


def _quantile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    xs = sorted(values)
    idx = min(len(xs) - 1, max(0, math.ceil(q * len(xs)) - 1))
    return xs[idx]


def run_construct_recovery(
    *,
    replicates: int = 8,
    rounds_per_order: int = 250,
    seed: int = 44001,
    seed_stride: int = 10_000,
    low_weight: float = LOW_WEIGHT,
    high_weight: float = HIGH_WEIGHT,
    minimum_matching_effect: float = 0.50,
    minimum_discriminant_margin: float = 0.20,
    shuffle_repetitions: int = 100,
) -> dict:
    specs = factorial_specs(low_weight, high_weight)
    families = {}

    for family_index, family in enumerate(sorted(FAMILIES)):
        rows = []
        for rep in range(replicates):
            for cell, spec in enumerate(specs):
                result = evaluate_spec(
                    family,
                    spec,
                    rounds_per_order=rounds_per_order,
                    seed=seed + family_index * 1_000_000 + rep * seed_stride + cell * 503,
                )
                result["replicate"] = rep
                result["cell"] = cell
                rows.append(result)

        effects = {}
        axis_checks = {}
        for score_axis in AXES:
            per_assigned = {
                assigned: _standardized_effect(rows, assigned, score_axis, low_weight, high_weight)
                for assigned in AXES
            }
            matching = per_assigned[score_axis]
            cross = max(abs(v) for k, v in per_assigned.items() if k != score_axis)
            margin = matching - cross
            null = _shuffled_null(
                rows,
                score_axis,
                score_axis,
                low=low_weight,
                high=high_weight,
                repetitions=shuffle_repetitions,
                seed=seed + family_index * 77_777 + AXES.index(score_axis) * 997,
            )
            null95 = _quantile(null, 0.95)
            effects[score_axis] = {
                "standardized_effect_by_assigned_axis": per_assigned,
                "matching_effect": matching,
                "largest_absolute_cross_effect": cross,
                "discriminant_margin": margin,
                "shuffled_matching_effect_95th_percentile": null95,
            }
            axis_checks[score_axis] = {
                "matching_effect_large_enough": matching >= minimum_matching_effect,
                "discriminant_margin_large_enough": margin >= minimum_discriminant_margin,
                "beats_shuffled_95th_percentile": matching > null95,
            }

        families[family] = {
            "effects": effects,
            "axis_checks": axis_checks,
            "all_axes_recovered": all(all(c.values()) for c in axis_checks.values()),
            "rows": rows,
        }

    cross_family_axis_status = {
        axis: all(all(families[f]["axis_checks"][axis].values()) for f in families)
        for axis in AXES
    }
    confirmed = all(cross_family_axis_status.values())

    return {
        "schema_version": 1,
        "design": {
            "experiment": "liars-dice-factorial-construct-recovery",
            "families": sorted(FAMILIES),
            "replicates": replicates,
            "rounds_per_order": rounds_per_order,
            "base_seed": seed,
            "seed_stride": seed_stride,
            "fresh_relative_to_balance_and_mechanism_seeds": seed not in (22001, 33001),
            "factorial_weights": {"low": low_weight, "high": high_weight},
            "neutral_baseline_gets_remainder": True,
            "opener_alternates": True,
            "seat_order_balanced": True,
            "policies_modified": False,
            "hidden_weights_used_for_scoring": False,
            "shuffle_repetitions": shuffle_repetitions,
        },
        "candidate_observables": {
            "pressure": "public commitment/escalation score",
            "control": "conditional mutual information between public opponent-profile regime and action, controlling for current-bid truth-probability bin",
            "chaos": "public-state-conditioned action entropy multiplied by an independent aggregate performance-adequacy floor",
        },
        "prespecified_thresholds": {
            "minimum_matching_standardized_effect": minimum_matching_effect,
            "minimum_discriminant_margin": minimum_discriminant_margin,
            "matching_effect_must_exceed_shuffled_95th_percentile": True,
        },
        "families": families,
        "cross_family_axis_status": cross_family_axis_status,
        "liars_dice_construct_recovery_confirmed": confirmed,
        "warning": (
            "Synthetic construct recovery in engineered Liar's Dice agents is a cross-domain validation test. "
            "It is not evidence that human players possess latent PCC states, and failed axes remain failed."
        ),
    }


def write_construct_recovery(path: str | Path, **kwargs) -> dict:
    report = run_construct_recovery(**kwargs)
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report

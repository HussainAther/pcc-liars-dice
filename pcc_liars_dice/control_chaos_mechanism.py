from __future__ import annotations

from collections import defaultdict
import json
from pathlib import Path
import random
import statistics

from .game import Bid, DEFAULT_RULESET, count_face, roll_hands
from .policies import FAMILIES, POLICIES, OpponentProfile, PublicState, truth_probability

DEFAULT_REPLICATES = 10
DEFAULT_ROUNDS = 500
HISTORY_EDGE_REDUCTION = 0.03
CHALLENGE_ACCURACY_MARGIN = 0.05
BID_PLAUSIBILITY_GAP = 0.05
FALSE_FINAL_BID_GAP = 0.05


def _profiles_from_history(match_history: list[dict]) -> tuple[OpponentProfile, OpponentProfile]:
    accum = [defaultdict(float), defaultdict(float)]
    last_bid = None
    for row in match_history:
        player = row["player"]
        accum[player]["public_actions"] += 1
        if row["type"] == "challenge":
            accum[player]["challenges"] += 1
        elif row["type"] == "bid":
            accum[player]["bids"] += 1
            if last_bid is not None:
                accum[player]["quantity_escalation_sum"] += max(0, row["bid"].quantity - last_bid.quantity)
            last_bid = row["bid"]
    return tuple(
        OpponentProfile(
            public_actions=int(a["public_actions"]),
            bids=int(a["bids"]),
            challenges=int(a["challenges"]),
            quantity_escalation_sum=float(a["quantity_escalation_sum"]),
        )
        for a in accum
    )


def _play_traced_round(policy_names, seed, opener, prior_public_history, *, mute_control_history=False):
    hands = roll_hands((5, 5), seed, DEFAULT_RULESET.faces)
    rng = random.Random(seed + 991)
    current_bid = None
    history: list[dict] = []
    decisions: list[dict] = []
    actor = opener
    profiles = _profiles_from_history(list(prior_public_history))
    while True:
        opponent = 1 - actor
        profile = profiles[opponent]
        if mute_control_history and policy_names[actor].endswith(":control"):
            profile = OpponentProfile()
        state = PublicState(actor, tuple(hands[actor]), (5, 5), current_bid, tuple(history), profile)
        current_p = truth_probability(state, current_bid) if current_bid is not None else None
        action = POLICIES[policy_names[actor]].act(state, rng)
        row = {
            "player": actor,
            "policy": policy_names[actor],
            "axis": policy_names[actor].split(":", 1)[1],
            "current_bid_truth_probability": current_p,
        }
        if action == "challenge":
            true_count = count_face(hands, current_bid.face)
            bidder = 1 - actor
            challenge_correct = true_count < current_bid.quantity
            winner = actor if challenge_correct else bidder
            row.update({"action": "challenge", "challenge_correct": challenge_correct})
            decisions.append(row)
            history.append({"type": "challenge", "player": actor})
            return winner, history, decisions, current_bid, true_count
        if not isinstance(action, Bid):
            raise TypeError("invalid action")
        bid_p = truth_probability(state, action)
        row.update({"action": "bid", "bid": action, "bid_truth_probability": bid_p})
        decisions.append(row)
        history.append({"type": "bid", "player": actor, "bid": action})
        current_bid = action
        actor = opponent
        if len(history) > 200:
            raise RuntimeError("round exceeded safety limit")


def _simulate_traced(policy0, policy1, rounds, seed, *, mute_control_history=False):
    wins = [0, 0]
    public_history: list[dict] = []
    decisions: list[dict] = []
    finals = []
    for i in range(rounds):
        winner, hist, rows, final_bid, true_count = _play_traced_round(
            (policy0, policy1), seed + i * 37, i % 2, tuple(public_history),
            mute_control_history=mute_control_history,
        )
        wins[winner] += 1
        public_history.extend(hist)
        decisions.extend(rows)
        finals.append({"bid": final_bid, "true_count": true_count, "false": true_count < final_bid.quantity})
    return {"wins": wins, "decisions": decisions, "finals": finals}


def _axis_decisions(sim, axis):
    return [r for r in sim["decisions"] if r["axis"] == axis]


def _metrics(sim, axis):
    rows = _axis_decisions(sim, axis)
    challenges = [r for r in rows if r["action"] == "challenge"]
    bids = [r for r in rows if r["action"] == "bid"]
    return {
        "decisions": len(rows),
        "challenge_rate": len(challenges) / max(1, len(rows)),
        "challenge_accuracy": sum(bool(r["challenge_correct"]) for r in challenges) / max(1, len(challenges)),
        "mean_challenged_bid_truth_probability": statistics.mean(r["current_bid_truth_probability"] for r in challenges) if challenges else None,
        "mean_bid_truth_probability": statistics.mean(r["bid_truth_probability"] for r in bids) if bids else None,
        "bid_count": len(bids),
        "challenge_count": len(challenges),
    }


def _run_order(control_name, chaos_name, rounds, seed, *, muted=False):
    fwd = _simulate_traced(control_name, chaos_name, rounds, seed, mute_control_history=muted)
    rev = _simulate_traced(chaos_name, control_name, rounds, seed + 500_003, mute_control_history=muted)
    control_wins = fwd["wins"][0] + rev["wins"][1]
    n = 2 * rounds
    combined = {"decisions": fwd["decisions"] + rev["decisions"], "finals": fwd["finals"] + rev["finals"]}
    return control_wins / n, combined


def run_control_chaos_mechanism(*, replicates=DEFAULT_REPLICATES, rounds_per_order=DEFAULT_ROUNDS, seed=33001):
    families = {}
    for family, names in FAMILIES.items():
        control = next(n for n in names if n.endswith(":control"))
        chaos = next(n for n in names if n.endswith(":chaos"))
        reps = []
        for rep in range(replicates):
            s = seed + rep * 1009 + (0 if family == "family-a" else 100_000)
            full_rate, full = _run_order(control, chaos, rounds_per_order, s, muted=False)
            muted_rate, muted = _run_order(control, chaos, rounds_per_order, s, muted=True)
            cm = _metrics(full, "control")
            hm = _metrics(full, "chaos")
            false_rate = sum(r["false"] for r in full["finals"]) / max(1, len(full["finals"]))
            reps.append({
                "replicate": rep,
                "control_win_rate": full_rate,
                "control_win_rate_history_muted": muted_rate,
                "history_edge_reduction": full_rate - muted_rate,
                "control": cm,
                "chaos": hm,
                "control_minus_chaos_challenge_accuracy": cm["challenge_accuracy"] - hm["challenge_accuracy"],
                "control_minus_chaos_bid_plausibility": cm["mean_bid_truth_probability"] - hm["mean_bid_truth_probability"],
                "false_final_bid_rate": false_rate,
            })
        def mean(key):
            return statistics.mean(r[key] for r in reps)
        summary = {
            "control_win_rate": mean("control_win_rate"),
            "control_win_rate_history_muted": mean("control_win_rate_history_muted"),
            "history_edge_reduction": mean("history_edge_reduction"),
            "control_minus_chaos_challenge_accuracy": mean("control_minus_chaos_challenge_accuracy"),
            "control_minus_chaos_bid_plausibility": mean("control_minus_chaos_bid_plausibility"),
            "false_final_bid_rate": mean("false_final_bid_rate"),
            "control_challenge_accuracy": statistics.mean(r["control"]["challenge_accuracy"] for r in reps),
            "chaos_challenge_accuracy": statistics.mean(r["chaos"]["challenge_accuracy"] for r in reps),
            "control_mean_bid_truth_probability": statistics.mean(r["control"]["mean_bid_truth_probability"] for r in reps),
            "chaos_mean_bid_truth_probability": statistics.mean(r["chaos"]["mean_bid_truth_probability"] for r in reps),
        }
        pathways = {
            "history_dependence_supported": summary["history_edge_reduction"] >= HISTORY_EDGE_REDUCTION,
            "challenge_timing_supported": summary["control_minus_chaos_challenge_accuracy"] >= CHALLENGE_ACCURACY_MARGIN,
            "chaos_lower_bid_plausibility_supported": summary["control_minus_chaos_bid_plausibility"] >= BID_PLAUSIBILITY_GAP,
        }
        families[family] = {"summary": summary, "pathways": pathways, "replicates": reps}

    pathway_counts = {
        p: sum(int(f["pathways"][p]) for f in families.values())
        for p in ("history_dependence_supported", "challenge_timing_supported", "chaos_lower_bid_plausibility_supported")
    }
    dominant = [p for p, count in pathway_counts.items() if count == len(families)]
    return {
        "schema_version": 1,
        "design": {
            "replicates": replicates,
            "rounds_per_order": rounds_per_order,
            "seed": seed,
            "fresh_relative_to_balance_seed": True,
            "policies_modified": False,
            "seat_and_opener_balanced": True,
            "history_intervention": "replace only Control's public opponent profile with an empty profile; policy code and thresholds unchanged",
            "thresholds": {
                "minimum_history_edge_reduction": HISTORY_EDGE_REDUCTION,
                "minimum_challenge_accuracy_margin": CHALLENGE_ACCURACY_MARGIN,
                "minimum_bid_plausibility_gap": BID_PLAUSIBILITY_GAP,
            },
        },
        "families": families,
        "cross_family_pathway_counts": pathway_counts,
        "cross_family_supported_pathways": dominant,
        "mechanism_decomposition_supported": bool(dominant),
        "warning": "This diagnoses engineered synthetic Liar's Dice policies. It is not evidence that human players possess PCC states or that poker mechanisms transfer unchanged.",
    }


def write_control_chaos_mechanism(path: str | Path, **kwargs):
    report = run_control_chaos_mechanism(**kwargs)
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report

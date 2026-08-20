from __future__ import annotations

from dataclasses import dataclass
import math
import random

from .game import Bid, legal_bids
from .probability import bid_truth_probability


@dataclass(frozen=True)
class OpponentProfile:
    public_actions: int = 0
    bids: int = 0
    challenges: int = 0
    quantity_escalation_sum: float = 0.0

    @property
    def challenge_rate(self) -> float:
        return self.challenges / max(1, self.public_actions)

    @property
    def mean_quantity_escalation(self) -> float:
        return self.quantity_escalation_sum / max(1, self.bids)


@dataclass(frozen=True)
class PublicState:
    player: int
    own_dice: tuple[int, ...]
    dice_counts: tuple[int, ...]
    current_bid: Bid | None
    history: tuple[dict, ...]
    opponent_profile: OpponentProfile = OpponentProfile()

    @property
    def total_dice(self) -> int:
        return sum(self.dice_counts)


def truth_probability(state: PublicState, bid: Bid) -> float:
    return bid_truth_probability(state.own_dice, state.total_dice, bid)


def _legal(state: PublicState) -> tuple[Bid, ...]:
    return legal_bids(state.current_bid, state.total_dice)


class BayesianBaselinePolicy:
    """Non-PCC reference policy based only on information-set plausibility."""

    name = "baseline"

    def act(self, state: PublicState, rng: random.Random):
        if state.current_bid is not None and truth_probability(state, state.current_bid) < 0.30:
            return "challenge"
        bids = _legal(state)
        if not bids:
            return "challenge"
        # Prefer a modestly assertive bid whose truth probability remains near 0.55.
        return min(
            bids,
            key=lambda b: (
                abs(truth_probability(state, b) - 0.55),
                b.quantity,
                b.face,
            ),
        )


# Family A: probability-score mechanisms. These policies share the rules/probability
# utilities but use different explicit mechanisms. They are not fitted from outcomes.
class FamilyAPressurePolicy:
    name = "family-a:pressure"

    def act(self, state: PublicState, rng: random.Random):
        if state.current_bid is not None and truth_probability(state, state.current_bid) < 0.20:
            return "challenge"
        bids = _legal(state)
        if not bids:
            return "challenge"
        plausible = [b for b in bids if truth_probability(state, b) >= 0.24]
        pool = plausible or bids
        # Highest commitment still above a fixed information-set plausibility floor.
        return max(pool, key=lambda b: (b.quantity, b.face))


class FamilyAControlPolicy:
    name = "family-a:control"

    def act(self, state: PublicState, rng: random.Random):
        profile = state.opponent_profile
        # Public opponent behavior shifts willingness to call an apparent bluff.
        challenge_cutoff = 0.30 + min(0.10, 0.04 * profile.mean_quantity_escalation)
        if state.current_bid is not None and truth_probability(state, state.current_bid) < challenge_cutoff:
            return "challenge"
        bids = _legal(state)
        if not bids:
            return "challenge"
        target = 0.58 - min(0.10, 0.30 * profile.challenge_rate)
        return min(
            bids,
            key=lambda b: (
                abs(truth_probability(state, b) - target),
                b.quantity,
                b.face,
            ),
        )


class FamilyAChaosPolicy:
    name = "family-a:chaos"

    def act(self, state: PublicState, rng: random.Random):
        if state.current_bid is not None:
            p_true = truth_probability(state, state.current_bid)
            challenge_probability = 0.10 + 0.55 * max(0.0, 0.45 - p_true) / 0.45
            if rng.random() < challenge_probability:
                return "challenge"
        bids = list(_legal(state))
        if not bids:
            return "challenge"
        viable = [b for b in bids if truth_probability(state, b) >= 0.10] or bids
        weights = [math.exp(-2.0 * abs(truth_probability(state, b) - 0.42)) for b in viable]
        return rng.choices(viable, weights=weights, k=1)[0]


# Family B: independently structured threshold/heuristic mechanisms. It avoids
# Family A's target-probability scoring rule so construct transfer is not tautological.
class FamilyBPressurePolicy:
    name = "family-b:pressure"

    def act(self, state: PublicState, rng: random.Random):
        if state.current_bid is not None and truth_probability(state, state.current_bid) <= 0.16:
            return "challenge"
        bids = _legal(state)
        if not bids:
            return "challenge"
        # Walk upward until the next increase crosses a conservative bluff boundary.
        candidate = bids[0]
        for bid in bids:
            if truth_probability(state, bid) < 0.27:
                break
            candidate = bid
        return candidate


class FamilyBControlPolicy:
    name = "family-b:control"

    def act(self, state: PublicState, rng: random.Random):
        profile = state.opponent_profile
        current = state.current_bid
        if current is not None:
            p_true = truth_probability(state, current)
            aggressive_opponent = profile.mean_quantity_escalation >= 0.8
            if (aggressive_opponent and p_true < 0.38) or p_true < 0.24:
                return "challenge"
        bids = _legal(state)
        if not bids:
            return "challenge"
        # Use a discrete adaptation rule rather than an optimization score.
        threshold = 0.50 if profile.challenge_rate < 0.18 else 0.62
        acceptable = [b for b in bids if truth_probability(state, b) >= threshold]
        return acceptable[-1] if acceptable else bids[0]


class FamilyBChaosPolicy:
    name = "family-b:chaos"

    def act(self, state: PublicState, rng: random.Random):
        current = state.current_bid
        if current is not None:
            p_true = truth_probability(state, current)
            if (p_true < 0.22 and rng.random() < 0.70) or rng.random() < 0.08:
                return "challenge"
        bids = list(_legal(state))
        if not bids:
            return "challenge"
        # Mix two qualitatively different but value-bounded bidding modes.
        conservative = [b for b in bids if truth_probability(state, b) >= 0.60]
        bluffing = [b for b in bids if 0.18 <= truth_probability(state, b) < 0.60]
        if rng.random() < 0.55 and conservative:
            return rng.choice(conservative)
        if bluffing:
            return rng.choice(bluffing)
        return bids[0]


POLICIES = {
    p.name: p
    for p in (
        BayesianBaselinePolicy(),
        FamilyAPressurePolicy(),
        FamilyAControlPolicy(),
        FamilyAChaosPolicy(),
        FamilyBPressurePolicy(),
        FamilyBControlPolicy(),
        FamilyBChaosPolicy(),
    )
}

FAMILIES = {
    "family-a": ("family-a:pressure", "family-a:control", "family-a:chaos"),
    "family-b": ("family-b:pressure", "family-b:control", "family-b:chaos"),
}

from __future__ import annotations

from collections import defaultdict
import random

from .game import Bid, DEFAULT_RULESET, RoundResult, count_face, roll_hands
from .policies import OpponentProfile, POLICIES, PublicState


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


def play_round(
    policy_names=("family-a:pressure", "family-a:control"),
    dice_counts=(5, 5),
    seed=1,
    opener: int = 0,
    prior_public_history: tuple[dict, ...] = (),
) -> RoundResult:
    if len(policy_names) != 2 or len(dice_counts) != 2:
        raise ValueError("v0.2 supports heads-up rounds only")
    if opener not in (0, 1):
        raise ValueError("opener must be 0 or 1")
    hands = roll_hands(dice_counts, seed, DEFAULT_RULESET.faces)
    rng = random.Random(seed + 991)
    current_bid = None
    history: list[dict] = []
    actor = opener
    profiles = _profiles_from_history(list(prior_public_history))

    while True:
        opponent = 1 - actor
        state = PublicState(
            actor,
            tuple(hands[actor]),
            tuple(dice_counts),
            current_bid,
            tuple(history),
            profiles[opponent],
        )
        action = POLICIES[policy_names[actor]].act(state, rng)
        if action == "challenge":
            if current_bid is None:
                raise RuntimeError("cannot challenge before first bid")
            true_count = count_face(hands, current_bid.face)
            bidder = 1 - actor
            winner, loser = (bidder, actor) if true_count >= current_bid.quantity else (actor, bidder)
            history.append({"type": "challenge", "player": actor})
            return RoundResult(winner, loser, current_bid, actor, true_count, history, opener)
        if not isinstance(action, Bid):
            raise TypeError("invalid action")
        if current_bid is not None and action <= current_bid:
            raise RuntimeError("policy returned non-increasing bid")
        history.append({"type": "bid", "player": actor, "bid": action})
        current_bid = action
        actor = 1 - actor
        if len(history) > 200:
            raise RuntimeError("round exceeded safety limit")


def simulate_match(policy0: str, policy1: str, rounds: int = 100, seed: int = 1) -> dict:
    wins = [0, 0]
    margins = []
    lengths = []
    public_history: list[dict] = []
    for i in range(rounds):
        opener = i % 2
        r = play_round(
            (policy0, policy1),
            seed=seed + i * 37,
            opener=opener,
            prior_public_history=tuple(public_history),
        )
        wins[r.winner] += 1
        margins.append(r.true_count - r.final_bid.quantity)
        lengths.append(len(r.history))
        public_history.extend(r.history)
    return {
        "policies": [policy0, policy1],
        "rounds": rounds,
        "seed": seed,
        "opener_alternates": True,
        "wins": wins,
        "win_rates": [w / rounds for w in wins],
        "mean_truth_margin": sum(margins) / rounds,
        "mean_round_actions": sum(lengths) / rounds,
    }

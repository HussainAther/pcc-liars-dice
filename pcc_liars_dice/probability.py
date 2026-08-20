from __future__ import annotations

import math
from .game import Bid


def binomial_tail(n: int, p: float, at_least: int) -> float:
    """P[X >= at_least] for X~Binomial(n,p), computed exactly for small n."""
    if at_least <= 0:
        return 1.0
    if at_least > n:
        return 0.0
    return sum(
        math.comb(n, k) * (p**k) * ((1.0 - p) ** (n - k))
        for k in range(at_least, n + 1)
    )


def bid_truth_probability(own_dice: tuple[int, ...], total_dice: int, bid: Bid, faces: int = 6) -> float:
    """Bayesian probability that a public bid is true from one player's information set.

    No opponent identity, PCC label, or future outcome enters this probability.
    """
    known = sum(1 for die in own_dice if die == bid.face)
    unknown = total_dice - len(own_dice)
    needed = bid.quantity - known
    return binomial_tail(unknown, 1.0 / faces, needed)

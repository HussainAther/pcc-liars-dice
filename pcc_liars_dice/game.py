from __future__ import annotations

from dataclasses import dataclass
import random
from typing import Sequence


@dataclass(frozen=True)
class Ruleset:
    """Frozen v0.2 laboratory rules.

    The laboratory uses a deliberately simple heads-up Liar's Dice variant:
    five dice per player, faces 1..6, no wild faces, lexicographic bidding by
    (quantity, face), and a challenge that immediately ends the round.
    """

    dice_per_player: int = 5
    faces: int = 6
    ones_wild: bool = False

    def validate(self) -> None:
        if self.dice_per_player < 1:
            raise ValueError("dice_per_player must be positive")
        if self.faces < 2:
            raise ValueError("faces must be at least 2")
        if self.ones_wild:
            raise ValueError("v0.2 laboratory rules do not use wild ones")


DEFAULT_RULESET = Ruleset()


@dataclass(frozen=True, order=True)
class Bid:
    quantity: int
    face: int

    def __post_init__(self):
        if self.quantity < 1:
            raise ValueError("quantity must be positive")
        if not 1 <= self.face <= 6:
            raise ValueError("face must be in 1..6")


def is_higher_bid(new: Bid, old: Bid | None) -> bool:
    return old is None or (new.quantity, new.face) > (old.quantity, old.face)


def legal_bids(old: Bid | None, total_dice: int, faces: int = 6) -> tuple[Bid, ...]:
    return tuple(
        Bid(q, f)
        for q in range(1, total_dice + 1)
        for f in range(1, faces + 1)
        if is_higher_bid(Bid(q, f), old)
    )


def count_face(dice: Sequence[Sequence[int]], face: int) -> int:
    return sum(1 for hand in dice for die in hand if die == face)


@dataclass
class RoundResult:
    winner: int
    loser: int
    final_bid: Bid
    challenged_by: int
    true_count: int
    history: list[dict]
    opener: int


def roll_hands(dice_counts: Sequence[int], seed: int, faces: int = 6) -> list[list[int]]:
    rng = random.Random(seed)
    return [[rng.randint(1, faces) for _ in range(n)] for n in dice_counts]

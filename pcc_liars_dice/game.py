from __future__ import annotations
from dataclasses import dataclass
import random
from typing import Sequence

@dataclass(frozen=True, order=True)
class Bid:
    quantity: int
    face: int
    def __post_init__(self):
        if self.quantity < 1:
            raise ValueError('quantity must be positive')
        if not 1 <= self.face <= 6:
            raise ValueError('face must be in 1..6')

def is_higher_bid(new: Bid, old: Bid | None) -> bool:
    return old is None or (new.quantity, new.face) > (old.quantity, old.face)

def legal_bids(old: Bid | None, total_dice: int) -> tuple[Bid, ...]:
    return tuple(Bid(q, f) for q in range(1, total_dice + 1) for f in range(1, 7) if is_higher_bid(Bid(q, f), old))

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

def roll_hands(dice_counts: Sequence[int], seed: int) -> list[list[int]]:
    rng = random.Random(seed)
    return [[rng.randint(1, 6) for _ in range(n)] for n in dice_counts]

from __future__ import annotations
from dataclasses import dataclass
import math, random
from .game import Bid, legal_bids

@dataclass
class PublicState:
    player: int
    own_dice: tuple[int, ...]
    dice_counts: tuple[int, ...]
    current_bid: Bid | None
    history: tuple[dict, ...]

def own_support(state: PublicState, face: int) -> int:
    return sum(1 for d in state.own_dice if d == face)

def expected_total_count(state: PublicState, face: int) -> float:
    known = own_support(state, face)
    unknown = sum(state.dice_counts) - len(state.own_dice)
    return known + unknown / 6.0

def bid_strain(state: PublicState, bid: Bid) -> float:
    exp = expected_total_count(state, bid.face)
    return max(0.0, (bid.quantity - exp) / max(1.0, sum(state.dice_counts)))

class PressurePolicy:
    name = 'pressure'
    def act(self, state: PublicState, rng: random.Random):
        if state.current_bid is not None and bid_strain(state, state.current_bid) > 0.42:
            return 'challenge'
        bids = legal_bids(state.current_bid, sum(state.dice_counts))
        if not bids:
            return 'challenge'
        plausible = [b for b in bids if bid_strain(state, b) <= 0.18]
        pool = plausible or bids
        # escalate toward the upper edge of plausible commitments, not arbitrary maximum bids
        return max((b.quantity + 0.05*b.face - 2.0*bid_strain(state,b), b) for b in pool)[1]

class ControlPolicy:
    name = 'control'
    def act(self, state: PublicState, rng: random.Random):
        if state.current_bid is not None:
            recent = [h for h in state.history[-4:] if h.get('type') == 'bid']
            escalation = recent[-1]['bid'].quantity - recent[-2]['bid'].quantity if len(recent) >= 2 else 0.0
            if bid_strain(state, state.current_bid) + 0.12*max(0, escalation) > 0.38:
                return 'challenge'
        bids = legal_bids(state.current_bid, sum(state.dice_counts))
        if not bids:
            return 'challenge'
        recent_q = [h['bid'].quantity for h in state.history[-4:] if h.get('type') == 'bid']
        pace = (recent_q[-1]-recent_q[0])/max(1,len(recent_q)-1) if len(recent_q) >= 2 else 0.0
        return max((-abs(b.quantity-expected_total_count(state,b.face)) - 0.15*max(0.0,pace)*b.quantity, b) for b in bids)[1]

class ChaosPolicy:
    name = 'chaos'
    def act(self, state: PublicState, rng: random.Random):
        if state.current_bid is not None and rng.random() < 0.18 + 0.35*bid_strain(state,state.current_bid):
            return 'challenge'
        bids = list(legal_bids(state.current_bid, sum(state.dice_counts)))
        if not bids:
            return 'challenge'
        plausible = [b for b in bids if bid_strain(state,b) < 0.42] or bids
        weights = [math.exp(-4.0*bid_strain(state,b)) for b in plausible]
        return rng.choices(plausible, weights=weights, k=1)[0]

POLICIES = {p.name:p for p in (PressurePolicy(), ControlPolicy(), ChaosPolicy())}

from __future__ import annotations
import random
from .game import Bid, RoundResult, count_face, roll_hands
from .policies import PublicState, POLICIES

def play_round(policy_names=('pressure','control'), dice_counts=(5,5), seed=1) -> RoundResult:
    if len(policy_names) != 2 or len(dice_counts) != 2:
        raise ValueError('v0.1 supports heads-up rounds only')
    hands = roll_hands(dice_counts, seed)
    rng = random.Random(seed + 991)
    current_bid = None
    history = []
    actor = 0
    while True:
        state = PublicState(actor, tuple(hands[actor]), tuple(dice_counts), current_bid, tuple(history))
        action = POLICIES[policy_names[actor]].act(state, rng)
        if action == 'challenge':
            if current_bid is None:
                raise RuntimeError('cannot challenge before first bid')
            true_count = count_face(hands, current_bid.face)
            bidder = 1 - actor
            winner, loser = (bidder, actor) if true_count >= current_bid.quantity else (actor, bidder)
            history.append({'type':'challenge','player':actor})
            return RoundResult(winner, loser, current_bid, actor, true_count, history)
        if not isinstance(action, Bid):
            raise TypeError('invalid action')
        history.append({'type':'bid','player':actor,'bid':action})
        current_bid = action
        actor = 1 - actor
        if len(history) > 200:
            raise RuntimeError('round exceeded safety limit')

def simulate_match(policy0: str, policy1: str, rounds: int=100, seed: int=1) -> dict:
    wins=[0,0]; margins=[]; lengths=[]
    for i in range(rounds):
        r=play_round((policy0,policy1), seed=seed+i*37)
        wins[r.winner]+=1; margins.append(r.true_count-r.final_bid.quantity); lengths.append(len(r.history))
    return {'policies':[policy0,policy1],'rounds':rounds,'seed':seed,'wins':wins,'win_rates':[w/rounds for w in wins],'mean_truth_margin':sum(margins)/rounds,'mean_round_actions':sum(lengths)/rounds}

from __future__ import annotations
import math
from collections import Counter

def pressure_observable(history: list[dict]) -> float:
    bids=[h['bid'] for h in history if h.get('type')=='bid']
    if len(bids)<2: return 0.0
    escalation=sum(max(0,b.quantity-a.quantity) for a,b in zip(bids,bids[1:]))
    challenge=1.0 if history and history[-1].get('type')=='challenge' else 0.0
    return escalation/max(1,len(bids)-1)+0.25*challenge

def history_alignment_observable(history: list[dict]) -> float:
    bids=[h['bid'].quantity for h in history if h.get('type')=='bid']
    if len(bids)<3: return 0.0
    diffs=[b-a for a,b in zip(bids,bids[1:])]
    mean=sum(diffs)/len(diffs)
    var=sum((d-mean)**2 for d in diffs)/len(diffs)
    return 1.0/(1.0+var)

def behavioral_surprisal(actions: list[str]) -> float:
    if not actions: return 0.0
    c=Counter(actions); n=len(actions)
    return sum(-math.log(c[a]/n) for a in actions)/n

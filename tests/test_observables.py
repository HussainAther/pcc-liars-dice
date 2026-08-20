from pcc_liars_dice.game import Bid
from pcc_liars_dice.observables import pressure_observable, history_alignment_observable, behavioral_surprisal

def test_pressure_increases_with_escalation():
    low=[{'type':'bid','bid':Bid(1,1)},{'type':'bid','bid':Bid(1,2)}]
    high=[{'type':'bid','bid':Bid(1,1)},{'type':'bid','bid':Bid(4,1)}]
    assert pressure_observable(high)>pressure_observable(low)

def test_alignment_rewards_regular_pace():
    regular=[{'type':'bid','bid':Bid(q,1)} for q in (1,2,3,4)]
    irregular=[{'type':'bid','bid':Bid(q,1)} for q in (1,2,5,6)]
    assert history_alignment_observable(regular)>history_alignment_observable(irregular)

def test_surprisal_nonnegative():
    assert behavioral_surprisal(['bid','bid','challenge'])>=0

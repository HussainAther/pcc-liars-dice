from pcc_liars_dice.simulate import play_round, simulate_match

def test_round_terminates():
    r=play_round(('pressure','control'), seed=3)
    assert r.winner in (0,1)
    assert r.loser==1-r.winner
    assert r.history[-1]['type']=='challenge'

def test_match_deterministic():
    assert simulate_match('pressure','chaos',20,11)==simulate_match('pressure','chaos',20,11)

def test_match_counts_rounds():
    r=simulate_match('control','chaos',25,2)
    assert sum(r['wins'])==25

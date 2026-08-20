from pcc_liars_dice.game import Bid, is_higher_bid, legal_bids, count_face, roll_hands

def test_bid_ordering():
    assert is_higher_bid(Bid(2,1), Bid(1,6))
    assert is_higher_bid(Bid(2,3), Bid(2,2))
    assert not is_higher_bid(Bid(2,2), Bid(2,3))

def test_legal_bids_only_higher():
    old=Bid(2,4)
    assert all(is_higher_bid(b, old) for b in legal_bids(old, 10))

def test_rolls_are_deterministic():
    assert roll_hands((5,5), 7) == roll_hands((5,5), 7)

def test_count_face():
    assert count_face([[1,2,2],[2,4]],2)==3

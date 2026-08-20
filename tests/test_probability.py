from pcc_liars_dice.game import Bid
from pcc_liars_dice.probability import binomial_tail, bid_truth_probability


def test_binomial_tail_boundaries():
    assert binomial_tail(5, 1/6, 0) == 1.0
    assert binomial_tail(5, 1/6, 6) == 0.0


def test_known_support_increases_truth_probability():
    bid = Bid(3, 2)
    low = bid_truth_probability((1, 3, 4, 5, 6), 10, bid)
    high = bid_truth_probability((2, 2, 4, 5, 6), 10, bid)
    assert high > low

import random
from pcc_liars_dice.game import Bid
from pcc_liars_dice.policies import FAMILIES, POLICIES, PublicState


def make_state(current=None, history=()):
    return PublicState(0, (2, 2, 5, 6, 1), (5, 5), current, tuple(history))


def test_all_policies_open_with_bid():
    for p in POLICIES.values():
        assert isinstance(p.act(make_state(), random.Random(1)), Bid)


def test_all_policies_return_legal_action():
    state = make_state(Bid(2, 3), ({"type": "bid", "player": 1, "bid": Bid(2, 3)},))
    for p in POLICIES.values():
        action = p.act(state, random.Random(2))
        assert action == "challenge" or action > Bid(2, 3)


def test_two_complete_policy_families_exist():
    assert set(FAMILIES) == {"family-a", "family-b"}
    for family, names in FAMILIES.items():
        assert {name.split(":")[1] for name in names} == {"pressure", "control", "chaos"}

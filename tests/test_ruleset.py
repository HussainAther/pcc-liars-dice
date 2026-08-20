import pytest
from pcc_liars_dice.game import DEFAULT_RULESET, Ruleset


def test_default_ruleset_is_frozen_simple_variant():
    assert DEFAULT_RULESET.dice_per_player == 5
    assert DEFAULT_RULESET.faces == 6
    assert DEFAULT_RULESET.ones_wild is False
    DEFAULT_RULESET.validate()


def test_wild_ones_not_silently_enabled():
    with pytest.raises(ValueError):
        Ruleset(ones_wild=True).validate()

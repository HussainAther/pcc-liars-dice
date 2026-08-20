from pcc_liars_dice.construct_recovery import (
    factorial_specs,
    run_construct_recovery,
    score_trajectory,
)


def test_factorial_weights_are_orthogonal_with_neutral_remainder():
    specs = factorial_specs()
    assert len(specs) == 8
    assert {s.pressure for s in specs} == {0.10, 0.30}
    assert {s.control for s in specs} == {0.10, 0.30}
    assert {s.chaos for s in specs} == {0.10, 0.30}
    assert all(abs(sum(s.as_dict().values()) - 1.0) < 1e-12 for s in specs)
    assert min(s.baseline for s in specs) >= 0.10 - 1e-12


def test_chaos_score_has_performance_floor():
    decisions = [
        {"state_bin": "open", "profile_bin": "lowE:lowC", "action_class": a,
         "bid_quantity": 2, "quantity_increment": 1}
        for a in ("safe_bid", "medium_bid", "bluff_bid", "challenge") * 5
    ]
    weak = score_trajectory(decisions, 0.30)
    adequate = score_trajectory(decisions, 0.55)
    assert weak["raw_chaos"] > 0
    assert weak["chaos"] == 0
    assert adequate["chaos"] == adequate["raw_chaos"]


def test_small_construct_recovery_report_has_frozen_structure():
    r = run_construct_recovery(
        replicates=1,
        rounds_per_order=20,
        seed=9901,
        shuffle_repetitions=5,
    )
    assert set(r["families"]) == {"family-a", "family-b"}
    assert set(r["cross_family_axis_status"]) == {"pressure", "control", "chaos"}
    assert r["design"]["policies_modified"] is False
    assert r["design"]["hidden_weights_used_for_scoring"] is False
    for family in r["families"].values():
        assert len(family["rows"]) == 8
        assert set(family["axis_checks"]) == {"pressure", "control", "chaos"}

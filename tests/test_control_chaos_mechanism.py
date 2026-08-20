from pcc_liars_dice.control_chaos_mechanism import run_control_chaos_mechanism


def test_mechanism_report_covers_two_families_and_frozen_pathways():
    r = run_control_chaos_mechanism(replicates=1, rounds_per_order=30, seed=901)
    assert set(r["families"]) == {"family-a", "family-b"}
    for f in r["families"].values():
        assert set(f["pathways"]) == {
            "history_dependence_supported",
            "challenge_timing_supported",
            "chaos_lower_bid_plausibility_supported",
        }
    assert r["design"]["policies_modified"] is False


def test_history_intervention_is_diagnostic_not_policy_tuning():
    r = run_control_chaos_mechanism(replicates=1, rounds_per_order=20, seed=902)
    assert "empty profile" in r["design"]["history_intervention"]
    assert r["design"]["fresh_relative_to_balance_seed"] is True

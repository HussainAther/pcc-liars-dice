from pcc_liars_dice.balance import run_balance_protocol


def test_balance_protocol_reports_both_independent_families():
    report = run_balance_protocol(replicates=1, rounds_per_order=20, seed=9)
    assert set(report["families"]) == {"family-a", "family-b"}
    assert report["design"]["seat_and_opener_balanced"] is True
    assert report["prespecified_checks"]["no_cycle_required"] is True


def test_balance_pairs_cover_three_axis_pairs():
    report = run_balance_protocol(replicates=1, rounds_per_order=10, seed=3)
    for family in report["families"].values():
        pairs = {(r["left"], r["right"]) for r in family["pairwise"]}
        assert pairs == {("pressure", "control"), ("pressure", "chaos"), ("control", "chaos")}

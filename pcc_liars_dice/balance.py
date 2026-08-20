from __future__ import annotations

import json
from itertools import combinations
from pathlib import Path

from .policies import FAMILIES
from .simulate import simulate_match


DEFAULT_REPLICATES = 8
DEFAULT_ROUNDS = 400
MAX_PAIRWISE_WIN_RATE = 0.70
MIN_PAIRWISE_WIN_RATE = 0.30


def _axis(name: str) -> str:
    return name.split(":", 1)[1]


def run_balance_protocol(
    *,
    replicates: int = DEFAULT_REPLICATES,
    rounds_per_order: int = DEFAULT_ROUNDS,
    seed: int = 22001,
) -> dict:
    """Run a frozen, seat-order-balanced competitiveness diagnostic.

    This protocol does not require or reward a rock-paper-scissors cycle.
    It asks only whether every pair remains meaningfully competitive.
    """
    family_reports = {}
    for family, names in FAMILIES.items():
        rows = []
        pair_checks = []
        for left, right in combinations(names, 2):
            left_wins = 0
            total = 0
            replicate_rates = []
            for rep in range(replicates):
                s = seed + rep * 1009 + len(rows) * 17
                forward = simulate_match(left, right, rounds_per_order, s)
                reverse = simulate_match(right, left, rounds_per_order, s + 500_003)
                wins = forward["wins"][0] + reverse["wins"][1]
                n = 2 * rounds_per_order
                rate = wins / n
                left_wins += wins
                total += n
                replicate_rates.append(rate)
            rate = left_wins / total
            competitive = MIN_PAIRWISE_WIN_RATE <= rate <= MAX_PAIRWISE_WIN_RATE
            row = {
                "left": _axis(left),
                "right": _axis(right),
                "left_win_rate": rate,
                "right_win_rate": 1.0 - rate,
                "replicate_rates": replicate_rates,
                "competitive": competitive,
            }
            rows.append(row)
            pair_checks.append(competitive)
        family_reports[family] = {
            "pairwise": rows,
            "all_pairs_competitive": all(pair_checks),
        }

    checks = {
        "family_a_all_pairs_competitive": family_reports["family-a"]["all_pairs_competitive"],
        "family_b_all_pairs_competitive": family_reports["family-b"]["all_pairs_competitive"],
        "no_cycle_required": True,
        "no_construct_recovery_used_for_balance": True,
    }
    return {
        "schema_version": 1,
        "design": {
            "replicates": replicates,
            "rounds_per_order": rounds_per_order,
            "seed": seed,
            "seat_and_opener_balanced": True,
            "minimum_pairwise_win_rate": MIN_PAIRWISE_WIN_RATE,
            "maximum_pairwise_win_rate": MAX_PAIRWISE_WIN_RATE,
            "criterion": "competitiveness only; a cyclic dominance pattern is neither required nor rewarded",
        },
        "families": family_reports,
        "prespecified_checks": checks,
        "balance_confirmed": all(checks.values()),
        "warning": "Balance is an engineering precondition for later construct tests, not evidence that PCC generalized to Liar's Dice.",
    }


def write_balance_protocol(path: str | Path, **kwargs) -> dict:
    report = run_balance_protocol(**kwargs)
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report

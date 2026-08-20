# PCC Liar's Dice

A synthetic, mechanistic Liar's Dice laboratory for testing whether behavioral structures studied in PCC Poker generalize to a different imperfect-information game.

This repository does **not** assume that PCC has generalized beyond poker. It is designed to make that claim difficult to earn.

## Why Liar's Dice?

Liar's Dice combines hidden private information, public escalating claims, bluffing, opponent adaptation, and exogenous randomness with a much smaller state/action space than a modern video game.

Poker remains the stronger flagship fit. Liar's Dice is valuable precisely because it is a different game: success can test cross-domain transfer, while failure can expose poker-specific assumptions.

## v0.3 scope

- frozen heads-up ruleset: 5 dice each, no wild ones, lexicographic bids
- exact information-set bid truth probabilities
- transparent Bayesian non-PCC baseline
- two independently structured synthetic Pressure/Control/Chaos policy families
- persistent public opponent profiles across rounds
- alternating opener and seat-order-balanced evaluation
- frozen pairwise competitiveness protocol
- frozen Control-over-Chaos mechanism decomposition on fresh seeds
- provisional observables only
- no human data
- no construct-recovery claim yet

## Quick start

```bash
python -m pip install -e ".[dev]"
python -m pytest -q
pcc-liars-dice simulate --policy0 family-a:pressure --policy1 family-a:control --rounds 200 --seed 42
pcc-liars-dice balance --output validation/balance.json
pcc-liars-dice control-chaos-mechanism --output validation/control-chaos-mechanism.json
```

## Scientific rule

Balance does **not** mean forcing the poker cycle to reappear. The v0.2 gate asks only whether all policy pairs are meaningfully competitive in both independent families. Construct-validity and falsification criteria must be preregistered before held-out recovery experiments.

See `docs/RULESET.md`, `docs/BASELINE_STRATEGY.md`, `docs/POLICY_FAMILIES.md`, `docs/BALANCE_PROTOCOL.md`, `docs/CONTROL_CHAOS_MECHANISM_PROTOCOL.md`, and `docs/CROSS_DOMAIN_SCOPE.md`.


## Construct recovery (v0.4)

Run the frozen synthetic recovery experiment with:

```bash
pcc-liars-dice construct-recovery --output validation/construct-recovery.json
```

See `docs/CONSTRUCT_RECOVERY_PROTOCOL.md`. This test uses fresh synthetic seeds and does not involve human data.

### Frozen v0.4 result

The first default construct-recovery run did **not** confirm all three axes. Chaos recovered across both policy families; Pressure recovered only in Family A and was confounded by Chaos in Family B; Control did not satisfy the cross-family frozen criteria. No thresholds or policies were retuned after the run. See `validation/construct-recovery.json`.

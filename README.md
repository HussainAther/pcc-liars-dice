# PCC Liar's Dice

A synthetic, mechanistic Liar's Dice laboratory for testing whether behavioral structures studied in PCC Poker generalize to a different imperfect-information game.

This repository does **not** assume that PCC has already generalized beyond poker. It is designed to make that claim difficult to earn.

## Why Liar's Dice?

Liar's Dice combines hidden private information, public escalating claims, bluffing, opponent adaptation, and exogenous randomness with a much smaller state/action space than a modern video game.

## v0.1 scope

- heads-up Liar's Dice engine
- deterministic seeded simulation
- three independently coded policy mechanisms: `pressure`, `control`, `chaos`
- intentionally provisional observables
- tests for legality, determinism, and termination
- no human data
- no claim that observables recover latent PCC dimensions yet

## Quick start

```bash
python -m pip install -e ".[dev]"
python -m pytest -q
pcc-liars-dice simulate --policy0 pressure --policy1 control --rounds 200 --seed 42
```

## Scientific rule

The next phase must preregister construct-validity and falsification criteria **before** running cross-family recovery experiments. Metrics that fail stay failed.

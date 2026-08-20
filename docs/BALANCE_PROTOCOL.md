# Frozen Balance Protocol (v0.2)

Balance is an engineering precondition, not a PCC finding.

## Design

For each policy family, evaluate all three unordered pairs:

- Pressure vs Control
- Pressure vs Chaos
- Control vs Chaos

Each replicate runs both policy seat orders. Inside each match the opening player alternates by round. The default protocol uses 8 replicates and 400 rounds per seat order.

## Prespecified competitiveness criterion

For each pair, the seat-order-combined win rate for the first axis must lie in:

`[0.30, 0.70]`.

Both families must satisfy all three pairwise bounds.

## What is *not* required

A Pressure > Control > Chaos > Pressure cycle is **not** required, rewarded, or tuned for. Liar's Dice may express the mechanisms differently from poker. Forcing a cycle would make the cross-domain comparison circular.

If the frozen default agents fail this balance gate, the result is retained as an engineering failure. Any later agent revision must be versioned and evaluated again before construct recovery begins.

## Frozen v0.2 result

The first default run failed the gate in both families, specifically on Control vs Chaos:

- Family A: Control win rate `0.7345`.
- Family B: Control win rate `0.7006`.

The remaining four pairwise comparisons were inside the prespecified `[0.30, 0.70]` interval. No policy parameters were changed after observing this result. See `validation/balance.json`.

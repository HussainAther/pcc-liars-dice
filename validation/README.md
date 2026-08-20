# Validation artifacts

These files contain frozen synthetic validation results only. They contain no human data.

- `balance.json` — v0.2 pairwise competitiveness gate. Failed because Control > Chaos exceeded the upper bound in both families.
- `control-chaos-mechanism.json` — v0.3 decomposition of that imbalance. Challenge timing and Chaos bid-plausibility cost replicated cross-family; public-history dependence was family-specific.
- `construct-recovery.json` — v0.4 orthogonal factorial construct recovery on fresh seeds. Full recovery failed; Chaos recovered cross-family, Pressure was partial, and Control did not recover cross-family.

Failed and partial results are retained rather than retuned.

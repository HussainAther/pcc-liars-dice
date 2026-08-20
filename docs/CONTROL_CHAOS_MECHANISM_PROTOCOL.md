# Control-over-Chaos mechanism decomposition (frozen v0.3 protocol)

## Question

The frozen v0.2 balance run found the same imbalance in both independent policy families: Control defeated Chaos more strongly than the prespecified competitiveness interval allowed. This protocol asks **why**, without changing either policy family.

This is an explanatory synthetic diagnostic, not a new balance-tuning pass and not a human construct claim.

## Frozen pathways

Three candidate pathways are evaluated on fresh seeds:

1. **Public-history dependence.** Re-run the Control-vs-Chaos matchup while replacing only Control's accumulated public opponent profile with an empty profile. Policy code and thresholds remain unchanged. A mean Control win-rate reduction of at least **0.03** supports a history pathway.
2. **Challenge timing.** Compare the correctness rate of Control and Chaos challenges against the realized hidden dice. A Control-minus-Chaos accuracy margin of at least **0.05** supports a challenge-timing pathway.
3. **Value/plausibility cost of stochastic bidding.** Compare the information-set truth probability of bids selected by each mechanism. A Control-minus-Chaos mean bid-truth-probability gap of at least **0.05** supports the hypothesis that Chaos pays a plausibility cost for its randomized bidding.

These thresholds are fixed before the fresh run and are not altered after inspecting outcomes.

## Design

- both independent policy families;
- 10 replicates;
- 500 rounds per seat/order per replicate;
- alternating opener and reversed seat order;
- fresh base seed `33001`, distinct from the v0.2 balance seed;
- no changes to `policies.py`.

## Interpretation

A pathway is called **cross-family supported** only if its frozen threshold is met in both families. Family-specific effects are reported as such and are not promoted to universal PCC mechanisms.

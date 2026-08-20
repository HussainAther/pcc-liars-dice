# Frozen construct-recovery protocol (v0.4)

## Question

Can public, label-free behavioral measurements recover independently manipulated Pressure, Control, and Chaos weight in **both** Liar's Dice policy families?

This is the first construct-recovery test in this repository. It is synthetic and cross-domain. It does not assume the poker measurement panel transfers automatically.

## Orthogonal factorial manipulation

Each evaluated synthetic player mixes four action mechanisms:

- the family's Pressure policy;
- the family's Control policy;
- the family's Chaos policy;
- the non-PCC Bayesian baseline.

Pressure, Control, and Chaos weights are independently assigned either `0.10` or `0.30`, producing all eight cells of a `2 x 2 x 2` factorial design. The Bayesian baseline receives the remaining probability mass.

This matters because the three target weights are manipulated orthogonally instead of being forced to sum to one. Raising one PCC axis therefore does not mechanically require lowering another PCC axis.

The component is randomly selected at each focal decision. Hidden component choices and hidden assigned weights are **not used to calculate behavioral scores**.

## Candidate observables frozen before the fresh run

### Pressure

Public bid commitment and upward quantity escalation, normalized by the total dice in play.

### Control

Conditional mutual information between the focal player's action class and a coarse public opponent-history profile, conditioning on the current public bid's information-set truth-probability bin. This measures history-sensitive action adjustment without using the opponent's hidden policy label.

### Chaos

Public-state-conditioned action entropy multiplied by an independent match-performance adequacy floor. Raw unpredictability therefore does not count as effective Chaos when the synthetic player collapses in performance.

The adequacy floor is zero at win rate `<= 0.35`, rises linearly, and is fully active at win rate `>= 0.50` against the neutral Bayesian baseline.

## Fresh evaluation design

Default frozen run:

- both independent policy families;
- 8 factorial cells;
- 8 replicates per cell;
- 250 rounds per seat order;
- reversed player seat order;
- alternating opener;
- fresh base seed `44001`;
- existing family policies unchanged;
- 100 shuffled-label repetitions per axis/family.

## Prespecified recovery criterion

For each observable in each family:

1. its standardized high-minus-low effect for the matching assigned axis must be at least `0.50`;
2. the matching effect must exceed the largest absolute nonmatching-axis effect by at least `0.20`;
3. the matching effect must exceed the 95th percentile of its shuffled-label null.

An axis is cross-family recovered only if all three checks pass in **both** families. Full Liar's Dice construct recovery is confirmed only if Pressure, Control, and Chaos all recover cross-family.

No threshold is changed after seeing the fresh result. Partial or failed axes are retained.

## Frozen v0.4 result

The first default fresh-seed run did **not** confirm full three-axis construct recovery.

- **Chaos:** cross-family recovered. Family A matching standardized effect `0.690` with discriminant margin `0.480`; Family B matching effect `1.340` with margin `0.241`. Both exceeded their shuffled-label 95th-percentile controls.
- **Pressure:** partial. Family A passed all frozen checks (`1.672` matching effect; `0.647` margin), but Family B failed discriminant validity because the Pressure observable responded even more strongly to assigned Chaos (`0.597` matching effect versus largest absolute cross-effect `1.348`).
- **Control:** not cross-family recovered. Family A showed a negative matching effect (`-0.215`) and failed all three checks. Family B was directionally/discriminantly promising (`0.450` matching effect; `0.313` margin; above shuffled control) but missed the prespecified `0.50` matching-effect threshold.

Accordingly:

`liars_dice_construct_recovery_confirmed = false`

and the cross-family axis status is:

- Pressure: `false`
- Control: `false`
- Chaos: `true`

No observable, policy, threshold, or seed was changed after inspecting this result.

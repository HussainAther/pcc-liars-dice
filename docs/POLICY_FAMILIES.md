# Independent Synthetic Policy Families

v0.2 contains two independently structured policy families. Their purpose is to make later construct validation harder than testing a metric against one implementation style.

## Family A: probability-score mechanisms

Family A uses explicit information-set truth probabilities throughout:

- **Pressure:** chooses the highest commitment that remains above a fixed plausibility floor.
- **Control:** changes challenge/bidding thresholds using accumulated public opponent behavior.
- **Chaos:** samples stochastically among value-bounded actions and uses probabilistic challenges.

## Family B: threshold/heuristic mechanisms

Family B deliberately avoids Family A's target-probability optimization rule:

- **Pressure:** walks the legal bid ladder until a conservative bluff boundary is crossed.
- **Control:** uses discrete rules based on public opponent escalation and challenge rate.
- **Chaos:** switches stochastically between conservative and bounded-bluff modes.

The two families share only the game rules and the basic information-set probability primitive. They do not share PCC-specific scoring equations.

## Scientific status

Names are latent synthetic assignments, not validated observational labels. Later recovery experiments must be preregistered and must succeed across both families before any cross-domain construct claim is promoted.

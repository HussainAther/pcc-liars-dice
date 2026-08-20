# Frozen Liar's Dice Laboratory Ruleset (v0.2)

This repository uses a deliberately narrow heads-up ruleset so that later PCC comparisons are not confounded by variant-specific rule choices.

## Round rules

- Two players.
- Five six-sided dice per player at the start of every laboratory round.
- Dice are private to their owner.
- Ones are **not wild**.
- A bid is `(quantity, face)` and means that at least `quantity` dice showing `face` exist across both players' hands.
- Bids increase lexicographically: quantity first, then face. Thus `(2,1)` is above `(1,6)`, and `(2,4)` is above `(2,3)`.
- The first action must be a bid.
- On later actions a player either makes a strictly higher bid or challenges.
- A challenge ends the round. If the final bid is true, the bidder wins; otherwise the challenger wins.

## Laboratory simplifications

This is **not** an elimination/tournament implementation. Dice counts reset to five per player every round. Match-level simulations alternate the opening player and preserve only public behavioral history for opponent adaptation.

Those choices are intentional. The first validation question is about strategic behavior under imperfect information, not survival dynamics caused by shrinking dice pools.

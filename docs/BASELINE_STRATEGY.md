# Bayesian Baseline Strategy

The v0.2 non-PCC baseline is defined before construct-recovery experiments.

For a candidate bid, the acting player knows its own dice and treats every unknown opponent die as independently matching the bid face with probability `1/6`. The exact binomial tail therefore gives the information-set probability that the bid is true.

The baseline:

1. challenges when the current bid has truth probability below `0.30`;
2. otherwise selects a legal bid closest to truth probability `0.55`, with lower commitment breaking ties.

This is not claimed to be Nash-optimal Liar's Dice. Its purpose is to provide a transparent, non-PCC reference policy built from ordinary probabilistic reasoning.

The baseline must not be tuned using later PCC construct-recovery results.

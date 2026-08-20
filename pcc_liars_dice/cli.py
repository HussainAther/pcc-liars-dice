from __future__ import annotations

import argparse
import json

from .balance import write_balance_protocol
from .control_chaos_mechanism import write_control_chaos_mechanism
from .construct_recovery import write_construct_recovery
from .policies import POLICIES
from .simulate import simulate_match


def main(argv=None):
    p = argparse.ArgumentParser(prog="pcc-liars-dice")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("simulate")
    s.add_argument("--policy0", choices=sorted(POLICIES), default="family-a:pressure")
    s.add_argument("--policy1", choices=sorted(POLICIES), default="family-a:control")
    s.add_argument("--rounds", type=int, default=100)
    s.add_argument("--seed", type=int, default=1)

    b = sub.add_parser("balance")
    b.add_argument("--replicates", type=int, default=8)
    b.add_argument("--rounds-per-order", type=int, default=400)
    b.add_argument("--seed", type=int, default=22001)
    b.add_argument("--output", default="validation/balance.json")

    m = sub.add_parser("control-chaos-mechanism")
    m.add_argument("--replicates", type=int, default=10)
    m.add_argument("--rounds-per-order", type=int, default=500)
    m.add_argument("--seed", type=int, default=33001)
    m.add_argument("--output", default="validation/control-chaos-mechanism.json")

    c = sub.add_parser("construct-recovery")
    c.add_argument("--replicates", type=int, default=8)
    c.add_argument("--rounds-per-order", type=int, default=250)
    c.add_argument("--seed", type=int, default=44001)
    c.add_argument("--shuffle-repetitions", type=int, default=100)
    c.add_argument("--output", default="validation/construct-recovery.json")

    args = p.parse_args(argv)
    if args.cmd == "simulate":
        report = simulate_match(args.policy0, args.policy1, args.rounds, args.seed)
    elif args.cmd == "balance":
        report = write_balance_protocol(
            args.output,
            replicates=args.replicates,
            rounds_per_order=args.rounds_per_order,
            seed=args.seed,
        )
    elif args.cmd == "control-chaos-mechanism":
        report = write_control_chaos_mechanism(
            args.output, replicates=args.replicates, rounds_per_order=args.rounds_per_order, seed=args.seed
        )
    else:
        report = write_construct_recovery(
            args.output,
            replicates=args.replicates,
            rounds_per_order=args.rounds_per_order,
            seed=args.seed,
            shuffle_repetitions=args.shuffle_repetitions,
        )
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

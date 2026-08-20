from __future__ import annotations
import argparse, json
from .policies import POLICIES
from .simulate import simulate_match

def main(argv=None):
    p=argparse.ArgumentParser(prog='pcc-liars-dice')
    sub=p.add_subparsers(dest='cmd', required=True)
    s=sub.add_parser('simulate')
    s.add_argument('--policy0', choices=sorted(POLICIES), default='pressure')
    s.add_argument('--policy1', choices=sorted(POLICIES), default='control')
    s.add_argument('--rounds', type=int, default=100)
    s.add_argument('--seed', type=int, default=1)
    args=p.parse_args(argv)
    print(json.dumps(simulate_match(args.policy0,args.policy1,args.rounds,args.seed), indent=2))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())

"""Commands for reproducible development experiments."""

import argparse
import json


def main():
    parser = argparse.ArgumentParser(prog="alpha-research")
    commands = parser.add_subparsers(dest="command", required=True)
    demo = commands.add_parser("benchmark", help="Run predeclared synthetic development controls")
    demo.add_argument("--output", default="artifacts/development/synthetic-v1.json")
    demo.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2, 3, 4])
    demo.add_argument("--budget", type=int, default=12)
    args = parser.parse_args()
    if args.command == "benchmark":
        from .experiments import run_synthetic_benchmark
        report = run_synthetic_benchmark(args.output, args.seeds, args.budget)
        print(json.dumps({"output": args.output, "summary": report["summary"]}, indent=2))


if __name__ == "__main__":
    main()

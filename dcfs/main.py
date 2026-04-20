import argparse
import asyncio

from dcfs.engine.simulator import FactorySimulator


def parse_args():
    parser = argparse.ArgumentParser(description="Digital Corrugated Factory Simulator")
    parser.add_argument(
        "--mode",
        choices=["real_time", "fast", "chaos"],
        default="real_time",
        help="Simulation mode",
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=None,
        help="Maximum amount of simulation steps to run",
    )
    parser.add_argument(
        "--time-step",
        type=float,
        default=None,
        help="Override step duration in seconds",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    simulator = FactorySimulator(mode=args.mode, time_step=args.time_step)
    asyncio.run(simulator.run(max_steps=args.max_steps))


if __name__ == "__main__":
    main()

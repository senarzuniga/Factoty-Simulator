import argparse
import asyncio

from dcfs.engine.simulator import FactorySimulator
from dcfs.integration.company_profile import load_company_profile
from dcfs.integration.dep_bridge import DEPBridgeClient


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
    parser.add_argument(
        "--dep-backend-url",
        type=str,
        default=None,
        help="DEP backend URL (for example http://localhost:8000)",
    )
    parser.add_argument(
        "--dep-token",
        type=str,
        default=None,
        help="DEP API bearer token",
    )
    parser.add_argument(
        "--company-profile",
        type=str,
        default=None,
        help="Path to company profile JSON compatible with DEP config/companies.json",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    step_callbacks = []

    if args.dep_backend_url:
        profile = load_company_profile(args.company_profile)
        bridge = DEPBridgeClient(
            base_url=args.dep_backend_url,
            token=args.dep_token,
            company_profile=profile,
        )
        step_callbacks.append(bridge.sync_step)

    simulator = FactorySimulator(
        mode=args.mode,
        time_step=args.time_step,
        step_callbacks=step_callbacks,
    )
    asyncio.run(simulator.run(max_steps=args.max_steps))


if __name__ == "__main__":
    main()

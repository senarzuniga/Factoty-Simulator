import asyncio

from dcfs.engine.simulator import FactorySimulator


if __name__ == "__main__":
    simulator = FactorySimulator(mode="real_time")
    asyncio.run(simulator.run())


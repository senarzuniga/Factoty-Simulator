import unittest

from dcfs.engine.simulator import FactorySimulator


class SimulatorTests(unittest.IsolatedAsyncioTestCase):
    async def test_step_publishes_production_and_kpi(self):
        simulator = FactorySimulator(mode="fast", time_step=0)
        received = []
        simulator.bus.subscribe(received.append)

        await simulator.step()
        event_types = {event["type"] for event in received}

        self.assertIn("production.update", event_types)
        self.assertIn("kpi.update", event_types)


if __name__ == "__main__":
    unittest.main()


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

    async def test_step_callbacks_receive_state_events_and_kpi(self):
        callback_calls = []

        def callback(state, events, kpi):
            callback_calls.append((state, events, kpi))

        simulator = FactorySimulator(mode="fast", time_step=0, step_callbacks=[callback])

        await simulator.step()

        self.assertEqual(len(callback_calls), 1)
        self.assertTrue(callback_calls[0][1])
        self.assertIn("oee", callback_calls[0][2])


if __name__ == "__main__":
    unittest.main()

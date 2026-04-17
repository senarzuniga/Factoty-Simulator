import unittest
from unittest import mock

from dcfs.engine.factory_state import FactoryState
from dcfs.logic.failures import FailureEngine


class FailureEngineTests(unittest.TestCase):
    @mock.patch("dcfs.logic.failures.random.random", side_effect=[0.0, 0.0])
    def test_maybe_fail_emits_machine_and_energy_events(self, _mock_random):
        state = FactoryState()
        engine = FailureEngine(mode="real_time")

        events = engine.maybe_fail(state)
        event_types = {event["type"] for event in events}

        self.assertIn("machine.anomaly", event_types)
        self.assertIn("energy.spike", event_types)

    @mock.patch("dcfs.logic.failures.random.random", side_effect=[1.0, 1.0])
    def test_maybe_fail_emits_congestion_when_wip_high(self, _mock_random):
        state = FactoryState()
        state.wip = 30001
        engine = FailureEngine()

        events = engine.maybe_fail(state)

        self.assertEqual(events[0]["type"], "wip.congestion")


if __name__ == "__main__":
    unittest.main()


import unittest
from unittest import mock

from dcfs.engine.factory_state import FactoryState
from dcfs.logic.failures import FailureEngine


class FailureEngineTests(unittest.TestCase):
    def test_maybe_fail_with_chaos_mode_emits_anomalies(self):
        """With chaos mode anomaly_rate=0.20 and 6 machines, at least one anomaly is very likely."""
        state = FactoryState()
        engine = FailureEngine(mode="chaos")

        # Run several steps to ensure anomalies are generated
        all_events = []
        for _ in range(20):
            all_events.extend(engine.maybe_fail(state))

        event_types = {e["type"] for e in all_events}
        self.assertIn("machine.anomaly", event_types)

    def test_maybe_fail_emits_congestion_when_wip_high(self):
        state = FactoryState()
        state.wip = 30001
        engine = FailureEngine()

        events = engine.maybe_fail(state)
        event_types = {e["type"] for e in events}

        self.assertIn("wip.congestion", event_types)

    def test_anomaly_includes_machine_id_from_state(self):
        """Anomaly events reference machines that exist in the factory state."""
        state = FactoryState()
        engine = FailureEngine(mode="chaos")
        valid_machines = set(state.machines.keys())

        all_events = []
        for _ in range(30):
            all_events.extend(engine.maybe_fail(state))

        anomalies = [e for e in all_events if e["type"] == "machine.anomaly"]
        for anomaly in anomalies:
            self.assertIn(anomaly["machine"], valid_machines)

    def test_low_inventory_triggers_alert(self):
        state = FactoryState()
        state.inventory["glue_l"] = 100.0  # below 500 threshold
        engine = FailureEngine()

        events = engine.maybe_fail(state)
        event_types = {e["type"] for e in events}

        self.assertIn("inventory.low", event_types)


if __name__ == "__main__":
    unittest.main()


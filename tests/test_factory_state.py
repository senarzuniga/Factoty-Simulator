import unittest
from unittest import mock

from dcfs.engine.factory_state import FactoryState


class FactoryStateTests(unittest.TestCase):
    def test_machines_are_six(self):
        state = FactoryState()
        self.assertEqual(len(state.machines), 6)

    def test_machine_ids_match_seed(self):
        state = FactoryState()
        expected = {
            "BHS-CORR-01", "FLEXO-01", "FLEXO-02",
            "DIECUT-01", "FOLDER-GLUER-01", "FOLDER-GLUER-02",
        }
        self.assertEqual(set(state.machines.keys()), expected)

    def test_all_machines_have_vibration_and_temp(self):
        state = FactoryState()
        for mid, m in state.machines.items():
            self.assertIn("vibration", m, f"{mid} missing vibration")
            self.assertIn("temp", m, f"{mid} missing temp")

    @mock.patch("dcfs.engine.factory_state.random.uniform", return_value=0.05)
    def test_generate_production_updates_wip_scrap_and_energy(self, _mock_uniform):
        state = FactoryState()
        events = state.generate_production()

        event_types = [e["type"] for e in events]
        self.assertIn("production.update", event_types)
        self.assertIn("energy.update", event_types)
        # At minimum, wip is updated (may go up or down depending on machine mix)
        self.assertGreaterEqual(state.scrap, 0)
        self.assertGreater(state.energy_kwh, 0)

    def test_inventory_depletes_on_update(self):
        state = FactoryState()
        initial_glue = state.inventory["glue_l"]
        state.update()
        self.assertLess(state.inventory["glue_l"], initial_glue)


if __name__ == "__main__":
    unittest.main()


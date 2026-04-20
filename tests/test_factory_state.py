import unittest
from unittest import mock

from dcfs.engine.factory_state import FactoryState


class FactoryStateTests(unittest.TestCase):
    @mock.patch("dcfs.engine.factory_state.random.uniform", return_value=0.05)
    def test_generate_production_updates_wip_scrap_and_energy(self, _mock_uniform):
        state = FactoryState()
        events = state.generate_production()

        self.assertEqual(events[0]["type"], "production.update")
        self.assertEqual(events[1]["type"], "energy.update")
        self.assertGreater(state.wip, 20000)
        self.assertGreater(state.scrap, 0)
        self.assertGreater(state.energy_kwh, 0)


if __name__ == "__main__":
    unittest.main()


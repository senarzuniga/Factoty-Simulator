import unittest

from dcfs.engine.factory_state import FactoryState
from dcfs.integration.dep_bridge import build_asset_payloads, build_telemetry_payloads


class DEPBridgePayloadTests(unittest.TestCase):
    def test_build_asset_payloads_for_company(self):
        state = FactoryState()

        payloads = build_asset_payloads(state, company_id="factory_simulator_corrugados")

        self.assertEqual(len(payloads), len(state.machines))
        self.assertEqual(payloads[0]["company_id"], "factory_simulator_corrugados")
        self.assertEqual(payloads[0]["connector_type"], "rest")

    def test_build_telemetry_payloads_only_for_registered_assets(self):
        state = FactoryState()
        machine_to_asset_id = {
            "CORR-01": "asset-1",
            "FLEXO-01": "asset-2",
        }

        payloads = build_telemetry_payloads(state, machine_to_asset_id, fallback_oee=0.82)

        self.assertEqual(len(payloads), 2)
        self.assertEqual(payloads[0]["oee"], 0.82)
        self.assertIn("power_kw", payloads[0])


if __name__ == "__main__":
    unittest.main()

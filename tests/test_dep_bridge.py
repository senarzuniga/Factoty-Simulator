import unittest
from unittest.mock import patch, MagicMock

from dcfs.engine.factory_state import FactoryState
from dcfs.integration.dep_bridge import DEPBridgeClient, build_asset_payloads, build_telemetry_payloads


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
            "BHS-CORR-01": "asset-1",
            "FLEXO-01": "asset-2",
        }

        payloads = build_telemetry_payloads(state, machine_to_asset_id, fallback_oee=0.82)

        self.assertEqual(len(payloads), 2)
        self.assertEqual(payloads[0]["oee"], 0.82)
        self.assertIn("power_kw", payloads[0])

    def test_build_telemetry_payloads_infers_oee_without_fallback(self):
        state = FactoryState()
        machine_to_asset_id = {"BHS-CORR-01": "asset-1"}

        payloads = build_telemetry_payloads(state, machine_to_asset_id)

        self.assertEqual(len(payloads), 1)
        self.assertGreater(payloads[0]["oee"], 0.0)
        self.assertLessEqual(payloads[0]["oee"], 1.0)

    @patch('dcfs.integration.dep_bridge.request.urlopen')
    def test_dep_bridge_client_request(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = b'{}'
        mock_urlopen.return_value = mock_response

        client = DEPBridgeClient(base_url='http://example.com', company_profile={'id': '123'})
        response = client._request('GET', '/data/assets')

        self.assertIsNotNone(response)
        mock_urlopen.assert_called_once()


if __name__ == "__main__":
    unittest.main()

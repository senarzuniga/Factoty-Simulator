import json
from typing import Dict, List, Mapping, Optional
from urllib import error, parse, request


def infer_asset_type(machine_id: str) -> str:
    if machine_id.startswith("CORR") or "CORR" in machine_id:
        return "Corrugator"
    if machine_id.startswith("FLEXO"):
        return "Flexo Printer"
    if machine_id.startswith("DIECUT"):
        return "Die Cutter"
    if "GLUER" in machine_id:
        return "Folder Gluer"
    return "Industrial Machine"


def build_asset_payloads(state, company_id: str) -> List[dict]:
    payloads = []
    for machine_id in state.machines:
        payloads.append(
            {
                "company_id": company_id,
                "name": machine_id,
                "asset_type": infer_asset_type(machine_id),
                "manufacturer": "Factory Simulator",
                "model_number": machine_id,
                "location": "Factory Simulator Plant",
                "connector_type": "rest",
            }
        )
    return payloads


def build_telemetry_payloads(
    state,
    machine_to_asset_id: Mapping[str, str],
    fallback_oee: Optional[float] = None,
) -> List[dict]:
    payloads = []
    for machine_id, machine in state.machines.items():
        asset_id = machine_to_asset_id.get(machine_id)
        if not asset_id:
            continue

        speed = float(machine.get("speed", 0.0))
        health = float(machine.get("health", 0.0))
        inferred_oee = min(1.0, max(0.0, (speed / 300.0) * health))

        payloads.append(
            {
                "asset_id": asset_id,
                "temperature": float(machine.get("temp", 0.0)),
                "vibration": float(machine.get("vibration", 0.0)),
                "power_kw": round(speed * 0.08, 3),
                "oee": round(fallback_oee if fallback_oee is not None else inferred_oee, 3),
            }
        )

    return payloads


class DEPBridgeClient:
    def __init__(self, base_url: str, company_profile: Mapping[str, object], token: Optional[str] = None, timeout: int = 5):
        self.base_url = base_url.rstrip("/")
        self.api_base = f"{self.base_url}/api/v1"
        self.company_id = str(company_profile["id"])
        self.token = token
        self.timeout = timeout
        self.machine_to_asset_id: Dict[str, str] = {}

    def _request(self, method: str, path: str, payload: Optional[dict] = None, params: Optional[dict] = None):
        url = f"{self.api_base}{path}"
        if params:
            url = f"{url}?{parse.urlencode(params)}"

        headers = {"Accept": "application/json"}
        data = None
        if payload is not None:
            headers["Content-Type"] = "application/json"
            data = json.dumps(payload).encode("utf-8")
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        req = request.Request(url=url, data=data, method=method, headers=headers)
        try:
            with request.urlopen(req, timeout=self.timeout) as response:
                raw = response.read().decode("utf-8")
                return json.loads(raw) if raw else None
        except error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"DEP request failed ({method} {path}): {exc.code} {body}") from exc
        except error.URLError as exc:
            raise RuntimeError(f"DEP backend unreachable at {self.api_base}: {exc.reason}") from exc

    def ensure_assets(self, state) -> Dict[str, str]:
        assets = self._request("GET", "/data/assets", params={"company_id": self.company_id}) or []
        self.machine_to_asset_id = {
            asset["name"]: asset["id"]
            for asset in assets
            if asset.get("name") and asset.get("id")
        }

        for payload in build_asset_payloads(state, self.company_id):
            if payload["name"] not in self.machine_to_asset_id:
                created = self._request("POST", "/data/assets", payload=payload)
                self.machine_to_asset_id[payload["name"]] = created["id"]

        return self.machine_to_asset_id

    def sync_step(self, state, _events: List[dict], kpi: Mapping[str, object]) -> None:
        machine_to_asset_id = self.ensure_assets(state)
        telemetry_payloads = build_telemetry_payloads(
            state,
            machine_to_asset_id,
            fallback_oee=float(kpi.get("oee", 0.0)),
        )
        for payload in telemetry_payloads:
            self._request("POST", "/data/telemetry", payload=payload)

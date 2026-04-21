import random
from datetime import datetime, timezone
from typing import Dict, List


class FactoryState:
    """In-memory digital twin state."""

    FAILURE_TO_MAINTENANCE_PROB = 0.20
    MAINTENANCE_TO_IDLE_PROB = 0.35
    IDLE_TO_RUNNING_PROB = 0.60
    RUNNING_TO_FAILURE_PROB = 0.02
    RUNNING_TO_IDLE_PROB = 0.05

    def __init__(self):
        self.machines: Dict[str, Dict[str, float]] = {
            "CORR-01": {
                "health": 0.85,
                "vibration": 2.0,
                "temp": 75.0,
                "speed": 280.0,
                "status": "RUNNING",
                "efficiency": 0.92,
                "wear": 0.15,
            },
            "FLEXO-01": {
                "health": 0.90,
                "speed": 9000.0,
                "status": "RUNNING",
                "efficiency": 0.95,
                "wear": 0.10,
            },
            "DIECUT-01": {
                "health": 0.88,
                "speed": 8000.0,
                "status": "RUNNING",
                "efficiency": 0.93,
                "wear": 0.12,
            },
        }
        self.wip = 20000
        self.scrap = 0
        self.energy_kwh = 0.0
        self.total_output = 0
        self.shift = "DAY"
        self.last_updated_at = self._iso_now()

    @staticmethod
    def _iso_now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _resolve_shift(now: datetime) -> str:
        hour = now.hour
        if 6 <= hour < 14:
            return "DAY"
        if 14 <= hour < 22:
            return "EVENING"
        return "NIGHT"

    def update(self) -> None:
        now = datetime.now(timezone.utc)
        self.shift = self._resolve_shift(now)
        self.last_updated_at = now.isoformat()

        for machine in self.machines.values():
            status = machine.get("status", "RUNNING")

            if status == "FAILURE" and random.random() < self.FAILURE_TO_MAINTENANCE_PROB:
                status = "MAINTENANCE"
            elif status == "MAINTENANCE" and random.random() < self.MAINTENANCE_TO_IDLE_PROB:
                status = "IDLE"
            elif status == "IDLE" and random.random() < self.IDLE_TO_RUNNING_PROB:
                status = "RUNNING"
            elif status == "RUNNING":
                if random.random() < self.RUNNING_TO_FAILURE_PROB:
                    status = "FAILURE"
                elif random.random() < self.RUNNING_TO_IDLE_PROB:
                    status = "IDLE"

            machine["status"] = status
            machine["health"] = max(0.0, machine["health"] - random.uniform(0.0001, 0.001))
            machine["wear"] = min(1.0, machine.get("wear", 0.0) + random.uniform(0.0005, 0.003))
            machine["efficiency"] = min(
                1.0,
                max(
                    0.40,
                    machine.get("efficiency", 0.9) + random.uniform(-0.02, 0.02),
                ),
            )

            if machine["status"] == "RUNNING":
                machine["speed"] = max(0.0, machine.get("speed", 0.0) * random.uniform(0.96, 1.04))
            elif machine["status"] in {"IDLE", "MAINTENANCE"}:
                machine["speed"] = max(0.0, machine.get("speed", 0.0) * random.uniform(0.25, 0.60))
            else:
                machine["speed"] = max(0.0, machine.get("speed", 0.0) * random.uniform(0.01, 0.10))

            if "vibration" in machine:
                machine["vibration"] = min(
                    15.0,
                    max(0.2, machine["vibration"] + random.uniform(-0.3, 0.3)),
                )
            if "temp" in machine:
                nominal_temp = 75.0
                delta = random.uniform(-0.8, 0.8) + (nominal_temp - machine["temp"]) * 0.05
                if machine["status"] == "RUNNING":
                    delta += 0.2
                if machine["status"] == "FAILURE":
                    delta += 0.8
                machine["temp"] = min(140.0, max(30.0, machine["temp"] + delta))

    def generate_production(self) -> List[dict]:
        corr = self.machines["CORR-01"]
        if corr.get("status") == "RUNNING":
            production = int(corr["speed"] * corr["health"] * corr.get("efficiency", 0.95) * 0.95)
        else:
            production = int(corr["speed"] * 0.01)
        scrap = int(production * random.uniform(0.02, 0.08))
        self.wip += production - scrap
        self.scrap += scrap
        self.energy_kwh += production * 0.015
        self.total_output += production

        return [
            {
                "type": "production.update",
                "machine": "CORR-01",
                "data": {
                    "produced_m2": production,
                    "scrap": scrap,
                    "wip": self.wip,
                    "shift": self.shift,
                    "machine_status": corr.get("status", "RUNNING"),
                },
            },
            {
                "type": "energy.update",
                "system": "plant",
                "data": {"energy_kwh": round(self.energy_kwh, 3)},
            },
        ]

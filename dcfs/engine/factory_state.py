import random
from typing import Dict, List


class FactoryState:
    """In-memory digital twin state."""

    def __init__(self):
        self.machines: Dict[str, Dict[str, float]] = {
            "CORR-01": {
                "health": 0.85,
                "vibration": 2.0,
                "temp": 75.0,
                "speed": 280.0,
            },
            "FLEXO-01": {"health": 0.90, "speed": 9000.0},
            "DIECUT-01": {"health": 0.88, "speed": 8000.0},
        }
        self.wip = 20000
        self.scrap = 0
        self.energy_kwh = 0.0

    def update(self) -> None:
        for machine in self.machines.values():
            machine["health"] = max(0.0, machine["health"] - random.uniform(0.0001, 0.001))
            if "vibration" in machine:
                machine["vibration"] += random.uniform(-0.2, 0.3)
            if "temp" in machine:
                machine["temp"] += random.uniform(-0.5, 0.8)

    def generate_production(self) -> List[dict]:
        corr = self.machines["CORR-01"]
        production = int(corr["speed"] * corr["health"] * 0.95)
        scrap = int(production * random.uniform(0.02, 0.08))
        self.wip += production - scrap
        self.scrap += scrap
        self.energy_kwh += production * 0.015

        return [
            {
                "type": "production.update",
                "machine": "CORR-01",
                "data": {
                    "produced_m2": production,
                    "scrap": scrap,
                    "wip": self.wip,
                },
            },
            {
                "type": "energy.update",
                "system": "plant",
                "data": {"energy_kwh": round(self.energy_kwh, 3)},
            },
        ]


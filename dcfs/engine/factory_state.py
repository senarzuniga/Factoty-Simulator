import random
from datetime import datetime, timezone
from typing import Dict, List

# Reference speeds for OEE performance factor per machine type
SPEED_REFERENCE = {
    "corrugator": 300.0,      # m/min
    "flexo": 10000.0,          # sheets/h
    "diecut": 9000.0,          # strokes/h
    "folder_gluer": 130000.0,  # pieces/h
}

# Energy cost per unit of output per machine type (kWh)
ENERGY_COST = {
    "corrugator": 0.015,
    "flexo": 0.0003,
    "diecut": 0.0004,
    "folder_gluer": 0.0002,
}

# Nominal temperatures per machine type (°C)
NOMINAL_TEMP = {
    "corrugator": 75.0,
    "flexo": 55.0,
    "diecut": 45.0,
    "folder_gluer": 40.0,
}


class FactoryState:
    """In-memory digital twin state for a 6-machine corrugated cardboard plant."""

    FAILURE_TO_MAINTENANCE_PROB = 0.20
    MAINTENANCE_TO_IDLE_PROB = 0.35
    IDLE_TO_RUNNING_PROB = 0.60
    RUNNING_TO_FAILURE_PROB = 0.02
    RUNNING_TO_IDLE_PROB = 0.05
    MIN_VIBRATION = 0.2
    MAX_VIBRATION = 15.0
    TEMP_REGULATION_FACTOR = 0.05
    RUNNING_TEMP_INCREASE = 0.2
    FAILURE_TEMP_INCREASE = 0.8
    MIN_TEMP = 25.0
    MAX_TEMP = 140.0

    def __init__(self):
        self.machines: Dict[str, Dict] = {
            "BHS-CORR-01": {
                "type": "corrugator",
                "health": 0.85,
                "vibration": 2.0,
                "temp": 75.0,
                "speed": 280.0,
                "speed_min": 100.0,
                "speed_max": 350.0,
                "status": "RUNNING",
                "efficiency": 0.92,
                "wear": 0.15,
            },
            "FLEXO-01": {
                "type": "flexo",
                "health": 0.90,
                "vibration": 1.5,
                "temp": 55.0,
                "speed": 9000.0,
                "speed_min": 6000.0,
                "speed_max": 12000.0,
                "status": "RUNNING",
                "efficiency": 0.95,
                "wear": 0.10,
            },
            "FLEXO-02": {
                "type": "flexo",
                "health": 0.88,
                "vibration": 1.8,
                "temp": 57.0,
                "speed": 8500.0,
                "speed_min": 6000.0,
                "speed_max": 12000.0,
                "status": "RUNNING",
                "efficiency": 0.93,
                "wear": 0.12,
            },
            "DIECUT-01": {
                "type": "diecut",
                "health": 0.87,
                "vibration": 2.5,
                "temp": 45.0,
                "speed": 8000.0,
                "speed_min": 6500.0,
                "speed_max": 11000.0,
                "status": "RUNNING",
                "efficiency": 0.91,
                "wear": 0.13,
            },
            "FOLDER-GLUER-01": {
                "type": "folder_gluer",
                "health": 0.89,
                "vibration": 1.2,
                "temp": 38.0,
                "speed": 110000.0,
                "speed_min": 80000.0,
                "speed_max": 150000.0,
                "status": "RUNNING",
                "efficiency": 0.94,
                "wear": 0.11,
            },
            "FOLDER-GLUER-02": {
                "type": "folder_gluer",
                "health": 0.86,
                "vibration": 1.4,
                "temp": 39.0,
                "speed": 105000.0,
                "speed_min": 80000.0,
                "speed_max": 150000.0,
                "status": "RUNNING",
                "efficiency": 0.92,
                "wear": 0.14,
            },
        }
        # Plant-level inventory (litres / kg)
        self.inventory: Dict[str, float] = {
            "glue_l": 5000.0,
            "ink_kg": 2000.0,
            "oil_l": 500.0,
        }
        self.wip = 20000          # m² of corrugated board in process
        self.scrap = 0            # m² total scrap
        self.energy_kwh = 0.0
        self.total_output = 0     # converted/finished units
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
            mtype = machine.get("type", "corrugator")
            status = machine.get("status", "RUNNING")
            nominal_t = NOMINAL_TEMP.get(mtype, 65.0)

            # --- State transitions ---
            if status == "FAILURE" and random.random() < self.FAILURE_TO_MAINTENANCE_PROB:
                status = "MAINTENANCE"
            elif status == "MAINTENANCE" and random.random() < self.MAINTENANCE_TO_IDLE_PROB:
                # Maintenance recovers health and wear partially
                machine["health"] = min(1.0, machine["health"] + random.uniform(0.005, 0.02))
                machine["wear"] = max(0.0, machine.get("wear", 0.0) - random.uniform(0.01, 0.05))
                status = "IDLE"
            elif status == "IDLE" and random.random() < self.IDLE_TO_RUNNING_PROB:
                status = "RUNNING"
            elif status == "RUNNING":
                roll = random.random()
                if roll < self.RUNNING_TO_FAILURE_PROB:
                    status = "FAILURE"
                elif roll < (self.RUNNING_TO_FAILURE_PROB + self.RUNNING_TO_IDLE_PROB):
                    status = "IDLE"

            machine["status"] = status

            # --- Degradation (skipped during maintenance recovery already handled above) ---
            if status != "MAINTENANCE":
                machine["health"] = max(0.0, machine["health"] - random.uniform(0.0001, 0.001))
                machine["wear"] = min(1.0, machine.get("wear", 0.0) + random.uniform(0.0005, 0.003))

            machine["efficiency"] = min(
                1.0,
                max(0.40, machine.get("efficiency", 0.9) + random.uniform(-0.02, 0.02)),
            )

            # --- Speed physics ---
            spd = machine.get("speed", 0.0)
            spd_min = machine.get("speed_min", 0.0)
            spd_max = machine.get("speed_max", spd * 1.2)
            if status == "RUNNING":
                spd = max(spd_min, min(spd_max, spd * random.uniform(0.97, 1.03)))
            elif status in {"IDLE", "MAINTENANCE"}:
                spd = max(0.0, spd * random.uniform(0.20, 0.50))
            else:  # FAILURE
                spd = max(0.0, spd * random.uniform(0.01, 0.08))
            machine["speed"] = spd

            # --- Vibration ---
            machine["vibration"] = min(
                self.MAX_VIBRATION,
                max(self.MIN_VIBRATION, machine["vibration"] + random.uniform(-0.3, 0.3)),
            )
            # Failures amplify vibration
            if status == "FAILURE":
                machine["vibration"] = min(self.MAX_VIBRATION, machine["vibration"] + random.uniform(0.5, 2.0))

            # --- Temperature ---
            delta = (
                random.uniform(-0.8, 0.8)
                + (nominal_t - machine["temp"]) * self.TEMP_REGULATION_FACTOR
            )
            if status == "RUNNING":
                delta += self.RUNNING_TEMP_INCREASE
            if status == "FAILURE":
                delta += self.FAILURE_TEMP_INCREASE
            machine["temp"] = min(self.MAX_TEMP, max(self.MIN_TEMP, machine["temp"] + delta))

        # --- Inventory depletion (per active machine) ---
        running_corrugators = sum(
            1 for m in self.machines.values() if m["type"] == "corrugator" and m["status"] == "RUNNING"
        )
        running_flexo = sum(
            1 for m in self.machines.values() if m["type"] == "flexo" and m["status"] == "RUNNING"
        )
        running_converting = sum(
            1 for m in self.machines.values()
            if m["type"] in {"diecut", "folder_gluer"} and m["status"] == "RUNNING"
        )
        self.inventory["glue_l"] = max(
            0.0, self.inventory["glue_l"] - (running_corrugators * 2.5 + running_converting * 0.8)
        )
        self.inventory["ink_kg"] = max(0.0, self.inventory["ink_kg"] - running_flexo * 1.2)
        self.inventory["oil_l"] = max(
            0.0, self.inventory["oil_l"] - len(self.machines) * 0.05
        )

    def generate_production(self) -> List[dict]:
        events: List[dict] = []
        step_energy = 0.0

        for machine_id, machine in self.machines.items():
            mtype = machine.get("type", "corrugator")
            status = machine.get("status", "RUNNING")
            speed = machine.get("speed", 0.0)
            health = machine.get("health", 0.0)
            efficiency = machine.get("efficiency", 0.95)

            if status == "RUNNING":
                output = int(speed * health * efficiency * random.uniform(0.92, 0.98))
            else:
                output = 0

            scrap = int(output * random.uniform(0.02, 0.08)) if output > 0 else 0
            net_output = output - scrap

            if mtype == "corrugator":
                self.wip += net_output
                self.scrap += scrap
            else:
                # Converting machines consume from WIP
                consumed = min(self.wip, int(net_output * 0.8))
                self.wip = max(0, self.wip - consumed)
                self.total_output += net_output
                self.scrap += scrap

            energy = round(output * ENERGY_COST.get(mtype, 0.01), 3)
            step_energy += energy

            events.append(
                {
                    "type": "production.update",
                    "machine": machine_id,
                    "data": {
                        "machine_type": mtype,
                        "output": output,
                        "scrap": scrap,
                        "wip": self.wip,
                        "shift": self.shift,
                        "machine_status": status,
                    },
                }
            )

        self.energy_kwh += step_energy
        events.append(
            {
                "type": "energy.update",
                "system": "plant",
                "data": {"energy_kwh": round(self.energy_kwh, 3), "step_kwh": round(step_energy, 3)},
            }
        )
        return events

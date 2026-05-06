import random

# Failure templates keyed by machine type
_FAILURE_TEMPLATES = {
    "corrugator": [
        ("Overheating detected on steam section", "HIGH"),
        ("Vibration anomaly on main drive shaft", "HIGH"),
        ("Paper tension loss – web break risk", "MEDIUM"),
        ("Glue unit pressure drop below threshold", "MEDIUM"),
        ("Corrugating roll bearing wear detected", "HIGH"),
    ],
    "flexo": [
        ("Ink viscosity out of range", "MEDIUM"),
        ("Printing cylinder alignment drift", "MEDIUM"),
        ("Anilox roller partial blockage detected", "HIGH"),
        ("Servo drive fault on impression unit", "HIGH"),
        ("Doctor blade pressure sensor failure", "MEDIUM"),
    ],
    "diecut": [
        ("Die board wear above maintenance threshold", "HIGH"),
        ("Stripping unit jam – feed stopped", "HIGH"),
        ("Counter-ejector misalign detected", "MEDIUM"),
        ("Cutting pressure inconsistency", "MEDIUM"),
        ("Brake system delayed response", "HIGH"),
    ],
    "folder_gluer": [
        ("Glue nozzle blockage on side seam", "HIGH"),
        ("Folding section misalignment", "MEDIUM"),
        ("Pre-breaker score cracking detected", "MEDIUM"),
        ("Belt tension loss on outfeed conveyor", "HIGH"),
        ("Quality camera: barcode read failure rate high", "MEDIUM"),
    ],
}

_GENERIC_FAILURE = ("Anomaly detected – inspection required", "MEDIUM")


class FailureEngine:
    def __init__(self, mode="real_time"):
        self.mode = mode
        # Base probabilities
        self.anomaly_rate = 0.05
        self.energy_spike_rate = 0.03
        if mode == "chaos":
            self.anomaly_rate = 0.20
            self.energy_spike_rate = 0.15

    def maybe_fail(self, state) -> list:
        events = []

        # --- Machine anomalies: weighted by degradation ---
        for machine_id, machine in state.machines.items():
            health = float(machine.get("health", 1.0))
            wear = float(machine.get("wear", 0.0))
            temp = float(machine.get("temp", 50.0))
            vibration = float(machine.get("vibration", 1.0))
            mtype = machine.get("type", "corrugator")
            status = machine.get("status", "RUNNING")

            # Only generate anomalies for RUNNING machines (or FAILURE state)
            if status not in {"RUNNING", "FAILURE"}:
                continue

            # Dynamic probability: higher wear / lower health = more failures
            degradation_factor = (1.0 - health) * 0.5 + wear * 0.5
            effective_rate = self.anomaly_rate * (1.0 + degradation_factor * 3.0)

            if random.random() < effective_rate:
                templates = _FAILURE_TEMPLATES.get(mtype, [_GENERIC_FAILURE])
                description, base_severity = random.choice(templates)

                # Escalate severity if temp or vibration are extreme
                severity = base_severity
                if temp > 95.0 or vibration > 8.0:
                    severity = "CRITICAL"
                elif temp > 85.0 or vibration > 6.0:
                    severity = "HIGH"

                events.append(
                    {
                        "type": "machine.anomaly",
                        "machine": machine_id,
                        "severity": severity,
                        "data": {
                            "description": description,
                            "vibration": round(vibration, 2),
                            "temperature": round(temp, 1),
                            "wear": round(wear, 3),
                            "risk": round(min(1.0, degradation_factor + 0.3), 2),
                        },
                    }
                )

        # --- Energy spike (plant-level) ---
        if random.random() < self.energy_spike_rate:
            events.append(
                {
                    "type": "energy.spike",
                    "system": "boiler",
                    "gas_m3": int(random.uniform(4000, 7000)),
                    "severity": "MEDIUM",
                }
            )

        # --- WIP congestion ---
        if state.wip > 30000:
            events.append(
                {
                    "type": "wip.congestion",
                    "severity": "HIGH" if state.wip > 50000 else "MEDIUM",
                    "value": state.wip,
                }
            )

        # --- Low inventory alerts ---
        for item, level in state.inventory.items():
            threshold = {"glue_l": 500.0, "ink_kg": 200.0, "oil_l": 50.0}.get(item, 100.0)
            if level <= threshold:
                events.append(
                    {
                        "type": "inventory.low",
                        "item": item,
                        "level": round(level, 1),
                        "threshold": threshold,
                        "severity": "HIGH" if level <= threshold * 0.3 else "MEDIUM",
                    }
                )

        return events


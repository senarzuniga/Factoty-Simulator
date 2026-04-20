import random


class FailureEngine:
    def __init__(self, mode="real_time"):
        self.mode = mode
        self.anomaly_rate = 0.05
        self.energy_spike_rate = 0.03
        if mode == "chaos":
            self.anomaly_rate = 0.20
            self.energy_spike_rate = 0.15

    def maybe_fail(self, state):
        events = []

        if random.random() < self.anomaly_rate:
            events.append(
                {
                    "type": "machine.anomaly",
                    "machine": "CORR-01",
                    "severity": "high",
                    "data": {
                        "vibration": 7.5,
                        "temperature": 92,
                        "risk": 0.9,
                    },
                }
            )

        if random.random() < self.energy_spike_rate:
            events.append(
                {
                    "type": "energy.spike",
                    "system": "boiler",
                    "gas_m3": 5000,
                }
            )

        if state.wip > 30000:
            events.append(
                {
                    "type": "wip.congestion",
                    "severity": "medium",
                    "value": state.wip,
                }
            )

        return events


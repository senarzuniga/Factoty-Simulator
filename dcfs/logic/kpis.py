from dcfs.logic.oee import calculate_oee


class KPIEngine:
    def compute(self, state):
        corr = state.machines["CORR-01"]
        availability = max(0.0, min(1.0, corr["health"]))
        performance = max(0.0, corr["speed"] / 300.0)
        quality = 1 - (state.scrap / (state.scrap + state.wip + 1))

        oee = calculate_oee(availability, performance, quality)
        return {
            "oee": round(oee, 3),
            "health_avg": sum(machine["health"] for machine in state.machines.values())
            / len(state.machines),
            "wip": state.wip,
            "scrap": state.scrap,
            "energy_kwh": round(state.energy_kwh, 3),
        }


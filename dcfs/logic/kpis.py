from dcfs.engine.factory_state import SPEED_REFERENCE
from dcfs.logic.oee import calculate_oee


class KPIEngine:
    def compute(self, state) -> dict:
        machine_kpis = {}
        oee_values = []
        total_health = 0.0

        for machine_id, machine in state.machines.items():
            mtype = machine.get("type", "corrugator")
            ref_speed = SPEED_REFERENCE.get(mtype, 300.0)
            health = max(0.0, min(1.0, float(machine.get("health", 0.0))))
            speed = float(machine.get("speed", 0.0))
            status = machine.get("status", "RUNNING")

            availability = health
            performance = min(1.0, speed / ref_speed) if ref_speed > 0 else 0.0
            # Quality degrades with wear; FAILURE machines get quality=0
            wear = float(machine.get("wear", 0.0))
            quality = max(0.0, 1.0 - wear * 0.3) if status not in {"FAILURE"} else 0.0
            oee = calculate_oee(availability, performance, quality)

            machine_kpis[machine_id] = {
                "oee": round(oee, 3),
                "availability": round(availability, 3),
                "performance": round(performance, 3),
                "quality": round(quality, 3),
                "status": status,
            }
            oee_values.append(oee)
            total_health += health

        plant_oee = round(sum(oee_values) / len(oee_values), 3) if oee_values else 0.0
        health_avg = round(total_health / len(state.machines), 3) if state.machines else 0.0

        return {
            "oee": plant_oee,
            "machine_kpis": machine_kpis,
            "health_avg": health_avg,
            "wip": state.wip,
            "scrap": state.scrap,
            "energy_kwh": round(state.energy_kwh, 3),
            "total_output": state.total_output,
            "inventory": dict(state.inventory),
        }


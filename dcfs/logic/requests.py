import uuid
from datetime import datetime, timezone
from typing import Dict, List, Tuple

# Spare part descriptions per machine type for FAILURE events
_SPARE_PART_DESCRIPTIONS = {
    "corrugator": "Bearing and corrugating roll replacement required after failure",
    "flexo": "Impression cylinder bearing and gear set replacement required",
    "diecut": "Cutting die and stripping board replacement after failure",
    "folder_gluer": "Folding belt and glue unit seal replacement required",
}

# Consumable descriptions per machine type
_CONSUMABLE_DESCRIPTIONS = {
    "corrugator": "Glue replenishment and steam seals replacement due to wear",
    "flexo": "Ink and anilox roller cleaning kit replenishment",
    "diecut": "Cutting foam strips and ejection rubber replacement",
    "folder_gluer": "Glue sticks and belt replacement due to wear",
}

# Service descriptions per alert type
_SERVICE_DESCRIPTIONS = {
    "HIGH": "Urgent corrective maintenance intervention required",
    "CRITICAL": "Emergency maintenance intervention – production risk",
    "MEDIUM": "Scheduled inspection and preventive maintenance required",
    "LOW": "Routine service and lubrication required",
}

# Inventory-triggered CONSUMABLE requests
_INVENTORY_CONSUMABLE = {
    "glue_l": ("CONSUMABLE", "Glue stock replenishment – running low", "HIGH"),
    "ink_kg": ("CONSUMABLE", "Ink cartridge replenishment – running low", "MEDIUM"),
    "oil_l": ("CONSUMABLE", "Maintenance oil replenishment – running low", "MEDIUM"),
}


class RequestGenerator:
    CONSUMABLE_WEAR_THRESHOLD = 0.80
    INVENTORY_REORDER_THRESHOLD = {
        "glue_l": 1000.0,
        "ink_kg": 400.0,
        "oil_l": 100.0,
    }

    def __init__(self, min_steps_between_same_request: int = 5):
        self.min_steps_between_same_request = min_steps_between_same_request
        self._last_generated_step: Dict[Tuple[str, str], int] = {}
        self._step = 0

    @staticmethod
    def _iso_now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def _can_generate(self, key: str, request_type: str) -> bool:
        ckey = (key, request_type)
        last_step = self._last_generated_step.get(ckey)
        if last_step is None:
            return True
        return (self._step - last_step) >= self.min_steps_between_same_request

    def _mark_generated(self, key: str, request_type: str) -> None:
        self._last_generated_step[(key, request_type)] = self._step

    def _machine_type(self, machine_id: str, state) -> str:
        machine = state.machines.get(machine_id, {})
        return machine.get("type", "corrugator")

    def generate_from_events(self, events: List[dict], state) -> List[dict]:
        self._step += 1
        generated: List[dict] = []

        for event in events:
            event_type = event.get("type")
            machine_id = event.get("machine_id") or event.get("machine") or "plant"
            severity = str(event.get("severity", "MEDIUM")).upper()
            mtype = self._machine_type(machine_id, state)

            # --- SERVICE from machine alerts ---
            if event_type in {"MACHINE_ALERT", "machine.anomaly"}:
                request_type = "SERVICE"
                if not self._can_generate(machine_id, request_type):
                    continue
                description = _SERVICE_DESCRIPTIONS.get(severity, _SERVICE_DESCRIPTIONS["MEDIUM"])
                generated.append(
                    {
                        "request_id": f"req_{uuid.uuid4().hex}",
                        "type": request_type,
                        "machine_id": machine_id,
                        "machine_type": mtype,
                        "description": description,
                        "urgency": "HIGH" if severity in {"HIGH", "CRITICAL"} else "MEDIUM",
                        "created_at": self._iso_now(),
                        "source_event_id": event.get("event_id"),
                    }
                )
                self._mark_generated(machine_id, request_type)
                continue

            # --- SPARE_PART from machine failure transitions ---
            if event_type == "MACHINE_STATUS_CHANGE" and event.get("new_status") == "FAILURE":
                request_type = "SPARE_PART"
                if not self._can_generate(machine_id, request_type):
                    continue
                description = _SPARE_PART_DESCRIPTIONS.get(
                    mtype, "Failure recovery component replacement required"
                )
                generated.append(
                    {
                        "request_id": f"req_{uuid.uuid4().hex}",
                        "type": request_type,
                        "machine_id": machine_id,
                        "machine_type": mtype,
                        "description": description,
                        "urgency": "HIGH",
                        "created_at": self._iso_now(),
                        "source_event_id": event.get("event_id"),
                    }
                )
                self._mark_generated(machine_id, request_type)

            # --- CONSUMABLE from inventory.low events ---
            if event_type == "inventory.low":
                item = event.get("item", "")
                if item in _INVENTORY_CONSUMABLE and self._can_generate(item, "CONSUMABLE"):
                    rtype, desc, urgency = _INVENTORY_CONSUMABLE[item]
                    generated.append(
                        {
                            "request_id": f"req_{uuid.uuid4().hex}",
                            "type": rtype,
                            "machine_id": "plant",
                            "machine_type": "plant",
                            "description": desc,
                            "urgency": urgency,
                            "created_at": self._iso_now(),
                            "source_event_id": event.get("event_id"),
                        }
                    )
                    self._mark_generated(item, "CONSUMABLE")

        # --- CONSUMABLE from machine wear threshold ---
        for machine_id, machine in state.machines.items():
            wear = float(machine.get("wear", 0.0))
            status = machine.get("status", "RUNNING")
            mtype = machine.get("type", "corrugator")
            if (
                wear >= self.CONSUMABLE_WEAR_THRESHOLD
                and status in {"RUNNING", "IDLE"}
                and self._can_generate(machine_id, "CONSUMABLE")
            ):
                description = _CONSUMABLE_DESCRIPTIONS.get(
                    mtype, "Consumable replenishment due to wear threshold"
                )
                generated.append(
                    {
                        "request_id": f"req_{uuid.uuid4().hex}",
                        "type": "CONSUMABLE",
                        "machine_id": machine_id,
                        "machine_type": mtype,
                        "description": description,
                        "urgency": "HIGH" if wear >= 0.95 else "MEDIUM",
                        "created_at": self._iso_now(),
                        "source_event_id": None,
                    }
                )
                self._mark_generated(machine_id, "CONSUMABLE")

        # --- CONSUMABLE from inventory reorder levels ---
        for item, threshold in self.INVENTORY_REORDER_THRESHOLD.items():
            level = state.inventory.get(item, 0.0)
            if level <= threshold and self._can_generate(item, "REORDER"):
                if item in _INVENTORY_CONSUMABLE:
                    rtype, desc, urgency = _INVENTORY_CONSUMABLE[item]
                    generated.append(
                        {
                            "request_id": f"req_{uuid.uuid4().hex}",
                            "type": rtype,
                            "machine_id": "plant",
                            "machine_type": "plant",
                            "description": f"{desc} (reorder level: {level:.0f})",
                            "urgency": "HIGH" if level <= threshold * 0.3 else urgency,
                            "created_at": self._iso_now(),
                            "source_event_id": None,
                        }
                    )
                    self._mark_generated(item, "REORDER")

        return generated

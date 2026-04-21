import uuid
from datetime import datetime, timezone
from typing import Dict, List, Tuple


class RequestGenerator:
    DEFAULT_SEVERITY = "MEDIUM"
    CONSUMABLE_WEAR_THRESHOLD = 0.85

    def __init__(self, min_steps_between_same_request: int = 5):
        self.min_steps_between_same_request = min_steps_between_same_request
        self._last_generated_step: Dict[Tuple[str, str], int] = {}
        self._step = 0

    @staticmethod
    def _iso_now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def _can_generate(self, machine_id: str, request_type: str) -> bool:
        key = (machine_id, request_type)
        last_step = self._last_generated_step.get(key)
        if last_step is None:
            return True
        return (self._step - last_step) >= self.min_steps_between_same_request

    def _mark_generated(self, machine_id: str, request_type: str) -> None:
        self._last_generated_step[(machine_id, request_type)] = self._step

    def generate_from_events(self, events: List[dict], state) -> List[dict]:
        self._step += 1
        generated: List[dict] = []

        for event in events:
            event_type = event.get("type")
            machine_id = event.get("machine_id") or event.get("machine") or "plant"
            severity = str(event.get("severity", self.DEFAULT_SEVERITY)).upper()

            if event_type in {"MACHINE_ALERT", "machine.anomaly"}:
                request_type = "SERVICE"
                if not self._can_generate(machine_id, request_type):
                    continue
                generated.append(
                    {
                        "request_id": f"req_{uuid.uuid4().hex}",
                        "type": request_type,
                        "machine_id": machine_id,
                        "description": "Inspection and corrective intervention required",
                        "urgency": "HIGH" if severity in {"HIGH", "CRITICAL"} else "MEDIUM",
                        "created_at": self._iso_now(),
                        "source_event_id": event.get("event_id"),
                    }
                )
                self._mark_generated(machine_id, request_type)
                continue

            if event_type in {"MACHINE_STATUS_CHANGE"} and event.get("new_status") == "FAILURE":
                request_type = "SPARE_PART"
                if not self._can_generate(machine_id, request_type):
                    continue
                generated.append(
                    {
                        "request_id": f"req_{uuid.uuid4().hex}",
                        "type": request_type,
                        "machine_id": machine_id,
                        "description": "Failure recovery component replacement required",
                        "urgency": "HIGH",
                        "created_at": self._iso_now(),
                        "source_event_id": event.get("event_id"),
                    }
                )
                self._mark_generated(machine_id, request_type)

        for machine_id, machine in state.machines.items():
            wear = float(machine.get("wear", 0.0))
            status = machine.get("status", "RUNNING")
            if (
                wear >= self.CONSUMABLE_WEAR_THRESHOLD
                and status in {"RUNNING", "IDLE"}
                and self._can_generate(machine_id, "CONSUMABLE")
            ):
                generated.append(
                    {
                        "request_id": f"req_{uuid.uuid4().hex}",
                        "type": "CONSUMABLE",
                        "machine_id": machine_id,
                        "description": "Consumable replenishment due to wear threshold",
                        "urgency": "MEDIUM",
                        "created_at": self._iso_now(),
                        "source_event_id": None,
                    }
                )
                self._mark_generated(machine_id, "CONSUMABLE")

        return generated

import asyncio
import inspect
import random
import uuid
from datetime import datetime, timezone
from typing import Any, Callable, List, Optional

from dcfs.engine.event_bus import EventBus
from dcfs.engine.factory_state import FactoryState
from dcfs.engine.time_engine import TimeEngine
from dcfs.logic.failures import FailureEngine
from dcfs.logic.kpis import KPIEngine
from dcfs.logic.requests import RequestGenerator

# Callback signature: (state after step, published non-KPI events, computed KPI dict).
StepCallback = Callable[[FactoryState, List[dict], dict], Any]
MIN_STEP_VARIANCE_FACTOR = 0.7
MAX_STEP_VARIANCE_FACTOR = 1.3


class FactorySimulator:
    def __init__(
        self,
        mode: str = "real_time",
        time_step: Optional[float] = None,
        step_callbacks: Optional[List[StepCallback]] = None,
    ):
        self.state = FactoryState()
        self.bus = EventBus()
        self.failures = FailureEngine(mode=mode)
        self.kpis = KPIEngine()
        self.requests = RequestGenerator()
        self.time_engine = TimeEngine(mode=mode, step_seconds=time_step)
        self.step_callbacks = step_callbacks or []
        self.last_events: List[dict] = []
        self.last_requests: List[dict] = []
        self.last_factory_status: dict = {}

    async def run(self, max_steps: Optional[int] = None):
        steps = 0
        while max_steps is None or steps < max_steps:
            await self.step()
            steps += 1
            await asyncio.sleep(
                random.uniform(
                    self.time_engine.step_seconds * MIN_STEP_VARIANCE_FACTOR,
                    self.time_engine.step_seconds * MAX_STEP_VARIANCE_FACTOR,
                )
            )

    async def step(self):
        before_status = {machine_id: machine.get("status", "RUNNING") for machine_id, machine in self.state.machines.items()}
        self.state.update()
        production_events = self.state.generate_production()
        failure_events = self.failures.maybe_fail(self.state)
        kpi = self.kpis.compute(self.state)
        machine_status_events = self._build_machine_status_events(before_status)
        normalized_events = self._build_normalized_events(production_events, failure_events, machine_status_events, kpi)
        generated_requests = self.requests.generate_from_events(normalized_events, self.state)
        published_events = production_events + failure_events + machine_status_events + normalized_events

        for event in published_events:
            await self.bus.publish(event)

        await self.bus.publish({"type": "kpi.update", "data": kpi})
        for request_event in generated_requests:
            await self.bus.publish({"type": "request.generated", "data": request_event})

        self.last_events = normalized_events
        self.last_requests = generated_requests
        self.last_factory_status = self._build_factory_status_event(kpi)

        await self._notify_step_callbacks(published_events, kpi)
        return published_events

    async def _notify_step_callbacks(self, events: List[dict], kpi: dict) -> None:
        for callback in self.step_callbacks:
            result = callback(self.state, events, kpi)
            if inspect.isawaitable(result):
                await result

    @staticmethod
    def _iso_now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def _event_id(self) -> str:
        return f"evt_{uuid.uuid4().hex}"

    def _build_machine_status_events(self, before_status: dict) -> List[dict]:
        events: List[dict] = []
        for machine_id, machine in self.state.machines.items():
            old = before_status.get(machine_id, "RUNNING")
            new = machine.get("status", "RUNNING")
            if old != new:
                events.append(
                    {
                        "type": "machine.status_change",
                        "machine": machine_id,
                        "old_status": old,
                        "new_status": new,
                    }
                )
        return events

    def _build_normalized_events(
        self,
        production_events: List[dict],
        failure_events: List[dict],
        machine_status_events: List[dict],
        kpi: dict,
    ) -> List[dict]:
        now = self._iso_now()
        events: List[dict] = []

        for event in machine_status_events:
            events.append(
                {
                    "event_id": self._event_id(),
                    "type": "MACHINE_STATUS_CHANGE",
                    "machine_id": event["machine"],
                    "old_status": event["old_status"],
                    "new_status": event["new_status"],
                    "shift": self.state.shift,
                    "timestamp": now,
                }
            )

        for event in production_events:
            if event.get("type") != "production.update":
                continue
            data = event.get("data", {})
            events.append(
                {
                    "event_id": self._event_id(),
                    "type": "PRODUCTION_UPDATE",
                    "machine_id": event.get("machine"),
                    "output": int(data.get("produced_m2", 0)),
                    "scrap": int(data.get("scrap", 0)),
                    "wip": int(data.get("wip", self.state.wip)),
                    "shift": self.state.shift,
                    "timestamp": now,
                }
            )

        for event in failure_events:
            if event.get("type") == "machine.anomaly":
                events.append(
                    {
                        "event_id": self._event_id(),
                        "type": "MACHINE_ALERT",
                        "machine_id": event.get("machine"),
                        "severity": str(event.get("severity", "HIGH")).upper(),
                        "description": "Machine anomaly detected",
                        "timestamp": now,
                    }
                )
            if event.get("type") == "energy.spike":
                events.append(
                    {
                        "event_id": self._event_id(),
                        "type": "MACHINE_ALERT",
                        "machine_id": "plant",
                        "severity": "MEDIUM",
                        "description": "Energy spike detected",
                        "timestamp": now,
                    }
                )

        events.append(self._build_factory_status_event(kpi))
        return events

    def _build_factory_status_event(self, kpi: dict) -> dict:
        running = sum(1 for machine in self.state.machines.values() if machine.get("status") == "RUNNING")
        return {
            "event_id": self._event_id(),
            "type": "FACTORY_STATUS_UPDATE",
            "factory_running": True,
            "shift": self.state.shift,
            "machines_running": running,
            "machines_total": len(self.state.machines),
            "oee": float(kpi.get("oee", 0.0)),
            "timestamp": self._iso_now(),
        }

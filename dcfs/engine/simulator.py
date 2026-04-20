import asyncio
import inspect
from typing import Any, Callable, List, Optional

from dcfs.engine.event_bus import EventBus
from dcfs.engine.factory_state import FactoryState
from dcfs.engine.time_engine import TimeEngine
from dcfs.logic.failures import FailureEngine
from dcfs.logic.kpis import KPIEngine

StepCallback = Callable[[FactoryState, List[dict], dict], Any]


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
        self.time_engine = TimeEngine(mode=mode, step_seconds=time_step)
        self.step_callbacks = step_callbacks or []

    async def run(self, max_steps: Optional[int] = None):
        steps = 0
        while max_steps is None or steps < max_steps:
            await self.step()
            steps += 1
            await asyncio.sleep(self.time_engine.step_seconds)

    async def step(self):
        self.state.update()
        events = self.state.generate_production()
        failure_events = self.failures.maybe_fail(self.state)
        kpi = self.kpis.compute(self.state)
        published_events = events + failure_events

        for event in published_events:
            await self.bus.publish(event)

        await self.bus.publish({"type": "kpi.update", "data": kpi})
        await self._notify_step_callbacks(published_events, kpi)
        return published_events

    async def _notify_step_callbacks(self, events: List[dict], kpi: dict) -> None:
        for callback in self.step_callbacks:
            result = callback(self.state, events, kpi)
            if inspect.isawaitable(result):
                await result

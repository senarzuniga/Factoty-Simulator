import asyncio
from typing import Optional

from dcfs.engine.event_bus import EventBus
from dcfs.engine.factory_state import FactoryState
from dcfs.engine.time_engine import TimeEngine
from dcfs.logic.failures import FailureEngine
from dcfs.logic.kpis import KPIEngine


class FactorySimulator:
    def __init__(self, mode: str = "real_time", time_step: Optional[float] = None):
        self.state = FactoryState()
        self.bus = EventBus()
        self.failures = FailureEngine(mode=mode)
        self.kpis = KPIEngine()
        self.time_engine = TimeEngine(mode=mode, step_seconds=time_step)

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

        for event in events + failure_events:
            await self.bus.publish(event)

        await self.bus.publish({"type": "kpi.update", "data": kpi})


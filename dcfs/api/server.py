import asyncio
import random
from collections import deque
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Deque, Dict, List, Optional, Set

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from dcfs.engine.simulator import FactorySimulator

MAX_EVENTS = 2000
MAX_REQUESTS = 1000
MIN_BROADCAST_DELAY_SECONDS = 0.5
MAX_BROADCAST_DELAY_SECONDS = 1.8


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class SimulationRuntime:
    def __init__(self) -> None:
        self.simulator = FactorySimulator(mode="real_time", time_step=1.0)
        self.running = False
        self._task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()
        self.events: Deque[dict] = deque(maxlen=MAX_EVENTS)
        self.requests: Deque[dict] = deque(maxlen=MAX_REQUESTS)
        self.clients: Set[WebSocket] = set()

    async def start(self) -> Dict[str, object]:
        async with self._lock:
            if self.running:
                return {"running": True}
            self.running = True
            self._task = asyncio.create_task(self._run_loop())
            return {"running": True}

    async def stop(self) -> Dict[str, object]:
        async with self._lock:
            if not self.running:
                return {"running": False}
            self.running = False
            task = self._task

        if task:
            await task
        return {"running": False}

    async def _run_loop(self) -> None:
        while self.running:
            await self.simulator.step()

            new_events = list(self.simulator.last_events)
            new_requests = list(self.simulator.last_requests)
            factory_status = dict(self.simulator.last_factory_status)

            self.events.extend(new_events)
            self.requests.extend(new_requests)

            if factory_status:
                await self._broadcast({"type": "FACTORY_STATUS_UPDATE", "payload": factory_status})
            for event in new_events:
                await self._broadcast({"type": "NEW_EVENT", "payload": event})
            for request in new_requests:
                await self._broadcast({"type": "NEW_REQUEST", "payload": request})

            await asyncio.sleep(random.uniform(MIN_BROADCAST_DELAY_SECONDS, MAX_BROADCAST_DELAY_SECONDS))

    async def _broadcast(self, message: dict) -> None:
        stale_clients = []
        for client in self.clients:
            try:
                await client.send_json(message)
            except Exception:
                stale_clients.append(client)
        for client in stale_clients:
            self.clients.discard(client)

    async def add_client(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.clients.add(websocket)
        await websocket.send_json({"type": "FACTORY_STATUS_UPDATE", "payload": self.get_status()})

    def remove_client(self, websocket: WebSocket) -> None:
        self.clients.discard(websocket)

    def get_status(self) -> Dict[str, object]:
        state = self.simulator.state
        running_machines = sum(1 for machine in state.machines.values() if machine.get("status") == "RUNNING")
        return {
            "factory_running": self.running,
            "shift": state.shift,
            "timestamp": _iso_now(),
            "machines_running": running_machines,
            "machines_total": len(state.machines),
            "wip": state.wip,
            "scrap": state.scrap,
            "energy_kwh": round(state.energy_kwh, 3),
            "total_output": state.total_output,
        }

    def get_machines(self) -> List[dict]:
        machines: List[dict] = []
        for machine_id, machine in self.simulator.state.machines.items():
            machine_payload = {
                "machine_id": machine_id,
                "status": machine.get("status", "RUNNING"),
                "health": round(float(machine.get("health", 0.0)), 4),
                "speed": round(float(machine.get("speed", 0.0)), 2),
                "efficiency": round(float(machine.get("efficiency", 0.0)), 4),
                "wear": round(float(machine.get("wear", 0.0)), 4),
                "temp": round(float(machine["temp"]), 2) if "temp" in machine else None,
                "vibration": round(float(machine["vibration"]), 2) if "vibration" in machine else None,
                "shift": self.simulator.state.shift,
                "updated_at": self.simulator.state.last_updated_at,
            }
            machines.append(machine_payload)
        return machines


runtime = SimulationRuntime()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    await runtime.start()
    try:
        yield
    finally:
        await runtime.stop()


app = FastAPI(title="Factory Simulator API", version="1.0.0", lifespan=lifespan)


@app.get("/factory/status")
async def get_factory_status() -> Dict[str, object]:
    return runtime.get_status()


@app.get("/factory/machines")
async def get_factory_machines() -> List[dict]:
    return runtime.get_machines()


@app.get("/factory/events")
async def get_factory_events() -> List[dict]:
    return list(runtime.events)


@app.get("/factory/requests")
async def get_factory_requests() -> List[dict]:
    return list(runtime.requests)


@app.post("/factory/start")
async def start_factory() -> Dict[str, object]:
    return await runtime.start()


@app.post("/factory/stop")
async def stop_factory() -> Dict[str, object]:
    return await runtime.stop()


@app.websocket("/factory/stream")
async def stream_factory(websocket: WebSocket) -> None:
    await runtime.add_client(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        runtime.remove_client(websocket)

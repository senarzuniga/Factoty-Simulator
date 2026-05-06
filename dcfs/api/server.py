import asyncio
import random
import logging
import os
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

# Set log level from environment variable or default to INFO
log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
logger = logging.getLogger(__name__)

# Configure JSON logging
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter(
    '%(asctime)s %(name)s %(levelname)s %(message)s %(request_id)s %(user_id)s'
)
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)
logger.setLevel(log_level)


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _log_error(message: str, error: Exception, context: Optional[dict] = None) -> None:
    logger.error(
        "{message} | Error: {error} | Context: {context} | Stack Trace: {stack_trace}",
        extra={
            "message": message,
            "error": str(error),
            "context": context or {},
            "stack_trace": logging.format_exc(),
            "request_id": context.get('request_id') if context else None,
            "user_id": context.get('user_id') if context else None
        }
    )


class SimulationRuntime:
    def __init__(self) -> None:
        self.simulator = FactorySimulator(mode="real_time", time_step=1.0)
        self.running = False
        self._task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()
        self.events: Deque[dict] = deque(maxlen=MAX_EVENTS)
        self.requests: Deque[dict] = deque(maxlen=MAX_REQUESTS)
        self.clients: Set[WebSocket] = set()
        self._last_kpi: dict = {}

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
            try:
                await self.simulator.step()

<<<<<<< Updated upstream
                new_events = list(self.simulator.last_events)
                new_requests = list(self.simulator.last_requests)
                factory_status = dict(self.simulator.last_factory_status)
=======
            new_events = list(self.simulator.last_events)
            new_requests = list(self.simulator.last_requests)
            factory_status = dict(self.simulator.last_factory_status)
            self._last_kpi = self.simulator.kpis.compute(self.simulator.state)
>>>>>>> Stashed changes

                self.events.extend(new_events)
                self.requests.extend(new_requests)

                if factory_status:
                    await self._broadcast({"type": "FACTORY_STATUS_UPDATE", "payload": factory_status})
                for event in new_events:
                    await self._broadcast({"type": "NEW_EVENT", "payload": event})
                for request in new_requests:
                    await self._broadcast({"type": "NEW_REQUEST", "payload": request})

                await asyncio.sleep(random.uniform(MIN_BROADCAST_DELAY_SECONDS, MAX_BROADCAST_DELAY_SECONDS))
            except Exception as e:
                _log_error("Error in simulation loop", e)

    async def _broadcast(self, message: dict) -> None:
        stale_clients = []
        for client in self.clients:
            try:
                await client.send_json(message)
            except Exception as e:
                _log_error("Error broadcasting to client", e, context={"message": message})
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
        running = sum(1 for m in state.machines.values() if m.get("status") == "RUNNING")
        failure = sum(1 for m in state.machines.values() if m.get("status") == "FAILURE")
        return {
            "factory_running": self.running,
            "shift": state.shift,
            "timestamp": _iso_now(),
            "machines_running": running,
            "machines_failure": failure,
            "machines_total": len(state.machines),
            "wip": state.wip,
            "scrap": state.scrap,
            "energy_kwh": round(state.energy_kwh, 3),
            "total_output": state.total_output,
            "inventory": dict(state.inventory),
        }

    def get_machines(self) -> List[dict]:
        state = self.simulator.state
        machine_kpis = self._last_kpi.get("machine_kpis", {})
        machines: List[dict] = []
        for machine_id, machine in state.machines.items():
            mkpi = machine_kpis.get(machine_id, {})
            machines.append(
                {
                    "machine_id": machine_id,
                    "machine_type": machine.get("type"),
                    "status": machine.get("status", "RUNNING"),
                    "health": round(float(machine.get("health", 0.0)), 4),
                    "speed": round(float(machine.get("speed", 0.0)), 2),
                    "speed_min": machine.get("speed_min"),
                    "speed_max": machine.get("speed_max"),
                    "efficiency": round(float(machine.get("efficiency", 0.0)), 4),
                    "wear": round(float(machine.get("wear", 0.0)), 4),
                    "temp": round(float(machine["temp"]), 2),
                    "vibration": round(float(machine["vibration"]), 2),
                    "oee": mkpi.get("oee"),
                    "availability": mkpi.get("availability"),
                    "performance": mkpi.get("performance"),
                    "quality": mkpi.get("quality"),
                    "shift": state.shift,
                    "updated_at": state.last_updated_at,
                }
            )
        return machines

    def get_kpi(self) -> dict:
        if self._last_kpi:
            return self._last_kpi
        return self.simulator.kpis.compute(self.simulator.state)


runtime = SimulationRuntime()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    await runtime.start()
    try:
        yield
    finally:
        await runtime.stop()


app = FastAPI(
    title="Factory Simulator API",
    description="Autonomous industrial data generation system for corrugated cardboard plant.",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content={"detail": exc.errors()})

@app.get("/factory/status", summary="Plant-level status snapshot")
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

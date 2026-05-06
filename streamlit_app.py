"""
Live Factory Simulator Dashboard
Runs an autonomous simulation in a background thread and auto-refreshes.
"""
import asyncio
import threading
import time
from collections import deque
from datetime import datetime, timezone
from typing import Deque, Dict, List

import streamlit as st

from dcfs.engine.simulator import FactorySimulator

st.set_page_config(
    page_title="Factory Simulator – Live",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# Module-level simulation broker (persists across Streamlit reruns)
# ---------------------------------------------------------------------------

_BROKER_KEY = "_factory_broker"


class _SimulationBroker:
    """Runs the asyncio simulation in a background daemon thread."""

    MAX_EVENTS = 200
    MAX_REQUESTS = 100

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._simulator = FactorySimulator(mode="real_time", time_step=1.0)
        self._events: Deque[dict] = deque(maxlen=self.MAX_EVENTS)
        self._requests: Deque[dict] = deque(maxlen=self.MAX_REQUESTS)
        self._kpi: dict = {}
        self._step = 0
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run, daemon=True, name="factory-sim")
        self._thread.start()

    def _run(self) -> None:
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self._async_loop())

    async def _async_loop(self) -> None:
        while True:
            await self._simulator.step()
            kpi = self._simulator.kpis.compute(self._simulator.state)
            with self._lock:
                self._events.extend(self._simulator.last_events)
                self._requests.extend(self._simulator.last_requests)
                self._kpi = kpi
                self._step += 1
            await asyncio.sleep(1.0)

    # -- Read-only accessors (called from Streamlit main thread) ------------

    def snapshot(self) -> dict:
        with self._lock:
            state = self._simulator.state
            machines = {
                mid: dict(m) for mid, m in state.machines.items()
            }
            return {
                "step": self._step,
                "shift": state.shift,
                "wip": state.wip,
                "scrap": state.scrap,
                "energy_kwh": round(state.energy_kwh, 3),
                "total_output": state.total_output,
                "inventory": dict(state.inventory),
                "machines": machines,
                "kpi": dict(self._kpi),
                "events": list(self._events),
                "requests": list(self._requests),
                "last_updated": state.last_updated_at,
            }


def _get_broker() -> _SimulationBroker:
    if _BROKER_KEY not in st.session_state:
        st.session_state[_BROKER_KEY] = _SimulationBroker()
    return st.session_state[_BROKER_KEY]


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

_STATUS_COLOR = {
    "RUNNING": "🟢",
    "IDLE": "🟡",
    "MAINTENANCE": "🔵",
    "FAILURE": "🔴",
}

_SEVERITY_COLOR = {
    "CRITICAL": "🔴",
    "HIGH": "🟠",
    "MEDIUM": "🟡",
    "LOW": "🟢",
}

_MACHINE_TYPE_ICON = {
    "corrugator": "⚙️",
    "flexo": "🖨️",
    "diecut": "✂️",
    "folder_gluer": "📦",
}


def _fmt_ts(iso: str) -> str:
    try:
        dt = datetime.fromisoformat(iso)
        return dt.strftime("%H:%M:%S")
    except Exception:
        return iso or "–"


# ---------------------------------------------------------------------------
# Dashboard layout
# ---------------------------------------------------------------------------

broker = _get_broker()
data = broker.snapshot()

kpi = data.get("kpi", {})
machines: Dict[str, dict] = data.get("machines", {})
events: List[dict] = data.get("events", [])
requests: List[dict] = data.get("requests", [])
inventory: dict = data.get("inventory", {})

# ---- Header ---------------------------------------------------------------
st.title("🏭 Digital Corrugated Factory – Live Simulator")
shift_icon = {"DAY": "☀️", "EVENING": "🌆", "NIGHT": "🌙"}.get(data["shift"], "")
st.caption(
    f"Step **{data['step']}** · Shift **{data['shift']}** {shift_icon} · "
    f"Last update: {_fmt_ts(data.get('last_updated', ''))}"
)

# ---- Top KPI metrics -------------------------------------------------------
m1, m2, m3, m4, m5, m6 = st.columns(6)
m1.metric("Plant OEE", f"{kpi.get('oee', 0):.1%}")
m2.metric("WIP (m²)", f"{data['wip']:,}")
m3.metric("Total Output", f"{data['total_output']:,}")
m4.metric("Scrap (m²)", f"{data['scrap']:,}")
m5.metric("Energy (kWh)", f"{data['energy_kwh']:,.1f}")
m6.metric("Health Avg", f"{kpi.get('health_avg', 0):.1%}")

st.divider()

# ---- Machine status cards --------------------------------------------------
st.subheader("🔩 Machines")
machine_kpis = kpi.get("machine_kpis", {})

cols = st.columns(3)
for idx, (machine_id, machine) in enumerate(machines.items()):
    col = cols[idx % 3]
    with col:
        mtype = machine.get("type", "")
        status = machine.get("status", "RUNNING")
        icon = _MACHINE_TYPE_ICON.get(mtype, "⚙️")
        status_dot = _STATUS_COLOR.get(status, "⚪")
        mkpi = machine_kpis.get(machine_id, {})

        with st.container(border=True):
            st.markdown(f"**{icon} {machine_id}** {status_dot} `{status}`")
            st.caption(f"Type: {mtype}")
            c1, c2 = st.columns(2)
            c1.metric("Health", f"{machine.get('health', 0):.1%}")
            c2.metric("OEE", f"{mkpi.get('oee', 0):.1%}")
            c1.metric("Speed", f"{machine.get('speed', 0):,.0f}")
            c2.metric("Wear", f"{machine.get('wear', 0):.1%}")
            c1.metric("Temp (°C)", f"{machine.get('temp', 0):.1f}")
            c2.metric("Vibration", f"{machine.get('vibration', 0):.2f}")

st.divider()

# ---- Inventory -------------------------------------------------------------
st.subheader("📦 Inventory")
inv_cols = st.columns(len(inventory) or 1)
inv_thresholds = {"glue_l": 1000, "ink_kg": 400, "oil_l": 100}
for i, (item, level) in enumerate(inventory.items()):
    threshold = inv_thresholds.get(item, 100)
    label = item.replace("_", " ").title()
    delta_color = "inverse" if level <= threshold else "normal"
    inv_cols[i].metric(label, f"{level:,.1f}", delta_color=delta_color)

st.divider()

# ---- Events & Requests (side by side) ------------------------------------
left_col, right_col = st.columns(2)

with left_col:
    st.subheader("⚡ Recent Events")
    recent_events = [e for e in reversed(events) if e.get("type") != "FACTORY_STATUS_UPDATE"][:20]
    if recent_events:
        for ev in recent_events:
            etype = ev.get("type", "")
            ts = _fmt_ts(ev.get("timestamp", ""))
            mid = ev.get("machine_id", "")
            if etype == "MACHINE_ALERT":
                sev = ev.get("severity", "MEDIUM")
                dot = _SEVERITY_COLOR.get(sev, "⚪")
                desc = ev.get("description", "")
                st.markdown(f"{dot} `{ts}` **{mid}** — {desc}")
            elif etype == "MACHINE_STATUS_CHANGE":
                old = ev.get("old_status", "")
                new = ev.get("new_status", "")
                st.markdown(f"🔄 `{ts}` **{mid}** `{old}` → `{new}`")
            elif etype == "PRODUCTION_UPDATE":
                output = ev.get("output", 0)
                scrap = ev.get("scrap", 0)
                st.markdown(f"📊 `{ts}` **{mid}** output={output:,} scrap={scrap:,}")
    else:
        st.info("Events will appear as the simulation runs.")

with right_col:
    st.subheader("🛠️ Operational Requests")
    recent_reqs = list(reversed(requests))[:20]
    if recent_reqs:
        for req in recent_reqs:
            rtype = req.get("type", "")
            urg = req.get("urgency", "MEDIUM")
            dot = _SEVERITY_COLOR.get(urg, "⚪")
            mid = req.get("machine_id", "")
            desc = req.get("description", "")
            ts = _fmt_ts(req.get("created_at", ""))
            type_icon = {"SERVICE": "🔧", "SPARE_PART": "🔩", "CONSUMABLE": "🧴"}.get(rtype, "📋")
            st.markdown(f"{dot}{type_icon} `{ts}` **{mid}** — {desc}")
    else:
        st.info("Requests are generated automatically from failures and wear.")

# ---- Auto-refresh ----------------------------------------------------------
st.divider()
auto = st.toggle("Auto-refresh (1 s)", value=True, key="auto_refresh")
if auto:
    time.sleep(1)
    st.rerun()

import streamlit as st

from dcfs.engine.factory_state import FactoryState
from dcfs.logic.kpis import KPIEngine


st.set_page_config(page_title="Factory Simulator", layout="wide")
st.title("Digital Corrugated Factory Simulator")


def _init_state() -> None:
    if "factory_state" not in st.session_state:
        st.session_state.factory_state = FactoryState()
    if "kpi_engine" not in st.session_state:
        st.session_state.kpi_engine = KPIEngine()
    if "step" not in st.session_state:
        st.session_state.step = 0
    if "last_kpi" not in st.session_state:
        st.session_state.last_kpi = st.session_state.kpi_engine.compute(
            st.session_state.factory_state
        )
    if "last_events" not in st.session_state:
        st.session_state.last_events = []


def _run_step() -> None:
    factory_state = st.session_state.factory_state
    factory_state.update()
    st.session_state.last_events = factory_state.generate_production()
    st.session_state.last_kpi = st.session_state.kpi_engine.compute(factory_state)
    st.session_state.step += 1


def _reset() -> None:
    for key in ["factory_state", "kpi_engine", "step", "last_kpi", "last_events"]:
        if key in st.session_state:
            del st.session_state[key]
    _init_state()


_init_state()

col1, col2 = st.columns(2)
with col1:
    if st.button("Run next step"):
        _run_step()
with col2:
    if st.button("Reset simulation"):
        _reset()

state = st.session_state.factory_state
kpi = st.session_state.last_kpi

st.subheader(f"Simulation step: {st.session_state.step}")
metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
metric_col1.metric("OEE", f"{kpi['oee']:.3f}")
metric_col2.metric("WIP", f"{kpi['wip']}")
metric_col3.metric("Scrap", f"{kpi['scrap']}")
metric_col4.metric("Energy (kWh)", f"{kpi['energy_kwh']:.3f}")

st.subheader("Machines")
st.json(state.machines)

st.subheader("Last production events")
if st.session_state.last_events:
    st.json(st.session_state.last_events)
else:
    st.info("Run the first step to generate events.")

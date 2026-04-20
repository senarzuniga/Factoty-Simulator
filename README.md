# Factoty-Simulator

Digital Factory Simulator (DFS) for a corrugated cardboard plant.

## Setup

```bash
python -m pip install -r requirements.txt
```

## Run

```bash
python -m dcfs.main
```

or:

```bash
python main.py
```

## Run with Streamlit

```bash
python -m streamlit run streamlit_app.py
```

## Run in Visual Studio Code

- Open **Run and Debug** and choose:
  - **Streamlit App** (web UI)
  - **Factory Simulator (real_time)** or **Factory Simulator (fast, 25 steps)**
- Or use **Terminal → Run Task...**:
  - **Install dependencies**
  - **Run Streamlit App**

## Behavior

- Simulates plant state in real time (`real_time`, `fast`, `chaos`)
- Generates production, energy, KPI, and failure events
- Calculates OEE every step
- Prints events to console through the event bus (extendable to HTTP/Kafka/WebSocket subscribers)

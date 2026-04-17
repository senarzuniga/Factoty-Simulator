# Factoty-Simulator

Digital Factory Simulator (DFS) for a corrugated cardboard plant.

## Run

```bash
python -m dcfs.main
```

or:

```bash
python main.py
```

## Behavior

- Simulates plant state in real time (`real_time`, `fast`, `chaos`)
- Generates production, energy, KPI, and failure events
- Calculates OEE every step
- Prints events to console through the event bus (extendable to HTTP/Kafka/WebSocket subscribers)

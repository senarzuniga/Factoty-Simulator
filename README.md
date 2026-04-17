# Factory-Simulator

Digital Factory Simulator (DFS) for a corrugated cardboard plant that feeds a Digital Monitoring Platform.

## Database foundation for industrial digital ecosystem

This repository now includes a production-oriented relational schema for:

- Plant assets and machine constraints
- Production orders and minute-level throughput
- WIP buffers and converting queues
- Telemetry, degradation and failures
- Maintenance (preventive, predictive, corrective)
- Spare parts, consumables and service requests
- Energy and cost signals
- Upgrades, consultant recommendations and KPI tracking
- Event publishing to digital platforms

### Files

- `database/schema.sql`
- `database/seed.sql`

### Quick start (SQLite)

```bash
sqlite3 plant_simulator.db < database/schema.sql
sqlite3 plant_simulator.db < database/seed.sql
```

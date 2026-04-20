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

## Company profile and Digital Ecosystem Platform connection

This repository now includes a company profile compatible with the
`Digital-Ecosystem-Platform` company definition:

- `config/company_profile.json`

The profile uses the same required fields as
`Digital-Ecosystem-Platform/config/companies.json` (`id`, `name`, `country`,
`sector`, `machines`, `employees`, `maturity_level`, `annual_revenue_m`,
`installed_base_age_avg_years`, `active_contracts`, `logo_color`).

Run the simulator and sync machine assets + telemetry into the DEP backend:

```bash
python main.py \
  --mode real_time \
  --dep-backend-url http://localhost:8000 \
  --dep-token <DEP_BEARER_TOKEN>
```

Optional:

- `--company-profile /absolute/path/to/company_profile.json` to override the default profile.

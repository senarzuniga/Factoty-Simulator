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

### Setup Instructions

To configure the Digital Ecosystem Platform connection, follow these steps:

1. **Set Environment Variables:**
   - `DEP_BACKEND_URL`: The URL of the DEP backend, e.g., `http://localhost:8000`.
   - `DEP_BEARER_TOKEN`: Your DEP authentication token.

2. **Configuration Files:**
   - Ensure `config/company_profile.json` is correctly filled with your company details.

3. **Command-Line Arguments:**
   - Run the simulator using the following command:
     ```bash
     python -m dcfs.main \
       --mode real_time \
       --dep-backend-url $DEP_BACKEND_URL \
       --dep-token $DEP_BEARER_TOKEN
     ```
   - Optional: Use `--company-profile /absolute/path/to/company_profile.json` to specify a custom company profile.

### Running the Simulator in Different Modes

The simulator can be run in various modes as defined in the `.vscode/launch.json` configurations. Ensure you have the correct setup for each mode:

- **Real-Time Mode:**
  - Use the command provided above to sync machine assets and telemetry in real-time.

- **Batch Mode:**
  - Modify the `--mode` argument to `batch` for batch processing.

- **Simulation Mode:**
  - Use `--mode simulation` to run the simulator in a controlled environment for testing purposes.

## Integration and Configuration Guide

This section provides detailed instructions for integrating and configuring the Digital Factory Simulator with the Digital Ecosystem Platform.

### Environment Variables

To ensure proper communication with the Digital Ecosystem Platform, set the following environment variables:

- `DEP_BACKEND_URL`: The URL of the DEP backend. Example: `http://localhost:8000`.
- `DEP_BEARER_TOKEN`: The bearer token for authentication. Obtain this from your DEP administrator.

### Configuration Files

Ensure that the `config/company_profile.json` file is populated with accurate company details. This file should match the structure required by the Digital Ecosystem Platform.

### Command-Line Arguments

To start the simulator, use the following command:

```bash
python -m dcfs.main \
  --mode real_time \
  --dep-backend-url $DEP_BACKEND_URL \
  --dep-token $DEP_BEARER_TOKEN
```

You can specify a custom company profile using:

```bash
--company-profile /absolute/path/to/company_profile.json
```

### Troubleshooting Tips

- **Connection Errors:** Ensure that `DEP_BACKEND_URL` is correct and that the DEP server is running.
- **Authentication Issues:** Verify that `DEP_BEARER_TOKEN` is valid and has not expired.
- **Configuration File Errors:** Double-check the JSON syntax in `config/company_profile.json`.

## Autonomous real-time factory API

The simulator also exposes an autonomous producer API with no direct coupling to consumers.

Install dependencies:

```bash
pip install -r requirements.txt
```

Run API:

```bash
python -m uvicorn dcfs.api.server:app --host 0.0.0.0 --port 9000
```

Required REST endpoints:

- `GET /factory/status`
- `GET /factory/machines`
- `GET /factory/events`
- `GET /factory/requests`
- `POST /factory/start`
- `POST /factory/stop`

Real-time streaming:

- `WS /factory/stream`
- Outbound message types: `FACTORY_STATUS_UPDATE`, `NEW_EVENT`, `NEW_REQUEST`

Notes:

- Events and requests include unique IDs and ISO8601 timestamps.
- Request generation is event-driven (failures/status changes/wear), not purely random.
- Any external platform (including Digital-Ecosystem-Platform) should consume this simulator via REST/WS.

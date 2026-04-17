PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS plants (
  plant_id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  timezone TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS machines (
  machine_id TEXT PRIMARY KEY,
  plant_id TEXT NOT NULL,
  machine_type TEXT NOT NULL CHECK (machine_type IN ('corrugator', 'flexo', 'diecut', 'folder_gluer')),
  line_section TEXT NOT NULL CHECK (line_section IN ('corrugator', 'converting')),
  max_speed_m_min REAL,
  realistic_speed_min_m_min REAL,
  realistic_speed_max_m_min REAL,
  mtbf_minutes INTEGER NOT NULL,
  maintenance_interval_minutes INTEGER NOT NULL,
  is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (plant_id) REFERENCES plants(plant_id)
);

CREATE TABLE IF NOT EXISTS machine_constraints (
  machine_id TEXT PRIMARY KEY,
  steam_dependency INTEGER NOT NULL DEFAULT 0 CHECK (steam_dependency IN (0, 1)),
  glue_dependency INTEGER NOT NULL DEFAULT 0 CHECK (glue_dependency IN (0, 1)),
  paper_quality_sensitivity INTEGER NOT NULL DEFAULT 0 CHECK (paper_quality_sensitivity IN (0, 1)),
  FOREIGN KEY (machine_id) REFERENCES machines(machine_id)
);

CREATE TABLE IF NOT EXISTS production_jobs (
  job_id TEXT PRIMARY KEY,
  plant_id TEXT NOT NULL,
  product_code TEXT NOT NULL,
  due_at TEXT,
  status TEXT NOT NULL CHECK (status IN ('planned', 'running', 'paused', 'completed', 'cancelled')),
  target_m2 REAL NOT NULL DEFAULT 0,
  target_units INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  started_at TEXT,
  completed_at TEXT,
  FOREIGN KEY (plant_id) REFERENCES plants(plant_id)
);

CREATE TABLE IF NOT EXISTS production_minute (
  ts_minute TEXT NOT NULL,
  plant_id TEXT NOT NULL,
  machine_id TEXT NOT NULL,
  job_id TEXT,
  produced_m2 REAL NOT NULL DEFAULT 0,
  converted_units INTEGER NOT NULL DEFAULT 0,
  scrap_units INTEGER NOT NULL DEFAULT 0,
  throughput_rate_per_hour REAL NOT NULL DEFAULT 0,
  PRIMARY KEY (ts_minute, machine_id),
  FOREIGN KEY (plant_id) REFERENCES plants(plant_id),
  FOREIGN KEY (machine_id) REFERENCES machines(machine_id),
  FOREIGN KEY (job_id) REFERENCES production_jobs(job_id)
);

CREATE TABLE IF NOT EXISTS wip_state_minute (
  ts_minute TEXT NOT NULL,
  plant_id TEXT NOT NULL,
  post_corrugator_m2 REAL NOT NULL DEFAULT 0,
  ready_for_flexo_units INTEGER NOT NULL DEFAULT 0,
  ready_for_die_cut_units INTEGER NOT NULL DEFAULT 0,
  blocked INTEGER NOT NULL DEFAULT 0 CHECK (blocked IN (0, 1)),
  buffer_capacity_m2 REAL NOT NULL DEFAULT 0,
  PRIMARY KEY (ts_minute, plant_id),
  FOREIGN KEY (plant_id) REFERENCES plants(plant_id)
);

CREATE TABLE IF NOT EXISTS converting_queue_minute (
  ts_minute TEXT NOT NULL,
  machine_id TEXT NOT NULL,
  queued_units INTEGER NOT NULL DEFAULT 0,
  starving INTEGER NOT NULL DEFAULT 0 CHECK (starving IN (0, 1)),
  setup_changeover_minutes INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (ts_minute, machine_id),
  FOREIGN KEY (machine_id) REFERENCES machines(machine_id)
);

CREATE TABLE IF NOT EXISTS machine_telemetry_minute (
  ts_minute TEXT NOT NULL,
  machine_id TEXT NOT NULL,
  speed_m_min REAL NOT NULL DEFAULT 0,
  vibration_mm_s REAL NOT NULL DEFAULT 0,
  temperature_c REAL NOT NULL DEFAULT 0,
  health_score REAL NOT NULL CHECK (health_score >= 0 AND health_score <= 1),
  wear_level REAL NOT NULL CHECK (wear_level >= 0 AND wear_level <= 1),
  uptime_minutes INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (ts_minute, machine_id),
  FOREIGN KEY (machine_id) REFERENCES machines(machine_id)
);

CREATE TABLE IF NOT EXISTS maintenance_events (
  maintenance_id TEXT PRIMARY KEY,
  machine_id TEXT NOT NULL,
  maintenance_type TEXT NOT NULL CHECK (maintenance_type IN ('preventive', 'predictive', 'corrective')),
  trigger_reason TEXT,
  recommended_action TEXT,
  scheduled_start_at TEXT,
  started_at TEXT,
  completed_at TEXT,
  downtime_minutes INTEGER NOT NULL DEFAULT 0,
  status TEXT NOT NULL CHECK (status IN ('open', 'scheduled', 'in_progress', 'done', 'cancelled')),
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (machine_id) REFERENCES machines(machine_id)
);

CREATE TABLE IF NOT EXISTS spare_parts (
  part_id TEXT PRIMARY KEY,
  part_name TEXT NOT NULL,
  part_category TEXT NOT NULL CHECK (part_category IN ('critical', 'standard', 'consumable')),
  stock_on_hand INTEGER NOT NULL DEFAULT 0,
  min_stock INTEGER NOT NULL DEFAULT 0,
  lead_time_days INTEGER NOT NULL DEFAULT 0,
  unit_cost_eur REAL NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS spare_part_movements (
  movement_id TEXT PRIMARY KEY,
  part_id TEXT NOT NULL,
  machine_id TEXT,
  maintenance_id TEXT,
  movement_type TEXT NOT NULL CHECK (movement_type IN ('inbound', 'consumed', 'adjustment')),
  quantity INTEGER NOT NULL,
  occurred_at TEXT NOT NULL,
  notes TEXT,
  FOREIGN KEY (part_id) REFERENCES spare_parts(part_id),
  FOREIGN KEY (machine_id) REFERENCES machines(machine_id),
  FOREIGN KEY (maintenance_id) REFERENCES maintenance_events(maintenance_id)
);

CREATE TABLE IF NOT EXISTS external_service_requests (
  request_id TEXT PRIMARY KEY,
  machine_id TEXT,
  service_type TEXT NOT NULL CHECK (service_type IN ('corrugator_oem', 'electrical_specialist', 'mechanical_contractor', 'automation_engineer')),
  requested_at TEXT NOT NULL,
  response_time_hours REAL NOT NULL DEFAULT 0,
  hourly_cost_eur REAL NOT NULL DEFAULT 0,
  effectiveness REAL NOT NULL CHECK (effectiveness >= 0 AND effectiveness <= 1),
  status TEXT NOT NULL CHECK (status IN ('requested', 'scheduled', 'in_progress', 'completed', 'cancelled')),
  FOREIGN KEY (machine_id) REFERENCES machines(machine_id)
);

CREATE TABLE IF NOT EXISTS engineering_upgrades (
  upgrade_id TEXT PRIMARY KEY,
  plant_id TEXT NOT NULL,
  upgrade_name TEXT NOT NULL,
  target_machine_id TEXT,
  investment_cost_eur REAL NOT NULL DEFAULT 0,
  efficiency_gain REAL NOT NULL DEFAULT 0,
  max_speed_gain_m_min REAL NOT NULL DEFAULT 0,
  installation_downtime_hours REAL NOT NULL DEFAULT 0,
  roi_months REAL,
  status TEXT NOT NULL CHECK (status IN ('proposed', 'approved', 'in_progress', 'completed', 'rejected')),
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (plant_id) REFERENCES plants(plant_id),
  FOREIGN KEY (target_machine_id) REFERENCES machines(machine_id)
);

CREATE TABLE IF NOT EXISTS energy_minute (
  ts_minute TEXT NOT NULL,
  plant_id TEXT NOT NULL,
  electricity_kwh REAL NOT NULL DEFAULT 0,
  steam_tons REAL NOT NULL DEFAULT 0,
  gas_m3 REAL NOT NULL DEFAULT 0,
  compressed_air_nm3 REAL NOT NULL DEFAULT 0,
  peak_penalty_eur REAL NOT NULL DEFAULT 0,
  energy_cost_eur REAL NOT NULL DEFAULT 0,
  PRIMARY KEY (ts_minute, plant_id),
  FOREIGN KEY (plant_id) REFERENCES plants(plant_id)
);

CREATE TABLE IF NOT EXISTS consumable_inventory (
  consumable_id TEXT PRIMARY KEY,
  consumable_name TEXT NOT NULL,
  quality_grade TEXT NOT NULL,
  stock_on_hand REAL NOT NULL DEFAULT 0,
  reorder_level REAL NOT NULL DEFAULT 0,
  unit_cost_eur REAL NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS consumable_usage_minute (
  ts_minute TEXT NOT NULL,
  machine_id TEXT NOT NULL,
  consumable_id TEXT NOT NULL,
  quantity_used REAL NOT NULL DEFAULT 0,
  speed_factor REAL NOT NULL DEFAULT 1,
  PRIMARY KEY (ts_minute, machine_id, consumable_id),
  FOREIGN KEY (machine_id) REFERENCES machines(machine_id),
  FOREIGN KEY (consumable_id) REFERENCES consumable_inventory(consumable_id)
);

CREATE TABLE IF NOT EXISTS failure_events (
  failure_id TEXT PRIMARY KEY,
  machine_id TEXT,
  failure_type TEXT NOT NULL CHECK (failure_type IN ('bearing_wear', 'glue_instability', 'electrical_fluctuation', 'operator_error', 'scheduling_delay', 'supplier_delay')),
  severity TEXT NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),
  started_at TEXT NOT NULL,
  resolved_at TEXT,
  downtime_minutes INTEGER NOT NULL DEFAULT 0,
  cost_impact_eur REAL NOT NULL DEFAULT 0,
  FOREIGN KEY (machine_id) REFERENCES machines(machine_id)
);

CREATE TABLE IF NOT EXISTS consultant_recommendations (
  recommendation_id TEXT PRIMARY KEY,
  plant_id TEXT NOT NULL,
  issue TEXT NOT NULL,
  suggestion TEXT NOT NULL,
  expected_gain TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  adopted INTEGER NOT NULL DEFAULT 0 CHECK (adopted IN (0, 1)),
  FOREIGN KEY (plant_id) REFERENCES plants(plant_id)
);

CREATE TABLE IF NOT EXISTS kpi_minute (
  ts_minute TEXT NOT NULL,
  plant_id TEXT NOT NULL,
  machine_id TEXT,
  oee REAL CHECK (oee >= 0 AND oee <= 1),
  energy_per_ton REAL,
  cost_per_unit REAL,
  wip_latency_minutes REAL,
  downtime_cost_eur REAL,
  scrap_cost_eur REAL,
  PRIMARY KEY (ts_minute, plant_id, machine_id),
  FOREIGN KEY (plant_id) REFERENCES plants(plant_id),
  FOREIGN KEY (machine_id) REFERENCES machines(machine_id)
);

CREATE TABLE IF NOT EXISTS shipping_events (
  shipping_id TEXT PRIMARY KEY,
  plant_id TEXT NOT NULL,
  job_id TEXT,
  packed_units INTEGER NOT NULL DEFAULT 0,
  shipped_units INTEGER NOT NULL DEFAULT 0,
  warehouse_movement_units INTEGER NOT NULL DEFAULT 0,
  forklift_cycles INTEGER NOT NULL DEFAULT 0,
  occurred_at TEXT NOT NULL,
  FOREIGN KEY (plant_id) REFERENCES plants(plant_id),
  FOREIGN KEY (job_id) REFERENCES production_jobs(job_id)
);

CREATE TABLE IF NOT EXISTS integration_events (
  event_id TEXT PRIMARY KEY,
  plant_id TEXT NOT NULL,
  event_type TEXT NOT NULL,
  event_source TEXT NOT NULL,
  event_time TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  published INTEGER NOT NULL DEFAULT 0 CHECK (published IN (0, 1)),
  published_at TEXT,
  FOREIGN KEY (plant_id) REFERENCES plants(plant_id)
);

CREATE INDEX IF NOT EXISTS idx_prod_machine_time ON production_minute(machine_id, ts_minute);
CREATE INDEX IF NOT EXISTS idx_telemetry_machine_time ON machine_telemetry_minute(machine_id, ts_minute);
CREATE INDEX IF NOT EXISTS idx_failure_machine_time ON failure_events(machine_id, started_at);
CREATE INDEX IF NOT EXISTS idx_maintenance_machine_status ON maintenance_events(machine_id, status);
CREATE INDEX IF NOT EXISTS idx_events_publish ON integration_events(published, event_time);

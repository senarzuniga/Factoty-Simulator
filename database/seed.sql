INSERT INTO plants (plant_id, name, timezone)
VALUES ('PLANT-DSMITH-01', 'Mid-Size Corrugated Plant', 'Europe/Madrid');

INSERT INTO machines (
  machine_id, plant_id, machine_type, line_section,
  max_speed_m_min, realistic_speed_min_m_min, realistic_speed_max_m_min,
  mtbf_minutes, maintenance_interval_minutes
)
VALUES
  ('BHS-CORR-01', 'PLANT-DSMITH-01', 'corrugator', 'corrugator', 300, 180, 290, 7200, 43200),
  ('FLEXO-01', 'PLANT-DSMITH-01', 'flexo', 'converting', 180, 120, 165, 5400, 28800),
  ('FLEXO-02', 'PLANT-DSMITH-01', 'flexo', 'converting', 170, 115, 160, 5200, 28800),
  ('DIECUT-01', 'PLANT-DSMITH-01', 'diecut', 'converting', 150, 100, 140, 5000, 25200),
  ('FOLDER-GLUER-01', 'PLANT-DSMITH-01', 'folder_gluer', 'converting', 220, 140, 200, 5600, 30000),
  ('FOLDER-GLUER-02', 'PLANT-DSMITH-01', 'folder_gluer', 'converting', 210, 135, 195, 5500, 30000);

INSERT INTO machine_constraints (machine_id, steam_dependency, glue_dependency, paper_quality_sensitivity)
VALUES
  ('BHS-CORR-01', 1, 1, 1),
  ('FLEXO-01', 0, 1, 1),
  ('FLEXO-02', 0, 1, 1),
  ('DIECUT-01', 0, 0, 1),
  ('FOLDER-GLUER-01', 0, 1, 0),
  ('FOLDER-GLUER-02', 0, 1, 0);

INSERT INTO spare_parts (part_id, part_name, part_category, stock_on_hand, min_stock, lead_time_days, unit_cost_eur)
VALUES
  ('SP-BHS-BEARING-01', 'corrugator_roller_bearing', 'critical', 4, 2, 5, 320.00),
  ('SP-BHS-BELT-01', 'drive_belt', 'standard', 8, 3, 4, 95.00),
  ('SP-DIECUT-BLADE-01', 'die_cut_blade', 'consumable', 30, 12, 2, 18.00);

INSERT INTO consumable_inventory (consumable_id, consumable_name, quality_grade, stock_on_hand, reorder_level, unit_cost_eur)
VALUES
  ('CONS-GLUE-01', 'glue', 'A', 12000, 3000, 1.10),
  ('CONS-INK-01', 'ink', 'A', 2500, 800, 3.50),
  ('CONS-OIL-01', 'maintenance_oil', 'A', 900, 250, 4.20);

INSERT INTO consultant_recommendations (recommendation_id, plant_id, issue, suggestion, expected_gain, adopted)
VALUES
  ('CONSULT-001', 'PLANT-DSMITH-01', 'converting_starvation', 'increase_WIP_buffer_by_18_percent', 'OEE +4.2%', 0);

INSERT INTO engineering_upgrades (
  upgrade_id, plant_id, upgrade_name, target_machine_id,
  investment_cost_eur, efficiency_gain, max_speed_gain_m_min,
  installation_downtime_hours, roi_months, status
)
VALUES
  ('UPG-001', 'PLANT-DSMITH-01', 'BHS_speed_modernization', 'BHS-CORR-01', 450000, 0.06, 20, 48, 26, 'proposed');

export type UserRole = "admin" | "operator" | "analyst";

export interface User {
  id: number;
  email: string;
  full_name?: string | null;
  role: UserRole;
  is_active: boolean;
  created_at: string;
}

export interface AuthToken {
  access_token: string;
  token_type: string;
  role: UserRole;
  user_id: number;
  email: string;
  full_name?: string | null;
}

export interface KpiItem {
  label: string;
  value: number;
  unit: string;
  status: "normal" | "warning" | "critical" | "success";
  change_pct?: number | null;
  change_period?: string | null;
}

export interface OverviewKpis {
  current_pv_kw: KpiItem;
  current_load_kw: KpiItem;
  battery_soc_pct: KpiItem;
  grid_import_kw: KpiItem;
  grid_export_kw: KpiItem;
  current_energy_cost: KpiItem;
  renewable_utilization_pct: KpiItem;
  forecasted_pv_next_hour_kw: KpiItem;
  forecasted_load_next_hour_kw: KpiItem;
}

export interface EnergyFlow {
  timestamp: string;
  pv_power_kw: number;
  load_demand_kw: number;
  battery_power_kw: number;
  battery_soc_pct: number;
  grid_import_kw: number;
  grid_export_kw: number;
  flow_pv_to_load_kw: number;
  flow_pv_to_battery_kw: number;
  flow_pv_to_grid_kw: number;
  flow_battery_to_load_kw: number;
  flow_grid_to_load_kw: number;
  operational_status: "Normal" | "Warning" | "Critical";
  status_label: string;
}

export interface TimeSeriesPoint {
  timestamp: string;
  pv_generation_kw: number;
  load_demand_kw: number;
  grid_import_kw: number;
  grid_export_kw: number;
  battery_soc_pct: number;
  battery_power_kw: number;
}

export interface OverviewDashboardData {
  status_label: string;
  operational_status: "Normal" | "Warning" | "Critical";
  operational_status_message: string;
  kpis: OverviewKpis;
  energy_flow: EnergyFlow;
  series: TimeSeriesPoint[];
}

export interface ForecastPoint {
  timestamp: string;
  horizon_hour: number;
  value_kw: number;
  lower_bound_kw?: number | null;
  upper_bound_kw?: number | null;
  is_historical: boolean;
}

export interface PVForecastResponse {
  model_id: string;
  model_name: string;
  forecast_timestamp: string;
  horizon_hours: number;
  is_simulated: boolean;
  unit: string;
  status_label: string;
  forecast_points: ForecastPoint[];
  historical_points: ForecastPoint[];
}

export interface LoadForecastSummary {
  expected_peak_kw: number;
  expected_min_kw: number;
  average_demand_kw: number;
  total_energy_kwh: number;
}

export interface LoadForecastResponse {
  model_id: string;
  model_name: string;
  forecast_timestamp: string;
  horizon_hours: number;
  is_simulated: boolean;
  unit: string;
  status_label: string;
  summary: LoadForecastSummary;
  forecast_points: ForecastPoint[];
  historical_points: ForecastPoint[];
}

export interface CombinedForecastPoint {
  timestamp: string;
  hour: number;
  pv_kw: number;
  load_kw: number;
  net_power_kw: number;
  surplus_deficit_state: "SURPLUS" | "DEFICIT";
}

export interface CombinedForecastResponse {
  forecast_timestamp: string;
  horizon_hours: number;
  total_pv_kwh: number;
  total_load_kwh: number;
  net_energy_kwh: number;
  surplus_hours: number;
  deficit_hours: number;
  status_label: string;
  points: CombinedForecastPoint[];
}

export interface ModelMetadata {
  model_id: string;
  model_name: string;
  model_type: string;
  version: string;
  description?: string | null;
  status: string;
  source?: string | null;
  metrics_json?: string | null;
  is_simulated: boolean;
  updated_at: string;
}

export interface BatteryConfig {
  id?: number;
  capacity_kwh: number;
  initial_soc: number;
  min_soc: number;
  max_soc: number;
  max_charge_kw: number;
  max_discharge_kw: number;
  charge_efficiency: number;
  discharge_efficiency: number;
  battery_health: number;
  is_active: boolean;
  updated_at?: string;
}

export interface BatteryStatus {
  capacity_kwh: number;
  current_soc: number;
  min_soc: number;
  max_soc: number;
  max_charge_kw: number;
  max_discharge_kw: number;
  charge_efficiency: number;
  discharge_efficiency: number;
  battery_health: number;
  current_power_kw: number;
  mode: "CHARGING" | "DISCHARGING" | "IDLE";
  operational_status: "NORMAL" | "WARNING" | "CRITICAL";
  status_label: string;
}

export interface BatteryScheduleStep {
  step_index: number;
  timestamp: string;
  pv_forecast_kw: number;
  load_forecast_kw: number;
  action: "CHARGE" | "DISCHARGE" | "IDLE";
  battery_power_kw: number;
  soc_before: number;
  soc_after: number;
  grid_import_kw: number;
  grid_export_kw: number;
  step_cost: number;
}

export interface BatterySchedule {
  schedule_id: string;
  generated_at: string;
  status: string;
  total_cost: number;
  algorithm: string;
  is_simulated: boolean;
  status_label: string;
  notes?: string | null;
  steps: BatteryScheduleStep[];
}

export interface GridConfig {
  id?: number;
  import_limit_kw: number;
  export_limit_kw: number;
  import_tariff: number;
  export_tariff: number;
  is_active: boolean;
  updated_at?: string;
}

export interface GridStatus {
  current_import_kw: number;
  current_export_kw: number;
  import_limit_kw: number;
  export_limit_kw: number;
  import_tariff: number;
  export_tariff: number;
  current_cost_rate_per_hour: number;
  peak_grid_demand_kw: number;
  renewable_utilization_pct: number;
  status: "NORMAL" | "WARNING" | "CRITICAL";
  status_label: string;
}

export interface HourlyGridPoint {
  timestamp: string;
  grid_import_kw: number;
  grid_export_kw: number;
  import_cost: number;
  export_revenue: number;
  net_cost: number;
  renewable_utilization_pct: number;
}

export interface StrategyMetric {
  strategy_name: string;
  total_grid_import_kwh: number;
  total_grid_export_kwh: number;
  total_cost: number;
  peak_grid_demand_kw: number;
  renewable_utilization_pct: number;
}

export interface StrategyComparison {
  baseline_strategy: StrategyMetric;
  scheduled_strategy: StrategyMetric;
  cost_savings_amount: number;
  cost_savings_pct: number;
  import_reduction_kwh: number;
  status_label: string;
}

export interface GridAnalytics {
  status_label: string;
  total_import_kwh: number;
  total_export_kwh: number;
  total_import_cost: number;
  total_export_revenue: number;
  net_grid_cost: number;
  peak_demand_kw: number;
  average_renewable_utilization_pct: number;
  hourly_series: HourlyGridPoint[];
  strategy_comparison: StrategyComparison;
}

export interface DailyEnergyItem {
  date: string;
  pv_generation_kwh: number;
  load_consumption_kwh: number;
  battery_charge_kwh: number;
  battery_discharge_kwh: number;
  grid_import_kwh: number;
  grid_export_kwh: number;
  net_cost: number;
  renewable_utilization_pct: number;
  peak_demand_kw: number;
}

export interface BatteryCyclingStats {
  equivalent_full_cycles: number;
  total_energy_throughput_kwh: number;
  average_depth_of_discharge_pct: number;
  estimated_soh_pct: number;
}

export interface AnalyticsSummary {
  status_label: string;
  period: string;
  total_pv_kwh: number;
  total_load_kwh: number;
  total_battery_charge_kwh: number;
  total_battery_discharge_kwh: number;
  total_grid_import_kwh: number;
  total_grid_export_kwh: number;
  total_energy_cost: number;
  renewable_utilization_pct: number;
  peak_demand_kw: number;
  battery_stats: BatteryCyclingStats;
  daily_breakdown: DailyEnergyItem[];
}

export interface SystemAlert {
  id: number;
  title: string;
  message: string;
  category: "Battery" | "PV" | "Load" | "Grid" | "System";
  severity: "INFO" | "WARNING" | "CRITICAL";
  is_acknowledged: boolean;
  acknowledged_at?: string | null;
  acknowledged_by?: string | null;
  timestamp: string;
}

export interface PVSettings {
  installed_capacity_kw: number;
  derating_factor: number;
  system_efficiency: number;
  pv_model_identifier: string;
}

export interface BatterySettings {
  capacity_kwh: number;
  initial_soc: number;
  min_soc: number;
  max_soc: number;
  max_charge_kw: number;
  max_discharge_kw: number;
  charge_efficiency: number;
  discharge_efficiency: number;
}

export interface GridSettings {
  import_limit_kw: number;
  export_limit_kw: number;
  import_tariff: number;
  export_tariff: number;
}

export interface ForecastSettings {
  forecast_horizon_hours: number;
  scheduling_horizon_hours: number;
  optimization_interval_minutes: number;
  forecast_update_interval_minutes: number;
}

export interface AllSettings {
  pv: PVSettings;
  battery: BatterySettings;
  grid: GridSettings;
  forecast: ForecastSettings;
}

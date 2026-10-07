export interface Scenario {
  name: string;
  description: string;
  hours: number;
}

export interface ModelParams {
  alpha?: number;
  beta?: number;
  gamma?: number;
  constant?: number;
  delay?: number;
  heater_power_kw?: number;
}

export interface OptimizeRequest {
  scenario: string;
  t_min: number;
  t_max: number;
  t_start: number;
  max_overshoot?: number;
  overrides?: Record<number, 0 | 1>;
  model_params?: ModelParams;
}

export interface HourRow {
  hour: number;
  price_pln_kwh: number;
  outside_temp_c: number;
  solar_radiation_wm2: number;
  optimal_state: number;
  optimal_temp_c: number;
  optimal_cost_pln: number;
  thermostat_state: number;
  thermostat_temp_c: number;
  thermostat_cost_pln: number;
}

export interface PlanSummary {
  cost_pln: number;
  energy_kwh: number;
  heating_hours: number;
  hours_below_t_min: number;
  deficit_kh: number;
  mean_temp_c: number;
}

export interface OptimizeResponse {
  scenario: string;
  hours: number;
  t_min: number;
  t_max: number;
  t_start: number;
  rows: HourRow[];
  optimal: PlanSummary;
  thermostat: PlanSummary;
  saving_pln: number;
  saving_pct: number;
}

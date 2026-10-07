from __future__ import annotations

from dataclasses import replace

from heating_optimizer import (
    ComfortBand,
    HourlyInputs,
    Plan,
    ThermalModel,
    available,
    default_model,
    find_optimal_schedule,
    load_inputs,
    simulate_thermostat,
)

from .schemas import (
    HourRow,
    ModelParams,
    OptimizeRequest,
    OptimizeResponse,
    PlanSummary,
    ScenarioOut,
)


def list_scenarios() -> list[ScenarioOut]:
    return [ScenarioOut(name=s.name, description=s.description, hours=s.hours) for s in available()]


def build_model(overrides: ModelParams) -> ThermalModel:
    changes = {k: v for k, v in overrides.model_dump().items() if v is not None}
    return replace(default_model(), **changes) if changes else default_model()


def summarize(plan: Plan, t_min: float) -> PlanSummary:
    return PlanSummary(
        cost_pln=round(plan.cost, 4),
        energy_kwh=round(plan.energy_kwh, 3),
        heating_hours=plan.heating_hours,
        hours_below_t_min=plan.hours_below(t_min),
        deficit_kh=round(plan.deficit(t_min), 3),
        mean_temp_c=round(plan.mean_temperature, 2),
    )


def build_rows(inputs: HourlyInputs, optimal: Plan, thermostat: Plan) -> list[HourRow]:
    return [
        HourRow(
            hour=hour,
            price_pln_kwh=inputs.prices[hour],
            outside_temp_c=inputs.outside_temperatures[hour],
            solar_radiation_wm2=inputs.solar_radiation[hour],
            optimal_state=optimal.schedule[hour],
            optimal_temp_c=optimal.temperatures[hour],
            optimal_cost_pln=round(optimal.cost_by_hour[hour], 4),
            thermostat_state=thermostat.schedule[hour],
            thermostat_temp_c=thermostat.temperatures[hour],
            thermostat_cost_pln=round(thermostat.cost_by_hour[hour], 4),
        )
        for hour in range(inputs.hours)
    ]


def optimize(request: OptimizeRequest) -> OptimizeResponse:
    model = build_model(request.model_params)
    inputs = load_inputs(request.scenario)
    comfort = ComfortBand(
        t_min=request.t_min, t_max=request.t_max, max_overshoot=request.max_overshoot
    )

    optimal = find_optimal_schedule(
        model, inputs, comfort, t_start=request.t_start, overrides=request.overrides
    )
    thermostat = simulate_thermostat(model, inputs, request.t_min, request.t_max, request.t_start)

    saving = thermostat.cost - optimal.cost
    return OptimizeResponse(
        scenario=request.scenario,
        hours=inputs.hours,
        t_min=request.t_min,
        t_max=request.t_max,
        t_start=request.t_start,
        rows=build_rows(inputs, optimal, thermostat),
        optimal=summarize(optimal, request.t_min),
        thermostat=summarize(thermostat, request.t_min),
        saving_pln=round(saving, 4),
        saving_pct=round(100 * saving / thermostat.cost, 2) if thermostat.cost > 0 else 0.0,
    )

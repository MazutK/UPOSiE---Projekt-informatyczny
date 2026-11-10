from __future__ import annotations

from dataclasses import replace
from datetime import date, datetime, timezone
from pathlib import Path

from heating_optimizer import (
    ComfortBand,
    HourlyInputs,
    Plan,
    ThermalModel,
    available,
    compare_all_methods,
    default_model,
    find_optimal_schedule,
    load_inputs,
    run_sensitivity_analysis,
    simulate_thermostat,
)
from heating_optimizer.data_sources import (
    build_hourly_inputs,
    fetch_open_meteo_day,
    fetch_pse_day,
    load_live_sample,
    save_as_csv,
    save_live_meta,
)
from heating_optimizer.datasets import (
    BUNDLED_DATA_DIR,
    LIVE_SCENARIO,
    live_data_dir,
    read_live_meta,
)

from .schemas import (
    CompareRequest,
    CompareResponse,
    HourRow,
    LiveDayResponse,
    MethodComparisonOut,
    ModelParams,
    OptimizeRequest,
    OptimizeResponse,
    PlanSummary,
    ScenarioOut,
    SensitivityRequest,
    SensitivityResponse,
    SensitivityRowOut,
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


def compare(request: CompareRequest) -> CompareResponse:
    model = build_model(request.model_params)
    inputs = load_inputs(request.scenario)
    comfort = ComfortBand(
        t_min=request.t_min, t_max=request.t_max, max_overshoot=request.max_overshoot
    )

    metrics = compare_all_methods(
        model=model,
        inputs=inputs,
        comfort=comfort,
        t_start=request.t_start,
        overrides=request.overrides,
    )

    methods_out = [
        MethodComparisonOut(
            method=m.method,
            label=m.label,
            description=m.description,
            cost_pln=m.cost_pln,
            energy_kwh=m.energy_kwh,
            heating_hours=m.heating_hours,
            hours_below_t_min=m.hours_below_t_min,
            deficit_kh=m.deficit_kh,
            mean_temp_c=m.mean_temp_c,
            min_temp_c=m.min_temp_c,
            max_temp_c=m.max_temp_c,
            saving_pln=m.saving_pln,
            saving_pct=m.saving_pct,
        )
        for m in metrics
    ]

    return CompareResponse(
        scenario=request.scenario,
        t_min=request.t_min,
        t_max=request.t_max,
        t_start=request.t_start,
        methods=methods_out,
    )


def sensitivity(request: SensitivityRequest) -> SensitivityResponse:
    model = build_model(request.model_params)
    inputs = load_inputs(request.scenario)

    result = run_sensitivity_analysis(
        model=model,
        inputs=inputs,
        parameter=request.parameter,
        values=request.values,
        scenario_name=request.scenario,
        t_min=request.t_min,
        t_max=request.t_max,
        t_start=request.t_start,
        max_overshoot=request.max_overshoot,
        overrides=request.overrides,
    )

    rows_out = [
        SensitivityRowOut(
            value=r.value,
            dp_cost_pln=r.dp_cost_pln,
            thermostat_cost_pln=r.thermostat_cost_pln,
            saving_pln=r.saving_pln,
            saving_pct=r.saving_pct,
            dp_heating_hours=r.dp_heating_hours,
            thermostat_heating_hours=r.thermostat_heating_hours,
            dp_hours_below_t_min=r.dp_hours_below_t_min,
            thermostat_hours_below_t_min=r.thermostat_hours_below_t_min,
            dp_mean_temp_c=r.dp_mean_temp_c,
            dp_max_temp_c=r.dp_max_temp_c,
        )
        for r in result.rows
    ]

    return SensitivityResponse(
        parameter=result.parameter,
        scenario=result.scenario,
        rows=rows_out,
    )


SAMPLE_DATE = "2026-10-13"  # data próbek w data/raw/ (Lab 3)
RAW_DIR = Path(__file__).resolve().parents[4] / "data" / "raw"


def get_live_day(date_str: str | None = None) -> LiveDayResponse:
    """Składa dobę live z PSE + Open-Meteo dla jednej daty (UC-01, krok 2).

    Zasady (P-01, Z-08, Z-09):
    - nigdy nie łączymy pogody z jednej daty i cen z innej — albo pełna doba z obu
      źródeł dla wybranej daty, albo cała próbka offline, albo poprzednia doba;
    - komunikat podaje datę, z której faktycznie są dane;
    - doba i jej metadane są zapisywane atomowo do katalogu live (poza repo).
    """
    date_str = date_str or date.today().isoformat()
    target_csv = live_data_dir() / f"{LIVE_SCENARIO}.csv"
    raw_pse = RAW_DIR / "pse-rce-sample.json"
    raw_weather = RAW_DIR / "open-meteo-sample.json"

    try:
        temps, rads = fetch_open_meteo_day(date_str, timeout=3.0)
        prices = fetch_pse_day(date_str, timeout=3.0)
        inputs = build_hourly_inputs(prices, temps, rads)
        source, data_date = "live_api", date_str
        message = f"Pobrano dane z PSE i Open-Meteo dla daty {date_str}."
    except Exception as live_error:
        reason = type(live_error).__name__
        if raw_pse.is_file() and raw_weather.is_file():
            inputs = load_live_sample(raw_pse, raw_weather)
            source, data_date = "offline_sample", SAMPLE_DATE
            message = (
                f"Nie udało się pobrać pełnej doby {date_str} ({reason}). "
                f"Użyto próbki offline z {SAMPLE_DATE} — wynik NIE dotyczy wybranej daty."
            )
        else:
            previous = next(
                (p for p in (target_csv, BUNDLED_DATA_DIR / f"{LIVE_SCENARIO}.csv") if p.is_file()),
                None,
            )
            if previous is None:
                raise
            meta = read_live_meta(previous) or {}
            known_date = meta.get("data_date")
            return LiveDayResponse(
                date=date_str,
                scenario_name=LIVE_SCENARIO,
                source="cached_bundled",
                hours=24,
                message=(
                    f"Nie udało się pobrać doby {date_str} ({reason}). Zostaje poprzednio "
                    + (f"zapisana doba z {known_date}." if known_date else "zapisana doba o nieznanej dacie.")
                ),
            )

    save_as_csv(inputs, target_csv)
    save_live_meta(
        target_csv,
        {
            "requested_date": date_str,
            "data_date": data_date,
            "source": source,
            "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        },
    )
    return LiveDayResponse(
        date=date_str,
        scenario_name=LIVE_SCENARIO,
        source=source,
        hours=24,
        message=message,
    )

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

# Z-03: NaN/Infinity w żądaniu to błąd walidacji (422), a nie liczba do obliczeń.
FINITE = ConfigDict(allow_inf_nan=False)


class ScenarioOut(BaseModel):
    name: str
    description: str
    hours: int


class ModelParams(BaseModel):
    """Podmiana parametrów budynku (Z-04): tylko wartości fizycznie sensowne.

    alpha — część różnicy temperatur tracona w godzinę (0 < alpha < 1),
    beta — przyrost temperatury od grzałki [°C/h] (> 0),
    gamma — wpływ nasłonecznienia (>= 0).
    """

    model_config = FINITE

    alpha: float | None = Field(default=None, gt=0.0, lt=1.0)
    beta: float | None = Field(default=None, gt=0.0, le=10.0)
    gamma: float | None = Field(default=None, ge=0.0, le=1.0)
    constant: float | None = Field(default=None, ge=-5.0, le=5.0)
    delay: int | None = Field(default=None, ge=0, le=6)
    heater_power_kw: float | None = Field(default=None, gt=0, le=50.0)


class OptimizeRequest(BaseModel):
    model_config = FINITE

    scenario: str = "doba_zmienna_cena"
    t_min: float = Field(default=21.0, ge=5.0, le=30.0)
    t_max: float = Field(default=22.5, ge=5.0, le=30.0)
    t_start: float = Field(default=21.8, ge=0.0, le=35.0)
    max_overshoot: float = Field(default=1.0, ge=0.0, le=5.0)
    overrides: dict[int, int] = Field(default_factory=dict)
    model_params: ModelParams = Field(default_factory=ModelParams)

    @model_validator(mode="after")
    def check_band(self) -> OptimizeRequest:
        if self.t_min > self.t_max:
            raise ValueError("t_min nie może być większe niż t_max")
        if any(state not in (0, 1) for state in self.overrides.values()):
            raise ValueError("wymuszenie musi mieć wartość 0 albo 1")
        return self


class HourRow(BaseModel):
    hour: int
    price_pln_kwh: float
    outside_temp_c: float
    solar_radiation_wm2: float
    optimal_state: int
    optimal_temp_c: float
    optimal_cost_pln: float
    thermostat_state: int
    thermostat_temp_c: float
    thermostat_cost_pln: float


class PlanSummary(BaseModel):
    cost_pln: float
    energy_kwh: float
    heating_hours: int
    hours_below_t_min: int
    deficit_kh: float
    mean_temp_c: float


class OptimizeResponse(BaseModel):
    scenario: str
    hours: int
    t_min: float
    t_max: float
    t_start: float
    rows: list[HourRow]
    optimal: PlanSummary
    thermostat: PlanSummary
    saving_pln: float
    saving_pct: float


class MethodComparisonOut(BaseModel):
    method: str
    label: str
    description: str
    cost_pln: float
    energy_kwh: float
    heating_hours: int
    hours_below_t_min: int
    deficit_kh: float
    mean_temp_c: float
    min_temp_c: float
    max_temp_c: float
    saving_pln: float
    saving_pct: float


class CompareRequest(BaseModel):
    model_config = FINITE

    scenario: str = "doba_zmienna_cena"
    t_min: float = Field(default=21.0, ge=5.0, le=30.0)
    t_max: float = Field(default=22.5, ge=5.0, le=30.0)
    t_start: float = Field(default=21.8, ge=0.0, le=35.0)
    max_overshoot: float = Field(default=1.0, ge=0.0, le=5.0)
    overrides: dict[int, int] = Field(default_factory=dict)
    model_params: ModelParams = Field(default_factory=ModelParams)

    @model_validator(mode="after")
    def check_band(self) -> CompareRequest:
        if self.t_min > self.t_max:
            raise ValueError("t_min nie może być większe niż t_max")
        return self


class CompareResponse(BaseModel):
    scenario: str
    t_min: float
    t_max: float
    t_start: float
    methods: list[MethodComparisonOut]


class SensitivityRowOut(BaseModel):
    value: float
    dp_cost_pln: float
    thermostat_cost_pln: float
    saving_pln: float
    saving_pct: float
    dp_heating_hours: int
    thermostat_heating_hours: int
    dp_hours_below_t_min: int
    thermostat_hours_below_t_min: int
    dp_mean_temp_c: float
    dp_max_temp_c: float


class SensitivityRequest(BaseModel):
    model_config = FINITE

    scenario: str = "doba_zmienna_cena"
    parameter: Literal["t_min", "max_overshoot"] = "t_min"
    values: list[float] | None = None
    t_min: float = Field(default=21.0, ge=5.0, le=30.0)
    t_max: float = Field(default=22.5, ge=5.0, le=30.0)
    t_start: float = Field(default=21.8, ge=0.0, le=35.0)
    max_overshoot: float = Field(default=1.0, ge=0.0, le=5.0)
    overrides: dict[int, int] = Field(default_factory=dict)
    model_params: ModelParams = Field(default_factory=ModelParams)


class SensitivityResponse(BaseModel):
    parameter: str
    scenario: str
    rows: list[SensitivityRowOut]


class LiveDayResponse(BaseModel):
    date: str
    scenario_name: str
    source: str
    hours: int
    message: str

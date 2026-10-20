from __future__ import annotations

from pydantic import BaseModel, Field, model_validator


class ScenarioOut(BaseModel):
    name: str
    description: str
    hours: int


class ModelParams(BaseModel):
    alpha: float | None = None
    beta: float | None = None
    gamma: float | None = None
    constant: float | None = None
    delay: int | None = Field(default=None, ge=0, le=6)
    heater_power_kw: float | None = Field(default=None, gt=0)


class OptimizeRequest(BaseModel):
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

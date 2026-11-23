"""Lab 7: testy logiki silnika (Karol Brzozowski).

Każdy test odpowiada przypadkowi z planu w docs/tests.md, sekcja 2 (ID TC-xx).
Oczekiwane wartości pochodzą ze specyfikacji i ręcznych rachunków, nie z bieżącego
działania kodu:
- docs/architecture.md, UC-01 (warunek rozpoczęcia, błędy, kryterium odbioru),
- docs/experiment.md, p. 3 (reguła termostatu), p. 6-7 (wyniki Lab 4 i ręczne przeliczenie),
- docs/problem.md (wymagania R1-R6),
- docs/PROJEKT.md (równanie modelu) + parametry.json.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from heating_optimizer import (
    ComfortBand,
    HourlyInputs,
    ThermalModel,
    find_optimal_schedule,
    simulate_thermostat,
)
from heating_optimizer.plan import Plan
from heating_optimizer.simulation import thermostat_decision

ROOT = Path(__file__).resolve().parents[1]
DAY_CSV = ROOT / "data" / "processed" / "doba-live.csv"
PARAMS = ROOT / "packages" / "core" / "src" / "heating_optimizer" / "data" / "parametry.json"

# Pasmo z docs/experiment.md p. 3 i kryterium odbioru UC-01.
T_MIN, T_MAX, T_START = 21.0, 22.5, 21.8
HEATER_KW = 1.5


@pytest.fixture(scope="module")
def model() -> ThermalModel:
    return ThermalModel.from_json(PARAMS)


@pytest.fixture(scope="module")
def day() -> HourlyInputs:
    return HourlyInputs.from_csv(DAY_CSV, expected_hours=24)


def dp_plan(model: ThermalModel, inputs: HourlyInputs) -> Plan:
    return find_optimal_schedule(model, inputs, ComfortBand(T_MIN, T_MAX), T_START)


def hand_cost(prices: tuple[float, ...], hours: list[int]) -> float:
    """Koszt = Σ u · 1,5 kW · 1 h · cena (docs/experiment.md p. 7, K3/K4)."""
    return sum(prices[h] for h in hours) * HEATER_KW


# --- TC-01 (R1, R3, R6): poprawne wejście, plan DP -------------------------------------


def test_tc01_dp_plan_for_real_day_matches_lab4(model, day):
    """Doba 2026-10-13: 24 decyzje 0/1, grzanie 0-1 i 10-13, 5,35 zł, 0 h poniżej T_min.

    Podstawa: experiment.md p. 6 (wynik DP) i p. 7 (ręczna suma: 3,5646 zł/kWh · 1,5 = 5,3469 zł).
    """
    plan = dp_plan(model, day)

    assert plan.hours == 24
    assert set(plan.schedule) <= {0, 1}
    heated = [h for h, u in enumerate(plan.schedule) if u == 1]
    assert heated == [0, 1, 10, 11, 12, 13]
    assert plan.energy_kwh == pytest.approx(9.0)
    assert plan.cost == pytest.approx(5.3469, abs=0.0005)
    assert plan.cost == pytest.approx(hand_cost(day.prices, heated), abs=1e-9)
    assert plan.hours_below(T_MIN) == 0


# --- TC-02 (R4, R6): poprawne wejście, termostat i oszczędność --------------------------


def test_tc02_thermostat_baseline_and_saving_match_lab4(model, day):
    """Termostat grzeje 7-16: 11,15 zł, 4 h poniżej T_min; oszczędność DP 5,81 zł (52,1 %).

    Podstawa: experiment.md p. 6-7 (Σ cen 7..16 = 7,4350 zł/kWh · 1,5 = 11,1525 zł;
    11,1525 − 5,3469 = 5,8056 zł; 52,06 %) i kryterium odbioru UC-01 (1).
    """
    thermostat = simulate_thermostat(model, day, T_MIN, T_MAX, T_START)
    optimal = dp_plan(model, day)

    heated = [h for h, u in enumerate(thermostat.schedule) if u == 1]
    assert heated == list(range(7, 17))
    assert thermostat.cost == pytest.approx(11.1525, abs=0.0005)
    assert thermostat.cost == pytest.approx(hand_cost(day.prices, heated), abs=1e-9)
    assert thermostat.hours_below(T_MIN) == 4

    saving = thermostat.cost - optimal.cost
    assert saving == pytest.approx(5.8056, abs=0.001)
    assert saving / thermostat.cost * 100 == pytest.approx(52.06, abs=0.05)


# --- TC-03 (R3): model cieplny, ręczny rachunek -----------------------------------------


def test_tc03_one_model_step_matches_hand_calculation(model):
    """T[t+1] = T − α(T − T_zew) + β·u[t−d] + γ·G + c, zaokrąglenie do 0,01 °C.

    Podstawa: docs/PROJEKT.md (równanie), parametry.json. Ręcznie dla T = 21,8, T_zew = 6,7, G = 0:
    21,8 − 0,0053218 · 15,1 − 0,0520086 = 21,6676 → 21,67 °C (bez grzania),
    21,6676 + 0,2694400 = 21,9370 → 21,94 °C (grzanie działa w tej godzinie).
    """
    assert model.next_temperature(21.8, 0, 6.7, 0.0) == 21.67
    assert model.next_temperature(21.8, 1, 6.7, 0.0) == 21.94


def test_tc03_heating_acts_after_two_hour_delay(model):
    """Opóźnienie d = 2 h: grzałka włączona w godzinie 0 podnosi temperaturę dopiero w godzinie 2.

    Podstawa: parametry.json (DELAY = 2), docs/PROJEKT.md („grzanie z opóźnieniem d”).
    """
    history = model.initial_history()
    effective = []
    for decision in (1, 0, 0):
        acting, history = model.advance(history, decision)
        effective.append(acting)
    assert effective == [0, 0, 1]


# --- TC-04 (R3): wartości graniczne pasma -----------------------------------------------


@pytest.mark.parametrize(
    ("temperature", "previous", "expected"),
    [
        (21.0, 0, 1),  # dokładnie T_min → grzej (T ≤ T_min)
        (22.5, 1, 0),  # dokładnie T_max → wyłącz (T ≥ T_max)
        (21.01, 0, 0),  # wewnątrz pasma → poprzedni stan
        (22.49, 1, 1),  # wewnątrz pasma → poprzedni stan
    ],
)
def test_tc04_thermostat_rule_at_band_edges(temperature, previous, expected):
    """Podstawa: experiment.md p. 3 i p. 5 — T ≤ T_min → 1, T ≥ T_max → 0, inaczej poprzedni stan."""
    assert thermostat_decision(temperature, T_MIN, T_MAX, previous) == expected


def test_tc04_temperature_exactly_t_min_is_not_counted_below():
    """Godzina z T = T_min nie jest „poniżej T_min”, 20,99 °C już jest.

    Podstawa: experiment.md p. 7, K5 (godziny < T_min) i UC-01 (miara „godziny poniżej T_min”).
    """
    plan = Plan(
        schedule=(0, 0, 0),
        temperatures=(21.0, 20.99, 22.5),
        cost_by_hour=(0.0, 0.0, 0.0),
        heater_power_kw=HEATER_KW,
    )
    assert plan.hours_below(T_MIN) == 1
    assert plan.deficit(T_MIN) == pytest.approx(0.01)


def test_tc04_band_with_t_min_equal_t_max_is_accepted_and_inverted_band_rejected():
    """Warunek rozpoczęcia UC-01: T_min ≤ T_max; T_min > T_max → błąd, bez planu.

    Podstawa: architecture.md, UC-01 (warunek rozpoczęcia, kryterium odbioru (2)).
    """
    band = ComfortBand(22.0, 22.0)
    assert band.t_min == band.t_max
    with pytest.raises(ValueError, match="t_min"):
        ComfortBand(22.6, 22.5)


# --- TC-05 (R2): zmiana cen zmienia harmonogram -----------------------------------------


def test_tc05_expensive_hours_change_the_schedule(model, day):
    """Ceny w godzinach 10-13 podniesione do 5 zł/kWh → DP nie grzeje w 10-13, plan inny niż bazowy.

    Podstawa: problem.md R2 („zmiana cen powoduje zmianę harmonogramu”). Tanie godziny nocne
    (0-5, 22-23: 0,50-0,70 zł/kWh) zostają, więc grzanie w 10-13 nie jest potrzebne do komfortu (R3).
    """
    prices = list(day.prices)
    for hour in range(10, 14):
        prices[hour] = 5.0
    changed = HourlyInputs.of(prices, day.outside_temperatures, day.solar_radiation)

    base = dp_plan(model, day)
    plan = dp_plan(model, changed)

    assert plan.schedule != base.schedule
    assert all(plan.schedule[h] == 0 for h in range(10, 14))
    assert plan.hours_below(T_MIN) == 0


# --- TC-06: błędne wejście, doba bez jednej godziny -------------------------------------


def test_tc06_day_without_one_hour_is_rejected(tmp_path):
    """Doba bez godziny 17 → ValueError „brakujące godziny [17]”, a nie plan na 23 h.

    Podstawa: architecture.md, UC-01 (komunikat o brakujących godzinach, kryterium odbioru (3)).
    Test pracuje na kopii w katalogu tymczasowym, nie na data/processed/.
    """
    lines = DAY_CSV.read_text(encoding="utf-8").splitlines()
    broken = tmp_path / "doba-bez-17.csv"
    broken.write_text(
        "\n".join(line for line in lines if not line.startswith("17,")) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match=r"brakujące godziny \[17\]"):
        HourlyInputs.from_csv(broken, expected_hours=24)


def test_tc06_invalid_test_day_is_rejected():
    """data/test/doba-invalid.csv (2 godziny) → błąd „niepełna doba”.

    Podstawa: docs/implementation.md, p. 2 (tabela błędów) i README (Lab 6).
    """
    invalid = ROOT / "data" / "test" / "doba-invalid.csv"
    with pytest.raises(ValueError, match="niepełna doba"):
        HourlyInputs.from_csv(invalid, expected_hours=24)


# --- TC-07: puste wejście ---------------------------------------------------------------


def test_tc07_file_with_header_only_is_rejected(tmp_path):
    """Plik z samym nagłówkiem → ValueError, żadnego planu z kosztem 0 zł.

    Podstawa: architecture.md, UC-01 („bez planu i bez kosztu 0 zł”).
    """
    empty = tmp_path / "pusta-doba.csv"
    shutil.copyfile(DAY_CSV, empty)
    header = empty.read_text(encoding="utf-8").splitlines()[0]
    empty.write_text(header + "\n", encoding="utf-8")

    with pytest.raises(ValueError):
        HourlyInputs.from_csv(empty, expected_hours=24)
    with pytest.raises(ValueError):
        HourlyInputs.from_csv(empty)


def test_tc07_empty_inputs_are_rejected():
    """Puste listy cen i pogody → ValueError. Podstawa: UC-01, warunek rozpoczęcia (24 godziny)."""
    with pytest.raises(ValueError):
        HourlyInputs.of([], [], [])

from __future__ import annotations

import io
import math
from collections.abc import Mapping
from pathlib import Path

from heating_optimizer.inputs import HourlyInputs

EXPECTED_HOURS = tuple(range(24))


def build_hourly_inputs(
    prices: Mapping[int, float],
    temperatures: Mapping[int, float],
    solar_radiation: Mapping[int, float],
) -> HourlyInputs:
    """Łączy 3 słowniki godzinowe (0..23) w jeden spójny obiekt HourlyInputs."""
    for name, m in [
        ("ceny", prices),
        ("temperatury", temperatures),
        ("nasłonecznienie", solar_radiation),
    ]:
        if sorted(m.keys()) != list(EXPECTED_HOURS):
            missing = set(EXPECTED_HOURS) - set(m.keys())
            raise ValueError(f"Brakujące godziny dla {name}: {sorted(missing)}")

    sorted_prices = []
    sorted_temps = []
    sorted_rads = []

    for h in EXPECTED_HOURS:
        p = float(prices[h])
        t = float(temperatures[h])
        r = float(solar_radiation[h])

        if not math.isfinite(p):
            raise ValueError(f"Cena dla godziny {h} jest nieskończona lub NaN: {p}")
        if not math.isfinite(t):
            raise ValueError(f"Temperatura dla godziny {h} jest nieskończona lub NaN: {t}")
        if not math.isfinite(r) or r < 0:
            raise ValueError(f"Nasłonecznienie dla godziny {h} jest nieprawidłowe: {r}")

        sorted_prices.append(p)
        sorted_temps.append(t)
        sorted_rads.append(r)

    return HourlyInputs(
        prices=tuple(sorted_prices),
        outside_temperatures=tuple(sorted_temps),
        solar_radiation=tuple(sorted_rads),
    )


def save_as_csv(inputs: HourlyInputs, target_path: str | Path) -> None:
    """Zapisuje HourlyInputs w formacie CSV akceptowanym przez silnik."""
    path = Path(target_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        f.write("hour,price_pln_kwh,outside_temp_c,solar_radiation_wm2\n")
        for h in range(inputs.hours):
            f.write(
                f"{h},{inputs.prices[h]:.4f},{inputs.outside_temperatures[h]:.2f},{inputs.solar_radiation[h]:.1f}\n"
            )


def format_as_csv_string(inputs: HourlyInputs) -> str:
    """Zwraca zawartość CSV jako string."""
    buf = io.StringIO()
    buf.write("hour,price_pln_kwh,outside_temp_c,solar_radiation_wm2\n")
    for h in range(inputs.hours):
        buf.write(
            f"{h},{inputs.prices[h]:.4f},{inputs.outside_temperatures[h]:.2f},{inputs.solar_radiation[h]:.1f}\n"
        )
    return buf.getvalue()

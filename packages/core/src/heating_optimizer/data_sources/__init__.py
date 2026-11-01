from __future__ import annotations

from pathlib import Path

from heating_optimizer.inputs import HourlyInputs

from .builder import build_hourly_inputs, format_as_csv_string, save_as_csv
from .open_meteo import fetch_open_meteo_day, load_open_meteo_file, parse_open_meteo_payload
from .pse import fetch_pse_day, load_pse_file, parse_pse_payload


def load_live_sample(pse_path: str | Path, weather_path: str | Path) -> HourlyInputs:
    """Wczytuje próbkę z plików JSON i składa ją do HourlyInputs."""
    prices = load_pse_file(pse_path)
    temps, rads = load_open_meteo_file(weather_path)
    return build_hourly_inputs(prices, temps, rads)


def fetch_live_day(
    date_str: str,
    latitude: float = 52.23,
    longitude: float = 21.01,
    timeout: float = 5.0,
) -> HourlyInputs:
    """Pobiera dane z publicznych API (PSE i Open-Meteo) i łączy w HourlyInputs."""
    prices = fetch_pse_day(date_str, timeout=timeout)
    temps, rads = fetch_open_meteo_day(date_str, latitude, longitude, timeout=timeout)
    return build_hourly_inputs(prices, temps, rads)


__all__ = [
    "build_hourly_inputs",
    "fetch_live_day",
    "fetch_open_meteo_day",
    "fetch_pse_day",
    "format_as_csv_string",
    "load_live_sample",
    "load_open_meteo_file",
    "load_pse_file",
    "parse_open_meteo_payload",
    "parse_pse_payload",
    "save_as_csv",
]

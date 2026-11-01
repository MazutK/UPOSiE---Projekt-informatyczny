from __future__ import annotations

import json
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any

OPEN_METEO_ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
OPEN_METEO_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"


def parse_open_meteo_payload(payload: dict[str, Any]) -> tuple[dict[int, float], dict[int, float]]:
    """Przetwarza payload z Open-Meteo do krotki:
    ({godzina: outside_temp_c}, {godzina: solar_radiation_wm2})
    """
    if "hourly" not in payload:
        raise ValueError("Brak klucza 'hourly' w odpowiedzi Open-Meteo")

    hourly = payload["hourly"]
    times = hourly.get("time", [])
    temps = hourly.get("temperature_2m", [])
    rads = hourly.get("shortwave_radiation", [])

    if not (len(times) == len(temps) == len(rads)):
        raise ValueError("Niespójne długości list w odpowiedzi Open-Meteo")

    temps_by_hour: dict[int, float] = {}
    rads_by_hour: dict[int, float] = {}

    for t_str, t_val, r_val in zip(times, temps, rads, strict=False):
        clean_time = t_str.replace("T", " ")
        try:
            dt = datetime.strptime(clean_time[:16], "%Y-%m-%d %H:%M")
        except ValueError as err:
            raise ValueError(f"Nieprawidłowy format czasu w Open-Meteo: {t_str}") from err

        hour = dt.hour
        temp = float(t_val)
        rad = float(r_val)
        if rad < 0:
            raise ValueError(f"Ujemne nasłonecznienie w godzinie {hour}: {rad}")

        temps_by_hour[hour] = round(temp, 2)
        rads_by_hour[hour] = round(rad, 1)

    if len(temps_by_hour) != 24 or len(rads_by_hour) != 24:
        raise ValueError(
            f"Oczekiwano dokładnie 24 unikalnych godzin z Open-Meteo, otrzymano {len(temps_by_hour)}"
        )

    return temps_by_hour, rads_by_hour


def load_open_meteo_file(path: str | Path) -> tuple[dict[int, float], dict[int, float]]:
    path = Path(path)
    content = json.loads(path.read_text(encoding="utf-8"))
    return parse_open_meteo_payload(content)


def fetch_open_meteo_day(
    date_str: str,
    latitude: float = 52.23,
    longitude: float = 21.01,
    timeout: float = 5.0,
) -> tuple[dict[int, float], dict[int, float]]:
    """Pobiera dane pogodowe dla danej daty (YYYY-MM-DD) i współrzędnych (domyślnie Warszawa)."""
    # Sprawdzamy czy data jest w przeszłości (archive) czy dziś/przyszłość (forecast)
    target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    today = datetime.now().date()
    base_url = OPEN_METEO_ARCHIVE_URL if target_date < today else OPEN_METEO_FORECAST_URL

    url = (
        f"{base_url}?latitude={latitude}&longitude={longitude}"
        f"&start_date={date_str}&end_date={date_str}"
        "&hourly=temperature_2m,shortwave_radiation&timezone=auto"
    )
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "OptymalizatorOgrzewania/0.2.0 (student-project)"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return parse_open_meteo_payload(data)

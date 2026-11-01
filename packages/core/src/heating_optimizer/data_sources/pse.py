from __future__ import annotations

import json
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

PSE_API_URL = "https://api.raporty.pse.pl/api/rce-pln"


def parse_pse_payload(payload: Any) -> dict[int, float]:
    """Przetwarza odpowiedź PSE (lub słownik/listę) do słownika {godzina: cena_pln_kwh}.

    PSE zwraca kwadranse z czasem końca (np. 00:15:00).
    Odejmujemy 15 minut, aby uzyskać początek kwadransa i przypisać do odpowiedniej godziny.
    """
    rows = payload.get("value", payload) if isinstance(payload, dict) else payload
    if not isinstance(rows, list) or len(rows) == 0:
        raise ValueError("Nieprawidłowy lub pusty payload PSE")

    hourly_values: dict[int, list[float]] = {h: [] for h in range(24)}

    for row in rows:
        time_str = row.get("dtime") or row.get("udtczas")
        if not time_str:
            continue
        try:
            # Format: 'YYYY-MM-DD HH:MM:SS' lub ISO
            clean_time = time_str.replace("T", " ")
            dt = datetime.strptime(clean_time[:19], "%Y-%m-%d %H:%M:%S")
        except ValueError as err:
            raise ValueError(f"Nieprawidłowy format czasu w PSE: {time_str}") from err

        quarter_start = dt - timedelta(minutes=15)
        hour = quarter_start.hour
        price_mwh = float(row["rce_pln"])
        hourly_values[hour].append(price_mwh)

    result: dict[int, float] = {}
    for hour, prices in hourly_values.items():
        if not prices:
            raise ValueError(f"Brak danych cenowych PSE dla godziny {hour}")
        mean_mwh = sum(prices) / len(prices)
        result[hour] = round(mean_mwh / 1000.0, 4)

    if len(result) != 24:
        raise ValueError(f"Oczekiwano 24 godzin z PSE, otrzymano {len(result)}")

    return result


def load_pse_file(path: str | Path) -> dict[int, float]:
    path = Path(path)
    content = json.loads(path.read_text(encoding="utf-8"))
    return parse_pse_payload(content)


def fetch_pse_day(date_str: str, timeout: float = 5.0) -> dict[int, float]:
    """Pobiera ceny RCE z API PSE dla danej daty (YYYY-MM-DD)."""
    url = f"{PSE_API_URL}?$filter=business_date%20eq%20'{date_str}'"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "OptymalizatorOgrzewania/0.2.0 (student-project)"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return parse_pse_payload(data)

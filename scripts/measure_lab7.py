"""Lab 7: pomiar niefunkcjonalny - czas pełnej analizy UC-01 (Sebastian Król).

Mierzy to, na co czeka użytkownik po zmianie ustawień: wczytanie i walidacja doby z CSV,
plan DP i symulacja termostatu (te same funkcje co CLI i /api/optimize). Walidacja nie jest
wyłączana. Jedno rozgrzewające uruchomienie, potem N powtórzeń, time.perf_counter.

Przypadki:
- doba: data/processed/doba-live.csv (24 h, próbka oceny),
- 10x: ta sama doba powtórzona 10 razy (240 h) - dziesięciokrotnie większa próbka.

Wynik: <out>/timing.csv (każde powtórzenie) i <out>/timing-summary.csv (mediana, min, max).
Skrypt nie nadpisuje istniejących wyników (podaj nowy katalog albo --overwrite).

    python scripts/measure_lab7.py data/processed/doba-live.csv results/lab7
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import platform
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from heating_optimizer import (
    ComfortBand,
    HourlyInputs,
    find_optimal_schedule,
    simulate_thermostat,
)
from heating_optimizer.datasets import default_model

T_MIN, T_MAX, T_START = 21.0, 22.5, 21.8
CRITERION_S = 1.0  # założenie zespołu, uzasadnienie w docs/tests.md, sekcja 3


def full_analysis(path: Path, hours: int) -> tuple[float, float]:
    model = default_model()
    inputs = HourlyInputs.from_csv(path, expected_hours=hours)
    optimal = find_optimal_schedule(model, inputs, ComfortBand(T_MIN, T_MAX), T_START)
    thermostat = simulate_thermostat(model, inputs, T_MIN, T_MAX, T_START)
    return optimal.cost, thermostat.cost


def repeated_day(source: Path, target: Path, times: int) -> None:
    with open(source, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)
    with open(target, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for day in range(times):
            for row in rows:
                writer.writerow({**row, "hour": int(row["hour"]) + 24 * day})


def cpu_name() -> str:
    try:
        for line in Path("/proc/cpuinfo").read_text().splitlines():
            if line.startswith("model name"):
                return line.split(":", 1)[1].strip()
    except OSError:
        pass
    return platform.processor() or platform.machine()


def commit() -> str:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, check=True
        )
        return out.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "nieznany"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("data", type=Path)
    parser.add_argument("out_dir", type=Path)
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args(argv)

    timing_path = args.out_dir / "timing.csv"
    summary_path = args.out_dir / "timing-summary.csv"
    if not args.overwrite and (timing_path.exists() or summary_path.exists()):
        print(f"Błąd: w {args.out_dir} są już wyniki - podaj nowy katalog albo --overwrite")
        return 1
    args.out_dir.mkdir(parents=True, exist_ok=True)

    env = {
        "data_pomiaru": dt.datetime.now().isoformat(timespec="seconds"),
        "commit": commit(),
        "python": platform.python_version(),
        "system": f"{platform.system()} {platform.release()} {platform.machine()}",
        "cpu": cpu_name(),
    }

    rows: list[dict[str, object]] = []
    summary: list[dict[str, object]] = []
    with tempfile.TemporaryDirectory() as tmp:
        big = Path(tmp) / "doba-x10.csv"
        repeated_day(args.data, big, 10)
        cases = [("doba", args.data, 24), ("10x", big, 240)]
        for name, path, hours in cases:
            costs = full_analysis(path, hours)  # rozgrzewka, nie liczona
            times = []
            for rep in range(1, args.repeats + 1):
                start = time.perf_counter()
                full_analysis(path, hours)
                elapsed = time.perf_counter() - start
                times.append(elapsed)
                rows.append(
                    {
                        **env,
                        "przypadek": name,
                        "godzin": hours,
                        "powtorzenie": rep,
                        "czas_s": f"{elapsed:.4f}",
                    }
                )
            med = statistics.median(times)
            summary.append(
                {
                    **env,
                    "przypadek": name,
                    "godzin": hours,
                    "powtorzen": args.repeats,
                    "mediana_s": f"{med:.4f}",
                    "min_s": f"{min(times):.4f}",
                    "max_s": f"{max(times):.4f}",
                    "kryterium_s": CRITERION_S,
                    "kryterium_spelnione": med <= CRITERION_S,
                    "koszt_dp_pln": f"{costs[0]:.4f}",
                    "koszt_termostat_pln": f"{costs[1]:.4f}",
                }
            )
            print(
                f"{name:5s} {hours:4d} h: mediana {med:.4f} s, min {min(times):.4f} s, "
                f"max {max(times):.4f} s (kryterium <= {CRITERION_S} s: "
                f"{'spełnione' if med <= CRITERION_S else 'NIE'})"
            )

    for path, data in ((timing_path, rows), (summary_path, summary)):
        with open(path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(data[0]))
            writer.writeheader()
            writer.writerows(data)
    print(f"Zapisano: {timing_path}, {summary_path}")
    print(f"Środowisko: Python {env['python']}, {env['system']}, {env['cpu']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

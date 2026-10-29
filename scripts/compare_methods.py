"""Lab 4: porownanie termostatu (wariant bazowy) i planu DP na tej samej dobie.

Uruchomienie (z katalogu repozytorium):
    python scripts/compare_methods.py data/processed/doba-live.csv results/lab4
    python scripts/compare_methods.py data/processed/doba-live.csv results/lab4/sensitivity --t-min 21.5

Skrypt nie zmienia silnika. Wola istniejace funkcje z packages/core:
simulate_thermostat (bazowy) i find_optimal_schedule (metoda).
Brak losowania, wiec ziarno nie jest potrzebne.
"""

from __future__ import annotations

import argparse
import csv
import math
import sys
from pathlib import Path

try:
    import heating_optimizer  # noqa: F401
except ImportError:  # gdy nie wykonano pip install -r requirements.txt
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "packages" / "core" / "src"))

from heating_optimizer import (
    ComfortBand,
    HourlyInputs,
    default_model,
    find_optimal_schedule,
    simulate_thermostat,
)

EXPECTED_COLUMNS = ["hour", "price_pln_kwh", "outside_temp_c", "solar_radiation_wm2"]


def check_input(path: Path) -> None:
    with path.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != EXPECTED_COLUMNS:
            raise SystemExit(f"Kolumny {reader.fieldnames} != {EXPECTED_COLUMNS}")
        rows = list(reader)
    hours = [int(row["hour"]) for row in rows]
    if sorted(hours) != list(range(24)):
        raise SystemExit("Wymagane 24 unikalne godziny 0..23")
    for row in rows:
        for column in EXPECTED_COLUMNS[1:]:
            value = float(row[column])
            if not math.isfinite(value):
                raise SystemExit(f"Wartosc nieskonczona lub pusta: {column}, godzina {row['hour']}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Porownanie termostat vs DP (Lab 4)")
    parser.add_argument("input", type=Path, help="CSV doby w formacie silnika")
    parser.add_argument("output", type=Path, help="katalog wynikow")
    parser.add_argument("--t-min", type=float, default=21.0)
    parser.add_argument("--t-max", type=float, default=22.5)
    parser.add_argument("--t-start", type=float, default=21.8)
    parser.add_argument("--max-overshoot", type=float, default=1.0)
    parser.add_argument(
        "--min-saving-pct",
        type=float,
        default=5.0,
        help="kryterium praktyczne: minimalna oszczednosc w %% kosztu termostatu",
    )
    args = parser.parse_args()

    check_input(args.input)
    inputs = HourlyInputs.from_csv(args.input)
    model = default_model()
    comfort = ComfortBand(t_min=args.t_min, t_max=args.t_max, max_overshoot=args.max_overshoot)

    baseline = simulate_thermostat(model, inputs, args.t_min, args.t_max, args.t_start)
    method = find_optimal_schedule(model, inputs, comfort, t_start=args.t_start)

    observations = []
    for hour in range(inputs.hours):
        observations.append(
            {
                "hour": hour,
                "price_pln_kwh": inputs.prices[hour],
                "outside_temp_c": inputs.outside_temperatures[hour],
                "solar_radiation_wm2": inputs.solar_radiation[hour],
                "termostat_u": baseline.schedule[hour],
                "termostat_temp_c": baseline.temperatures[hour],
                "termostat_koszt_pln": round(baseline.cost_by_hour[hour], 4),
                "dp_u": method.schedule[hour],
                "dp_temp_c": method.temperatures[hour],
                "dp_koszt_pln": round(method.cost_by_hour[hour], 4),
            }
        )

    params = (
        f"t_min={args.t_min};t_max={args.t_max};t_start={args.t_start};"
        f"max_overshoot={args.max_overshoot}"
    )
    comparison = []
    for variant, plan in [("termostat", baseline), ("dp", method)]:
        saving = baseline.cost - plan.cost
        saving_pct = 100 * saving / baseline.cost if baseline.cost > 0 else 0.0
        not_colder = plan.hours_below(args.t_min) <= baseline.hours_below(args.t_min)
        comparison.append(
            {
                "wariant": variant,
                "parametry": params,
                "dane": args.input.as_posix(),
                "n_godzin": plan.hours,
                "koszt_pln": round(plan.cost, 4),
                "energia_kwh": round(plan.energy_kwh, 2),
                "godziny_grzania": plan.heating_hours,
                "godziny_ponizej_tmin": plan.hours_below(args.t_min),
                "deficyt_c_h": round(plan.deficit(args.t_min), 3),
                "srednia_temp_c": round(plan.mean_temperature, 3),
                "min_temp_c": min(plan.temperatures),
                "max_temp_c": max(plan.temperatures),
                "oszczednosc_pln": round(saving, 4),
                "oszczednosc_proc": round(saving_pct, 2),
                "kryterium_spelnione": (
                    "-" if variant == "termostat"
                    else str(saving_pct >= args.min_saving_pct and not_colder).lower()
                ),
            }
        )

    if len(observations) != 24 or any(len(p.schedule) != 24 for p in (baseline, method)):
        raise SystemExit("Oba warianty musza obejmowac te same 24 godziny")

    args.output.mkdir(parents=True, exist_ok=True)
    for name, records in [("observations.csv", observations), ("comparison.csv", comparison)]:
        destination = args.output / name
        if destination.resolve() == args.input.resolve():
            raise SystemExit("Wynik nie moze nadpisac pliku wejsciowego")
        with destination.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(records[0]))
            writer.writeheader()
            writer.writerows(records)

    for row in comparison:
        print(
            f"{row['wariant']:10s} koszt={row['koszt_pln']:.2f} zl  "
            f"kWh={row['energia_kwh']:.1f}  ponizej_Tmin={row['godziny_ponizej_tmin']}  "
            f"oszczednosc={row['oszczednosc_proc']:.1f}%"
        )
    print(f"Zapisano: {args.output}")


if __name__ == "__main__":
    main()

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

from .datasets import available, default_model, resolve
from .inputs import HourlyInputs
from .model import ThermalModel
from .optimizer import ComfortBand, find_optimal_schedule
from .plan import Plan
from .simulation import simulate_thermostat

DEFAULT_DATA = "doba_zmienna_cena"


def parse_override(text: str) -> tuple[int, int]:
    try:
        hour, state = text.split("=")
        return int(hour), int(state)
    except ValueError:
        raise argparse.ArgumentTypeError(f"oczekiwano GODZINA=0/1, otrzymano '{text}'") from None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m heating_optimizer",
        description="Wyznacza optymalny plan grzania i porównuje go z termostatem.",
    )
    parser.add_argument(
        "--data",
        default=DEFAULT_DATA,
        help="nazwa scenariusza albo ścieżka do pliku CSV z danymi godzinowymi",
    )
    parser.add_argument("--params", type=Path, help="plik JSON z parametrami modelu")
    parser.add_argument("--list", action="store_true", help="wypisz dostępne scenariusze i zakończ")
    parser.add_argument("--t-min", type=float, default=21.0, help="dolna granica komfortu [°C]")
    parser.add_argument("--t-max", type=float, default=22.5, help="górna granica komfortu [°C]")
    parser.add_argument("--t-start", type=float, default=21.8, help="temperatura początkowa [°C]")
    parser.add_argument(
        "--override",
        type=parse_override,
        action="append",
        default=[],
        metavar="GODZINA=STAN",
        help="wymuszony stan grzania w danej godzinie, np. 6=1 (można powtarzać)",
    )
    parser.add_argument("--out", type=Path, help="zapisz wyniki godzinowe do pliku CSV")
    return parser


def format_table(inputs: HourlyInputs, optimal: Plan, thermostat: Plan) -> str:
    lines = [
        " godz   cena   T_zew |  opt  T_wew |  term  T_wew",
        " ----  -----  ------ | ----  ----- | -----  -----",
    ]
    for hour in range(inputs.hours):
        lines.append(
            f" {hour:4d}  {inputs.prices[hour]:5.2f}  {inputs.outside_temperatures[hour]:6.1f} |"
            f" {optimal.schedule[hour]:4d}  {optimal.temperatures[hour]:5.2f} |"
            f" {thermostat.schedule[hour]:5d}  {thermostat.temperatures[hour]:5.2f}"
        )
    return "\n".join(lines)


def format_summary(optimal: Plan, thermostat: Plan, t_min: float) -> str:
    rows = [
        ("Koszt energii [zł]", f"{optimal.cost:.2f}", f"{thermostat.cost:.2f}"),
        ("Energia [kWh]", f"{optimal.energy_kwh:.1f}", f"{thermostat.energy_kwh:.1f}"),
        ("Godziny grzania", str(optimal.heating_hours), str(thermostat.heating_hours)),
        (
            "Godziny poniżej T_min",
            str(optimal.hours_below(t_min)),
            str(thermostat.hours_below(t_min)),
        ),
        (
            "Średnia temperatura [°C]",
            f"{optimal.mean_temperature:.2f}",
            f"{thermostat.mean_temperature:.2f}",
        ),
    ]
    lines = [f" {'':26s} {'optymalizator':>13s} {'termostat':>10s}"]
    lines += [f" {label:26s} {a:>13s} {b:>10s}" for label, a, b in rows]
    saving = thermostat.cost - optimal.cost
    if thermostat.cost > 0:
        lines.append(f"\n Oszczędność: {saving:.2f} zł ({100 * saving / thermostat.cost:.1f}%)")
    else:
        lines.append(f"\n Oszczędność: {saving:.2f} zł")
    return "\n".join(lines)


def write_csv(path: Path, inputs: HourlyInputs, optimal: Plan, thermostat: Plan) -> None:
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "hour",
                "price_pln_kwh",
                "outside_temp_c",
                "solar_radiation_wm2",
                "optimal_state",
                "optimal_temp_c",
                "thermostat_state",
                "thermostat_temp_c",
            ]
        )
        for hour in range(inputs.hours):
            writer.writerow(
                [
                    hour,
                    inputs.prices[hour],
                    inputs.outside_temperatures[hour],
                    inputs.solar_radiation[hour],
                    optimal.schedule[hour],
                    optimal.temperatures[hour],
                    thermostat.schedule[hour],
                    thermostat.temperatures[hour],
                ]
            )


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.list:
        for scenario in available():
            print(f" {scenario.name:24s} {scenario.hours:3d} h  {scenario.description}")
        return 0
    try:
        model = default_model() if args.params is None else ThermalModel.from_json(args.params)
        data_path = resolve(args.data)
        inputs = HourlyInputs.from_csv(data_path)
        comfort = ComfortBand(t_min=args.t_min, t_max=args.t_max)
        optimal = find_optimal_schedule(
            model, inputs, comfort, t_start=args.t_start, overrides=dict(args.override)
        )
    except (OSError, ValueError, KeyError) as e:
        print(f"Błąd: {e}", file=sys.stderr)
        return 1
    thermostat = simulate_thermostat(model, inputs, args.t_min, args.t_max, args.t_start)

    print(f" Dane: {data_path.name} ({inputs.hours} h)")
    print(f" Komfort: {args.t_min:.1f}-{args.t_max:.1f} °C, start: {args.t_start:.1f} °C\n")
    print(format_table(inputs, optimal, thermostat))
    print()
    print(format_summary(optimal, thermostat, args.t_min))

    if args.out:
        write_csv(args.out, inputs, optimal, thermostat)
        print(f"\n Zapisano: {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

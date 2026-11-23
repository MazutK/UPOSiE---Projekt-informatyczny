"""Lab 7: porównanie jakości po integracji z wynikiem eksperymentu Lab 4 (Sebastian Rączka).

Dla każdego przypadku z Lab 4 wykonuje pełną operację przez interfejs projektu
(`python -m heating_optimizer ... --out`), czyta plik wyniku i liczy od nowa miary z Lab 4
(koszt, energia, godziny grzania, godziny < T_min, deficyt, temperatury, oszczędność).
Godziny dopasowuje po kolumnie `hour` (nie po pozycji wiersza) do results/lab4/.../observations.csv
i liczy MAE temperatury oraz liczbę różnych decyzji. Porównanie z comparison.csv z tolerancją.

    python scripts/compare_lab7.py results/lab7
"""

from __future__ import annotations

import argparse
import csv
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed" / "doba-live.csv"
HEATER_KW = 1.5

# Uzgodniona tolerancja (docs/tests.md, sekcja 4).
TOLERANCE = {
    "koszt_pln": 0.01,
    "energia_kwh": 0.0,
    "godziny_grzania": 0,
    "godziny_ponizej_tmin": 0,
    "deficyt_c_h": 0.01,
    "srednia_temp_c": 0.01,
    "min_temp_c": 0.01,
    "max_temp_c": 0.01,
    "oszczednosc_pln": 0.01,
    "oszczednosc_proc": 0.1,
}

CASES = [
    ("bazowy", ["--t-min", "21.0", "--t-max", "22.5", "--t-start", "21.8"], 21.0, "results/lab4"),
    (
        "wrazliwosc",
        ["--t-min", "21.5", "--t-max", "22.5", "--t-start", "21.8"],
        21.5,
        "results/lab4/sensitivity",
    ),
]
VARIANTS = {"termostat": "thermostat", "dp": "optimal"}


def run_cli(args: list[str], out: Path) -> None:
    env = dict(os.environ)
    env["PYTHONPATH"] = (
        str(ROOT / "packages" / "core" / "src") + os.pathsep + env.get("PYTHONPATH", "")
    )
    env["PYTHONIOENCODING"] = "utf-8"
    subprocess.run(
        [sys.executable, "-m", "heating_optimizer", "--data", str(DATA), "--out", str(out), *args],
        check=True,
        capture_output=True,
        env=env,
    )


def read_csv(path: Path) -> list[dict[str, str]]:
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def metrics(rows: list[dict[str, str]], prefix: str, t_min: float) -> dict[str, float]:
    states = [int(r[f"{prefix}_state"]) for r in rows]
    temps = [float(r[f"{prefix}_temp_c"]) for r in rows]
    prices = [float(r["price_pln_kwh"]) for r in rows]
    return {
        "koszt_pln": sum(u * HEATER_KW * p for u, p in zip(states, prices, strict=True)),
        "energia_kwh": sum(states) * HEATER_KW,
        "godziny_grzania": sum(states),
        "godziny_ponizej_tmin": sum(1 for t in temps if t < t_min),
        "deficyt_c_h": sum(max(0.0, t_min - t) for t in temps),
        "srednia_temp_c": sum(temps) / len(temps),
        "min_temp_c": min(temps),
        "max_temp_c": max(temps),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("out_dir", type=Path)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args(argv)
    quality_path = args.out_dir / "quality.csv"
    hourly_path = args.out_dir / "quality-hourly.csv"
    if not args.overwrite and (quality_path.exists() or hourly_path.exists()):
        print(f"Błąd: w {args.out_dir} są już wyniki - podaj nowy katalog albo --overwrite")
        return 1
    args.out_dir.mkdir(parents=True, exist_ok=True)

    quality: list[dict[str, object]] = []
    hourly: list[dict[str, object]] = []
    with tempfile.TemporaryDirectory() as tmp:
        for case, cli_args, t_min, lab4_dir in CASES:
            out = Path(tmp) / f"{case}.csv"
            run_cli(cli_args, out)
            rows = read_csv(out)
            lab4_obs = {int(r["hour"]): r for r in read_csv(ROOT / lab4_dir / "observations.csv")}
            lab4_cmp = {r["wariant"]: r for r in read_csv(ROOT / lab4_dir / "comparison.csv")}

            got = {name: metrics(rows, prefix, t_min) for name, prefix in VARIANTS.items()}
            base_cost = got["termostat"]["koszt_pln"]
            for name in VARIANTS:
                saving = base_cost - got[name]["koszt_pln"]
                got[name]["oszczednosc_pln"] = saving
                got[name]["oszczednosc_proc"] = 100 * saving / base_cost if base_cost else 0.0

            for name, prefix in VARIANTS.items():
                for measure, tol in TOLERANCE.items():
                    expected = float(lab4_cmp[name][measure])
                    value = got[name][measure]
                    diff = value - expected
                    quality.append(
                        {
                            "przypadek": case,
                            "wariant": name,
                            "miara": measure,
                            "lab4": f"{expected:.4f}",
                            "lab7": f"{value:.4f}",
                            "roznica": f"{diff:+.4f}",
                            "tolerancja": tol,
                            "zgodne": abs(diff) <= tol + 1e-9,
                        }
                    )
                # Dopasowanie po godzinie, nie po pozycji.
                errors, mismatched = [], 0
                for r in rows:
                    ref = lab4_obs[int(r["hour"])]
                    errors.append(abs(float(r[f"{prefix}_temp_c"]) - float(ref[f"{name}_temp_c"])))
                    mismatched += int(r[f"{prefix}_state"]) != int(ref[f"{name}_u"])
                hourly.append(
                    {
                        "przypadek": case,
                        "wariant": name,
                        "godzin": len(rows),
                        "mae_temp_c": f"{sum(errors) / len(errors):.4f}",
                        "max_blad_temp_c": f"{max(errors):.4f}",
                        "rozne_decyzje": mismatched,
                    }
                )

    for path, data in ((quality_path, quality), (hourly_path, hourly)):
        with open(path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(data[0]))
            writer.writeheader()
            writer.writerows(data)

    bad = [q for q in quality if not q["zgodne"]]
    for h in hourly:
        print(
            f"{h['przypadek']:10s} {h['wariant']:9s} MAE temp {h['mae_temp_c']} °C, "
            f"różne decyzje: {h['rozne_decyzje']}/{h['godzin']}"
        )
    print(f"Miary zgodne z Lab 4: {len(quality) - len(bad)}/{len(quality)}")
    for q in bad:
        print(
            f"  NIEZGODNE: {q['przypadek']} {q['wariant']} {q['miara']}: {q['lab4']} -> {q['lab7']}"
        )
    print(f"Zapisano: {quality_path}, {hourly_path}")
    return 0 if not bad else 2


if __name__ == "__main__":
    sys.exit(main())

"""Lab 4: niezalezna kontrola obliczen porownania termostat vs DP.

Uruchomienie (z katalogu repozytorium):
    python scripts/check_lab4.py results/lab4
    python scripts/check_lab4.py results/lab4/sensitivity

Skrypt NIE importuje silnika ani pandas - liczy wszystko od nowa z plikow
observations.csv i comparison.csv (biblioteka standardowa), zeby nie powtarzac
ewentualnego bledu z scripts/compare_methods.py.

Kontrole:
    K1  struktura: kolumny, 24 unikalne godziny 0..23, warianty termostat + dp, n_godzin = 24
    K2  decyzje u w {0, 1}; godziny_grzania = suma u; energia_kwh = suma u * moc grzalki
    K3  koszt godzinowy = u * moc [kW] * 1 h * cena [zl/kWh] (oba warianty)
    K4  suma kosztow godzinowych = koszt_pln w comparison.csv (oba warianty)
    K5  komfort z kolumny temperatur: godziny < T_min, deficyt, srednia / min / max T
    K6  oszczednosc zl i %, kryterium (>= prog % i nie wiecej godzin < T_min)
    K7  te same dane wejsciowe: cena i pogoda zgodne z plikiem z kolumny `dane`,
        a MD5 tego pliku (konce linii LF) = `dane_md5` (Lab 6, Z-06)
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PARAMS = REPO / "packages" / "core" / "src" / "heating_optimizer" / "data" / "parametry.json"

OBS_COLUMNS = [
    "hour", "price_pln_kwh", "outside_temp_c", "solar_radiation_wm2",
    "termostat_u", "termostat_temp_c", "termostat_koszt_pln",
    "dp_u", "dp_temp_c", "dp_koszt_pln",
]
CMP_COLUMNS = [
    "wariant", "parametry", "dane", "n_godzin", "koszt_pln", "energia_kwh",
    "godziny_grzania", "godziny_ponizej_tmin", "deficyt_c_h", "srednia_temp_c",
    "min_temp_c", "max_temp_c", "oszczednosc_pln", "oszczednosc_proc", "kryterium_spelnione",
    "dane_md5", "data_uruchomienia",
]
VARIANTS = ("termostat", "dp")

TOL_HOUR = 0.0001   # koszt godzinowy zapisany z 4 miejscami po przecinku
TOL_SUM = 0.002     # suma 24 zaokraglonych kosztow vs koszt z pelna precyzja
TOL_TEMP = 0.01     # temperatury zapisane z 2 miejscami po przecinku


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        return list(reader.fieldnames or []), list(reader)


def parse_params(text: str) -> dict[str, float]:
    return {key: float(value) for key, value in (item.split("=") for item in text.split(";"))}


def check(folder: Path, power_kw: float, min_saving_pct: float) -> list[str]:
    errors: dict[str, list[str]] = {f"K{i}": [] for i in range(1, 8)}

    # K1 - struktura
    obs_cols, obs = read_csv(folder / "observations.csv")
    cmp_cols, cmp_rows = read_csv(folder / "comparison.csv")
    if obs_cols != OBS_COLUMNS:
        errors["K1"].append(f"observations.csv: kolumny {obs_cols}")
    if cmp_cols != CMP_COLUMNS:
        errors["K1"].append(f"comparison.csv: kolumny {cmp_cols}")
    if errors["K1"]:
        return [f"{k}: {m}" for k, msgs in errors.items() for m in msgs]
    hours = [int(row["hour"]) for row in obs]
    if hours != list(range(24)):
        errors["K1"].append(f"godziny {hours} != 0..23 (kolejno, bez powtorzen)")
    cmp = {row["wariant"]: row for row in cmp_rows}
    if sorted(cmp) != sorted(VARIANTS) or len(cmp_rows) != 2:
        errors["K1"].append(f"warianty {[r['wariant'] for r in cmp_rows]} != {list(VARIANTS)}")
        return [f"{k}: {m}" for k, msgs in errors.items() for m in msgs]
    for name in VARIANTS:
        if int(cmp[name]["n_godzin"]) != 24:
            errors["K1"].append(f"{name}: n_godzin = {cmp[name]['n_godzin']}")
    if any(cmp["termostat"][c] != cmp["dp"][c] for c in ("parametry", "dane", "dane_md5", "data_uruchomienia")):
        errors["K1"].append("warianty maja rozne parametry albo dane")

    params = parse_params(cmp["dp"]["parametry"])
    t_min = params["t_min"]

    for name in VARIANTS:
        row = cmp[name]
        u = [int(float(r[f"{name}_u"])) for r in obs]
        temps = [float(r[f"{name}_temp_c"]) for r in obs]
        prices = [float(r["price_pln_kwh"]) for r in obs]
        costs = [float(r[f"{name}_koszt_pln"]) for r in obs]

        # K2 - decyzje i energia
        if any(x not in (0, 1) for x in u):
            errors["K2"].append(f"{name}: decyzje spoza {{0, 1}}")
        if sum(u) != int(row["godziny_grzania"]):
            errors["K2"].append(f"{name}: suma u = {sum(u)} != godziny_grzania {row['godziny_grzania']}")
        energy = sum(u) * power_kw
        if abs(energy - float(row["energia_kwh"])) > 0.01:
            errors["K2"].append(f"{name}: energia {energy:.2f} kWh != {row['energia_kwh']}")

        # K3 - koszt kazdej godziny
        for hour, (ui, price, cost) in enumerate(zip(u, prices, costs)):
            expected = ui * power_kw * price
            if abs(expected - cost) > TOL_HOUR:
                errors["K3"].append(
                    f"{name}, godz. {hour}: {ui} * {power_kw} * {price} = {expected:.4f} zl, w pliku {cost}"
                )

        # K4 - suma kosztow
        total = sum(costs)
        if abs(total - float(row["koszt_pln"])) > TOL_SUM:
            errors["K4"].append(f"{name}: suma godzin {total:.4f} zl != koszt_pln {row['koszt_pln']}")

        # K5 - komfort liczony z temperatur
        below = sum(1 for t in temps if t < t_min)
        deficit = sum(max(0.0, t_min - t) for t in temps)
        if below != int(row["godziny_ponizej_tmin"]):
            errors["K5"].append(f"{name}: godziny < T_min = {below} != {row['godziny_ponizej_tmin']}")
        if abs(deficit - float(row["deficyt_c_h"])) > TOL_TEMP * 24:
            errors["K5"].append(f"{name}: deficyt {deficit:.3f} != {row['deficyt_c_h']}")
        for label, value in (
            ("srednia_temp_c", sum(temps) / len(temps)),
            ("min_temp_c", min(temps)),
            ("max_temp_c", max(temps)),
        ):
            if abs(value - float(row[label])) > TOL_TEMP:
                errors["K5"].append(f"{name}: {label} {value:.3f} != {row[label]}")

    # K6 - oszczednosc i kryterium
    cost_t = float(cmp["termostat"]["koszt_pln"])
    cost_dp = float(cmp["dp"]["koszt_pln"])
    saving = cost_t - cost_dp
    saving_pct = 100 * saving / cost_t if cost_t > 0 else 0.0
    if abs(saving - float(cmp["dp"]["oszczednosc_pln"])) > TOL_SUM:
        errors["K6"].append(f"oszczednosc {saving:.4f} zl != {cmp['dp']['oszczednosc_pln']}")
    if abs(saving_pct - float(cmp["dp"]["oszczednosc_proc"])) > 0.01:
        errors["K6"].append(f"oszczednosc {saving_pct:.2f} % != {cmp['dp']['oszczednosc_proc']}")
    if float(cmp["termostat"]["oszczednosc_pln"]) != 0.0:
        errors["K6"].append("termostat (baza) musi miec oszczednosc 0")
    not_colder = int(cmp["dp"]["godziny_ponizej_tmin"]) <= int(cmp["termostat"]["godziny_ponizej_tmin"])
    expected_flag = str(saving_pct >= min_saving_pct and not_colder).lower()
    if cmp["dp"]["kryterium_spelnione"] != expected_flag:
        errors["K6"].append(f"kryterium_spelnione = {cmp['dp']['kryterium_spelnione']}, powinno {expected_flag}")

    # K7 - te same dane wejsciowe co plik zrodlowy
    source = Path(cmp["dp"]["dane"])
    if not source.is_absolute():
        source = REPO / source
    if not source.exists():
        errors["K7"].append(f"brak pliku danych {source}")
    else:
        md5 = hashlib.md5(source.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
        if md5 != cmp["dp"]["dane_md5"]:
            errors["K7"].append(f"MD5 {source.name} = {md5} != dane_md5 {cmp['dp']['dane_md5']}")
        _, src_rows = read_csv(source)
        src = {int(r["hour"]): r for r in src_rows}
        for r in obs:
            s = src.get(int(r["hour"]))
            if s is None:
                errors["K7"].append(f"godz. {r['hour']}: brak w {source.name}")
                continue
            for col in ("price_pln_kwh", "outside_temp_c", "solar_radiation_wm2"):
                if abs(float(s[col]) - float(r[col])) > 1e-9:
                    errors["K7"].append(f"godz. {r['hour']}: {col} {r[col]} != {s[col]} w {source.name}")

    return [f"{k}: {m}" for k, msgs in errors.items() for m in msgs]


def main() -> None:
    parser = argparse.ArgumentParser(description="Niezalezna kontrola wynikow Lab 4 (K1-K7)")
    parser.add_argument("folder", type=Path, help="katalog z observations.csv i comparison.csv")
    parser.add_argument("--moc-kw", type=float, default=None, help="moc grzalki; domyslnie z parametry.json")
    parser.add_argument("--min-saving-pct", type=float, default=5.0)
    args = parser.parse_args()

    power = args.moc_kw
    if power is None:
        power = float(json.loads(PARAMS.read_text(encoding="utf-8"))["HEMS_HEATER_POWER_KW"])

    errors = check(args.folder, power, args.min_saving_pct)
    print(f"Katalog: {args.folder}")
    print(f"Moc grzalki: {power} kW")
    if errors:
        failed = sorted({e.split(":")[0] for e in errors}, key=lambda k: int(k[1:]))
        raise SystemExit(
            f"Kontrola niezaliczona ({', '.join(failed)}):\n- " + "\n- ".join(errors)
        )
    print("Kontrola OK (K1-K7)")


if __name__ == "__main__":
    main()

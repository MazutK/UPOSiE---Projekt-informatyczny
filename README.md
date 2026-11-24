# Optymalizator ogrzewania

Najtańszy plan grzania przy zmiennych cenach energii, porównany z termostatem.

Opis projektu, jak działa silnik i podział pracy zespołu: [`docs/PROJEKT.md`](docs/PROJEKT.md).

**Prezentowana wersja: `v1.0.0`** (tag w repozytorium; odtworzenie: `git clone --branch v1.0.0 …`).

## Dokumentacja

- [Raport końcowy](docs/report.md)
- [Instrukcja użytkownika](docs/user-guide.md)
- [Testy i ocena](docs/tests.md)
- [Scenariusz prezentacji i demo](docs/presentation.md)
- [Slajdy (PDF)](presentation/slides.pdf)
- [Opis problemu](docs/problem.md) · [Dane](docs/data.md) · [Eksperyment (Lab 4)](docs/experiment.md) ·
  [Architektura (Lab 5)](docs/architecture.md) · [Realizacja MVP (Lab 6)](docs/implementation.md)

## Instalacja

Jeden blok dla całego projektu - sekcje labów niżej korzystają z tego samego środowiska.
Potrzebne: Python 3.10+, a do GUI bez Dockera także Node 20+.

```bash
python -m venv .venv
```

Aktywacja `.venv` (w każdym nowym terminalu, w którym uruchamiasz Pythona):

| Terminal | Polecenie |
|---|---|
| Windows PowerShell | `.\.venv\Scripts\Activate.ps1` |
| Windows cmd | `.venv\Scripts\activate.bat` |
| Git Bash | `source .venv/Scripts/activate` |
| Linux / macOS | `source .venv/bin/activate` |

```bash
python -m pip install -r requirements.txt -r requirements-dev.txt
python -m pytest                     # sprawdzenie instalacji: wszystkie testy przechodzą
```

`requirements.txt` to zależności programu, `requirements-dev.txt` - testy i API; potrzebne są oba.

## Uruchomienie

**Docker (całość jednym poleceniem)** - potrzebny [Docker Desktop](https://www.docker.com/products/docker-desktop/):

```bash
docker compose up --build
```

Aplikacja: [http://localhost:8080](http://localhost:8080). Zatrzymanie: `Ctrl+C`, potem `docker compose down`.

**Bez Dockera (praca nad kodem)** - po [instalacji](#instalacja), jednorazowo `npm install`, potem **dwa terminale**
(oba polecenia działają, dopóki ich nie zatrzymasz `Ctrl+C`):

| Terminal | Polecenie | Uwagi |
|---|---|---|
| 1 - API | `npm run api` | wcześniej aktywuj `.venv` (uvicorn jest zainstalowany w `.venv`); API na porcie 8000 |
| 2 - GUI | `npm run dev` | GUI: [http://localhost:5173](http://localhost:5173) |

**Wiersz poleceń (bez GUI):** `python -m heating_optimizer --data data/processed/doba-live.csv --out wyniki/plan.csv`
- szczegóły w [instrukcji użytkownika](docs/user-guide.md).


## Nasz zespół

| Imię | Nazwisko |
|------|----------|
| Kacper | Mazur 6️⃣7️⃣|
| Sebastian | Król|
| Sebastian | Rączka|
| Karol | Brzozowski|
| Oskar | Wysocki|
| Patryk | Uchman|

## Przetwarzanie danych (Lab 3)
Surowa próbka: `data/raw/`. Wynik: `data/processed/doba-live.csv`.
Kolekcja żądań do źródeł: `api/` (to nie jest backend; backend jest w `apps/api`).
Słownik: [`docs/data-dictionary.md`](docs/data-dictionary.md).
Kroki i kontrole: [`docs/processing.md`](docs/processing.md).
Środowisko: [Instalacja](#instalacja).
```bash
python scripts/prepare_data.py data/raw/pse-rce-sample.json data/raw/open-meteo-sample.json data/processed/doba-live.csv
python scripts/check_data.py data/processed/doba-live.csv
```
## Porównanie metod (Lab 4)
Pytanie, źródła, warunki, wyniki i ograniczenia: [`docs/experiment.md`](docs/experiment.md).
Wariant bazowy = termostat, metoda = plan DP. Te same dane: `data/processed/doba-live.csv` (Lab 3).
Brak nowych pakietów, brak losowania (ziarno niepotrzebne). Środowisko: [Instalacja](#instalacja).

```bash
python -c "import sys; print(sys.executable)"   # ma wskazywać .venv

# 1) dane z Lab 3 (plik jest w repo; to polecenie go odtwarza)
python scripts/prepare_data.py data/raw/pse-rce-sample.json data/raw/open-meteo-sample.json data/processed/doba-live.csv
python scripts/check_data.py data/processed/doba-live.csv

# 2) porównanie podstawowe (T_min 21.0, T_max 22.5, start 21.8, max_overshoot 1.0)
python scripts/compare_methods.py data/processed/doba-live.csv results/lab4

# 3) próba wrażliwości (T_min 21.5)
python scripts/compare_methods.py data/processed/doba-live.csv results/lab4/sensitivity --t-min 21.5

# 4) kontrola obliczeń
python scripts/check_lab4.py results/lab4
python scripts/check_lab4.py results/lab4/sensitivity
```

Oczekiwane: termostat 11,15 zł / 4 h poniżej T_min, DP 5,35 zł / 0 h (−52,1 %);
wrażliwość: 11,39 zł vs 7,28 zł (−36,1 %).
Od Lab 6 skrypt odmawia zapisu do katalogu, w którym są już wyniki — ponowne uruchomienie do
`results/lab4` wymaga `--overwrite` (zmieni się tylko kolumna `data_uruchomienia`), lepiej podać nowy katalog.

Demo z instrukcji (opcjonalnie): `python examples/lab4/compare_forecasts.py examples/lab4/data/popyt.csv examples/lab4/results/okno3 --window 3`

## Projekt architektury (Lab 5)
Granice, UC-01, kontrakt, model danych, diagramy i przegląd: [`docs/architecture.md`](docs/architecture.md).
Decyzja o zapisie: [`docs/decisions/001-storage.md`](docs/decisions/001-storage.md). Diagramy: `docs/diagrams/`.

## Realizacja MVP (Lab 6)
Stan, podział prac, ograniczenia i ocena usprawnienia: [`docs/implementation.md`](docs/implementation.md).

**Instalacja:** [wspólny blok na górze](#instalacja).

**Główny przepływ (UC-01) — jedno polecenie:**

```bash
python -m heating_optimizer --data data/processed/doba-live.csv --out wyniki/plan-2026-10-13.csv
```

- Wejście: CSV doby `hour,price_pln_kwh,outside_temp_c,solar_radiation_wm2`, dokładnie 24 godziny 0..23
  (`data/processed/doba-live.csv` z Lab 3 jest w repo). Pasmo: `--t-min 21.0 --t-max 22.5 --t-start 21.8` (domyślne).
- Oczekiwane: optymalizator 5,35 zł / 0 h poniżej T_min, termostat 11,15 zł / 4 h, oszczędność 5,81 zł (52,1 %);
  plik `wyniki/plan-2026-10-13.csv` (24 godziny, `wyniki/` jest w `.gitignore`).
- Błędy: niepełna doba (`data/test/doba-invalid.csv`) → komunikat i kod 1 bez pliku wyniku;
  istniejący plik `--out` nie jest nadpisywany.

Ten sam przepływ w GUI: patrz [Uruchomienie](#uruchomienie) (Docker albo dwa terminale).

**Konfiguracja:** zmienne opcjonalne opisane w [`.env.example`](.env.example) (`HEMS_DATA_DIR`,
`HEMS_LIVE_DIR`, `HEMS_CORS_ORIGINS`) — bez sekretów. Doba pobrana w GUI („Dane publiczne”) trafia do
`data-local/` (poza gitem) razem z `doba_live.meta.json` (data i źródło danych).

**Kontrola:** `python -m pytest` (wszystkie testy), `python scripts/check_lab4.py results/lab4`.

Ćwiczenia z instrukcji (osobno od kodu projektu): `python examples/lab6/forecast.py examples/lab6/history.json examples/lab6/results/run-02.json --window 3`
→ `Prognoza: 14.00 zgloszenia/dzien`; opcjonalnie API: `python -m uvicorn examples.lab6.server:app --port 8001`.

## Testy i CI (Lab 7)
Instrukcja użycia, interpretacja wyniku i komunikaty błędów: [`docs/user-guide.md`](docs/user-guide.md).
Plan testów, wyniki i statusy wymagań: [`docs/tests.md`](docs/tests.md).

**Uruchomienie testów** (środowisko: [Instalacja](#instalacja)):

```bash
python -m pytest -v                                    # wszystkie testy
python -m pytest -v --junitxml=reports/pytest.xml      # z raportem (tak jak w CI)
```

Testy są w `tests/` (testy logiki i integracyjny z Lab 7), `packages/core/tests` i `apps/api/tests`.
Katalog `reports/` jest w `.gitignore`.

**CI:** [`.github/workflows/check.yml`](.github/workflows/check.yml) uruchamia testy przy każdym `push`
i `pull_request` (Python 3.10, Ubuntu). Raport `test-report` (`pytest.xml`, `pytest.txt`) jest zapisywany
jako artefakt także wtedy, gdy testy nie przejdą; pobiera się go ze strony przebiegu w zakładce **Actions**.
Jeśli GitHub Actions nie działa, to samo sprawdzenie wykonuje lokalnie
`python -m pytest -v --junitxml=reports/pytest.xml`.

# Realizacja głównego przepływu (MVP)

_Lab 6. Integracja i weryfikacja: Sebastian Król. Stan na gałąź `feature/lab6-integracja` (2026-11-10)._

Główny przepływ = **UC-01**: dla doby (ceny + pogoda) i pasma komfortu wyznaczyć najtańszy plan
grzania na 24 h i porównać go z termostatem. Działa w dwóch interfejsach, które wołają te same
funkcje silnika: CLI (`python -m heating_optimizer`) i GUI → `POST /api/optimize`.

## 1. Zakres i powiązana dokumentacja

- Architektura, UC-01, kontrakt API, model danych, lista zmian Z-01…Z-10: [`architecture.md`](architecture.md)
- Dane wejściowe i słownik pól: [`data.md`](data.md), [`data-dictionary.md`](data-dictionary.md), [`processing.md`](processing.md)
- Porównanie metod (termostat vs DP) i wyniki referencyjne: [`experiment.md`](experiment.md)
- Decyzja o zapisie (pliki zamiast bazy): [`decisions/001-storage.md`](decisions/001-storage.md)

Co już było przed Lab 6 (nie robiliśmy tego od nowa): silnik (model cieplny, DP, termostat),
API (`/api/optimize`, `/api/compare`, `/api/sensitivity`, `/api/live`), GUI (panel, wykresy,
tabela, porównanie metod, wrażliwość, wymuszenia, dane live, eksport CSV), Docker, skrypty Lab 3–4
z kontrolami, testy `pytest`. Lab 6 zamyka luki wykryte w przeglądzie Lab 5 (§2.4, §3.5, §4.4, §8.4).

## 2. Uruchomienie głównego przepływu

Instalacja (raz, z katalogu repozytorium):

```bash
python -m venv .venv
.venv\Scripts\activate            # Linux/macOS: source .venv/bin/activate
python -m pip install -r requirements.txt -r requirements-dev.txt
```

**Polecenie (CLI):**

```bash
python -m heating_optimizer --data data/processed/doba-live.csv --out wyniki/plan-2026-10-13.csv
```

**Wymagane wejście:** CSV doby z kolumnami `hour,price_pln_kwh,outside_temp_c,solar_radiation_wm2`,
dokładnie 24 kolejne godziny 0..23, liczby skończone, nasłonecznienie ≥ 0 (słownik: `data-dictionary.md`).
Parametry: `--t-min` (21,0), `--t-max` (22,5), `--t-start` (21,8) °C, opcjonalnie `--override GODZINA=0|1`.
Zamiast ścieżki można podać nazwę scenariusza (`--list` wypisuje dostępne).

**Oczekiwany wynik:** tabela 24 h na ekranie i podsumowanie — optymalizator **5,35 zł**, 0 h poniżej
T_min; termostat **11,15 zł**, 4 h poniżej T_min; oszczędność **5,81 zł (52,1 %)** — zgodnie z Lab 4.
Plik `wyniki/plan-2026-10-13.csv`: 25 linii (nagłówek + 24 godziny), kolumny wejścia + `optimal_state`,
`optimal_temp_c`, `thermostat_state`, `thermostat_temp_c`. Katalog `wyniki/` jest w `.gitignore`.

**Ten sam przepływ w GUI:** `npm run api` + `npm run dev` → http://localhost:5173 (albo
`docker compose up --build` → http://localhost:8080). Wynik dla tych samych ustawień jest taki sam
(test `test_scenarios.py` i ręczne sprawdzenie poniżej).

**Błędy (sprawdzone ręcznie 2026-11-10 na gałęzi integracyjnej):**

| Wejście / krok | Oczekiwane | Wynik |
| -------------- | ---------- | ----- |
| `--data data/test/doba-invalid.csv --out wyniki/bad.csv` (2 godziny) | komunikat „niepełna doba — brakujące godziny [2, …, 23]”, kod 1, brak pliku | zgodne |
| ponownie to samo `--out` co w pierwszym uruchomieniu | „plik … już istnieje — podaj nową nazwę”, kod 1, stary plik nietknięty | zgodne |
| `--out` = plik wejściowy | „plik wyniku nie może nadpisać pliku wejściowego”, kod 1 | zgodne (test) |
| `POST /api/optimize` z `{"t_start": NaN}` | HTTP 422 (wcześniej 500) | zgodne (test) |
| `POST /api/optimize` z `model_params.alpha = -5` | HTTP 422 (wcześniej 200 z bezsensownym planem) | zgodne (test) |
| scenariusz bez godziny 17 w `/api/optimize` | HTTP 422 „brakujące godziny [17]”, bez `rows` | zgodne (test) |
| GUI: API wyłączone, zmiana wymuszenia | baner z błędem, prawa kolumna **bez** planu z poprzednich ustawień | zgodne (przeglądarka) |
| GUI: „Pobierz dobę” dla 2026-11-10 | „Pobrano dane z PSE i Open-Meteo dla daty 2026-11-10.”, pliki w `data-local/`, `git status` czysty | zgodne |
| `compare_methods.py … results/lab4` bez `--overwrite` | odmowa, kod 1 | zgodne |

## 3. Wynik integracji i podział prac

**Zweryfikowana wersja:** gałąź `feature/lab6-integracja` = `main` (`ee1670b`) + scalone gałęzie
pięciu osób (kolejność niżej) + commit integracyjny. Weryfikował: **Sebastian Król** (nie jest autorem
zmian w silniku ani API). Po scaleniu: `pytest` **104 passed**; `npm run typecheck`, `npm run lint`,
`npm run build` bez błędów; `ruff check .` — 4 ostrzeżenia, wszystkie istniały już na `main`
(`check_data.py`, `check_lab4.py`, `examples/lab4`), żadne nowe; `check_data.py` i `check_lab4.py`
(K1–K7) OK; CLI i GUI sprawdzone jak w §2.

Kolejność scalania (zależności: Rączka opisuje w diagramach zachowanie po zmianach Oskara i Patryka):

| # | Gałąź / PR | Osoba | Zadania (Issues z Lab 5) | Pliki |
| - | ---------- | ----- | ------------------------ | ----- |
| 1 | `feature/lab6-walidacja-doby` | Kacper Mazur | **Z-01** kontrola 24 kolejnych godzin w `from_csv` → 422; **Z-02** GUI bez starego planu po błędzie; CLI: ochrona przed nadpisaniem `--out` | `inputs.py`, `datasets.py` (`load_inputs`), `cli.py`, `useOptimization.ts`, testy |
| 2 | `feature/lab6-walidacja-api` | Karol Brzozowski | **Z-03** NaN → 422; **Z-04** zakresy `model_params`; przykłady z instrukcji `examples/lab6/` | `schemas.py`, `main.py`, `test_api.py`, `examples/lab6/` |
| 3 | `feature/lab6-doba-live` | Oskar Wysocki | **Z-08** `doba_live.meta.json` + data w `/api/scenarios`; **Z-09** zapis atomowy do `data-local/`; **P-01** bez doby mieszanej; `.env.example` | `datasets.py` (katalogi), `builder.py`, `service.get_live_day`, `Dockerfile.api`, testy |
| 4 | `feature/lab6-wersja-wynikow` | Patryk Uchman | **Z-06** `dane_md5`, `data_uruchomienia` + kontrola K7; **Z-07** odmowa nadpisania bez `--overwrite` | `compare_methods.py`, `check_lab4.py`, `results/lab4/`, §4 `architecture.md` |
| 5 | `feature/lab6-wymuszenia-diagramy` | Sebastian Rączka | **Z-05** informacja o wymuszeniach w GUI; **P-02** diagramy §5, §6, `granice.drawio`; ocena usprawnienia (§5 niżej) | `OverridesGrid.*`, `architecture.md` §5–§6, `sequence.mmd`, `sensitivity.py`, `measure_sensitivity.py` |
| 6 | `feature/lab6-integracja` | Sebastian Król | **Z-10** kontekst w nazwie eksportu; integracja, README, ten plik | `ExportPlanButton.tsx`, `README.md`, `docs/implementation.md` |

Konflikty przy scalaniu: brak (podział plików ustalony przed pracą; wspólne pliki `datasets.py`,
`test_api.py` i `architecture.md` edytowane w rozłącznych miejscach).

Uwaga z przeglądu integracji: polecenie z README kończyło się błędem zapisu, gdy katalog `wyniki/`
nie istniał (komunikat był poprawny, ale brakowało kroku). Poprawka na gałęzi Kacpra
(`CLI: tworzenie brakującego katalogu wyniku`) i ponowne scalenie; test `test_cli_creates_missing_output_dir`.

## 4. Znane ograniczenia i otwarte zadania

- **Z-10 częściowo:** nazwa pliku eksportu ma scenariusz, `T_min`, `T_max`, `T_start` i **datę eksportu**,
  ale nie datę doby live — odpowiedź `/api/optimize` jej nie zawiera. Data doby jest w
  `data-local/doba_live.meta.json` i w opisie scenariusza z `/api/scenarios`. Otwarte: dodać `data_date`
  do odpowiedzi API (zmiana kontraktu `schemas.py` + `types.ts`).
- Lista scenariuszy w GUI jest pobierana raz przy starcie — opis `doba_live` z nową datą widać po odświeżeniu strony.
- **P-02:** `docs/diagrams/granice.drawio` poprawiony, ale `granice.png` trzeba wyeksportować ponownie
  z draw.io (Plik → Eksportuj → PNG) — w repo nadal stary obraz z „Tailwind” i „K1–K5”.
- W kontenerze Docker nie ma `data/raw/`, więc przy braku sieci `/api/live` nie ma próbki offline
  i zostaje poprzednia doba (`cached_bundled`) — zachowanie poprawne, ale bez świeżych danych.
- Termostat nadal nie stosuje wymuszeń (Z-05 rozwiązane informacją w GUI, nie zmianą porównania).
- `compare_methods.py` sprawdza dobę własną funkcją `check_input` i czyta plik drugi raz przez
  `HourlyInputs.from_csv` (po Z-01 kontrole się dublują) — kandydat na kolejne usprawnienie.
- Atomowość zapisu nie chroni przed dwoma równoczesnymi `GET /api/live` (ostatni wygrywa) — akceptowane
  przy jednym użytkowniku (ADR-001).

## 5. Ocena usprawnienia implementacji

_Pomiar i zmiana: Sebastian Rączka (`feature/lab6-wymuszenia-diagramy`)._

**Fragment:** `run_sensitivity_analysis` w `packages/core/src/heating_optimizer/sensitivity.py`
(używany przez `POST /api/sensitivity` i panel „Analiza wrażliwości”).
**Obserwacja:** przy siatce `max_overshoot` pętla wywoływała `simulate_thermostat` dla każdej wartości,
choć termostat nie zależy od `max_overshoot` (reguła tylko `T_min`/`T_max`, bez cen) — 5 identycznych symulacji.

**Warunki sprawdzenia:** doba `data/processed/doba-live.csv` (MD5 `729ecf79…`), domyślne siatki
(5 wartości), `T_min` 21,0, `T_max` 22,5, `T_start` 21,8; liczba wywołań zliczana opakowaniem funkcji
z logowaniem INFO na stderr; czas = mediana z 7 powtórzeń, ten sam komputer, 2 serie;
poprawność = skrót MD5 listy wierszy wyniku. Polecenie: `python scripts/measure_sensitivity.py`.

| Parametr | Przed: termostat / DP | Po: termostat / DP | Mediana czasu przed → po | Skrót wyniku przed = po |
| -------- | --------------------- | ------------------ | ------------------------ | ----------------------- |
| `max_overshoot` | 5× / 5× | **1×** / 5× | 31,7 → 31,8 ms; 30,3 → 29,8 ms | `9d4a29caa3d3` = `9d4a29caa3d3` |
| `t_min` (bez zmian w kodzie) | 5× / 5× | 5× / 5× | 29,1 → 29,3 ms | `a61778a1d618` = `a61778a1d618` |

**Wniosek:** zbędne symulacje termostatu spadły z 5 do 1, wynik jest identyczny (test
`test_overshoot_grid_reuses_one_thermostat_with_identical_rows`), walidacja wejścia bez zmian.
Czas się praktycznie nie zmienił — dominuje DP (5 wywołań, ok. 6 ms każde), a symulacja termostatu
to ułamek milisekundy. Zmianę zostawiamy, bo usuwa zbędne operacje bez kosztu w czytelności;
przy siatce `t_min` termostat zależy od wartości, więc tam liczymy go nadal dla każdej.
Większe przyspieszenie wymagałoby zmian w DP (`optimizer.py`) — zapisane jako możliwa praca dalsza,
bez obserwacji, która by jej teraz wymagała (czas ok. 30 ms jest akceptowalny dla GUI).

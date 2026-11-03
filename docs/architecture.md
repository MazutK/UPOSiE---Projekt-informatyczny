# Lab 5 — projekt architektury: optymalizator ogrzewania

Kolejność edycji tego pliku: Kacper → Karol → Patryk → Rączka → Oskar → Król.
Każda osoba przed edycją robi `git pull` i podmienia **tylko swój** blok `_(uzupełnia …)_`.
Każda osoba robi własny commit ze swoją sekcją.

| Osoba | Imię | Sekcja / rezultat | Diagram |
| ----- | ---- | ----------------- | ------- |
| 1 | Kacper Mazur | §1 granice systemu, odpowiedzialności modułów, §2 UC-01 | — |
| 2 | Karol Brzozowski | §3 kontrakt `POST /api/optimize` | — |
| 3 | Patryk Uchman | §4 model danych (schemat plików) | — |
| 4 | Sebastian Rączka | §5 przepływ danych, §6 diagram sekwencji UML UC-01, opcjonalnie diagram granic | Mermaid `flowchart LR` i `sequenceDiagram` (+ `examples/lab5/sequence.mmd`); opcjonalnie `docs/diagrams/granice.drawio` + PNG |
| 5 | Oskar Wysocki | ADR `docs/decisions/001-<temat>.md`, §7 co istnieje / co planowane | — |
| 6 | Sebastian Król | §8 przegląd + GitHub Issues | — |

Wariant architektury: **usługa z API** (FastAPI w `apps/api`) + **analiza plikowa**
(`scripts/`, `data/`, `results/`). Bez bazy danych — nie tworzymy fikcyjnej bazy pod diagram.

Wejście do projektu: `docs/problem.md` (wymagania R1–R6), `docs/data-dictionary.md`,
`docs/processing.md` (Lab 3), `docs/experiment.md` (Lab 4), `docs/PROJEKT.md` (warstwy).

Legenda statusu elementów: **istnieje** (jest w repo i działa) / **planowane** (do zrobienia, ma Issue).

---

## 1. Granice systemu

_(uzupełnia Osoba 1 — Kacper Mazur)_

- Użytkownik:
- Systemy zewnętrzne (PSE RCE, Open-Meteo — co od nich bierzemy, w jakim formacie):
- Zakres odpowiedzialności naszego rozwiązania:
- Poza zakresem (z `docs/problem.md`):

Diagram granic i modułów (opcjonalny): `docs/diagrams/granice.drawio` / `granice.png` (Sebastian Rączka).

### 1.1. Odpowiedzialności modułów

_(uzupełnia Osoba 1 — Kacper Mazur)_

| Moduł | Ścieżka | Odpowiada za | Nie odpowiada za | Status |
| ----- | ------- | ------------ | ---------------- | ------ |
| GUI | `apps/web` | | | istnieje |
| API | `apps/api` | | | istnieje |
| Silnik | `packages/core` | | | istnieje |
| Źródła danych | `packages/core/.../data_sources/`, `scripts/prepare_data.py` | | | istnieje |
| Kontrola danych | `scripts/check_data.py` | | | istnieje |

---

## 2. Przypadek użycia UC-01

_(uzupełnia Osoba 1 — Kacper Mazur)_

| Element | UC-01 — plan grzania na 24 h i porównanie z termostatem |
| ------- | ------------------------------------------------------- |
| Cel i wymaganie | (R1, R2, R3, R4, R6 z `docs/problem.md`) |
| Wejście | |
| Warunek rozpoczęcia | |
| Przebieg | |
| Wynik | |
| Brak danych / błąd | |
| Kryterium odbioru | |

Poprawny przebieg:

1.

Błędny przebieg:

1.

---

## 3. Kontrakt interfejsu `POST /api/optimize`

_Osoba 2 — Karol Brzozowski._

Granica: **GUI ↔ API** (HTTP/JSON). Jest to krok „obliczenie” w UC-01: jedno wywołanie zwraca
plan DP i plan termostatu na tych samych danych.

Źródło prawdy: `apps/api/src/hems_api/schemas.py` i `apps/web/src/api/types.ts` (muszą być zgodne).
Obsługa błędów: `apps/api/src/hems_api/main.py`. Testy: `apps/api/tests/test_api.py`.
Wszystkie odpowiedzi poniżej sprawdzone na działającym kodzie (`fastapi.testclient`, 2026-11-03).

### 3.1. Wejście

| Pole | Typ | Jednostka | Domyślnie | Ograniczenie |
| ---- | --- | --------- | --------- | ------------ |
| `scenario` | string | — | `doba_zmienna_cena` | nazwa z `GET /api/scenarios` (plik CSV doby) |
| `t_min` | float | °C | 21.0 | 5.0 ≤ x ≤ 30.0, `t_min ≤ t_max` |
| `t_max` | float | °C | 22.5 | 5.0 ≤ x ≤ 30.0 |
| `t_start` | float | °C | 21.8 | 0.0 ≤ x ≤ 35.0 — temperatura wewnątrz o godz. 0 |
| `max_overshoot` | float | °C | 1.0 | 0.0 ≤ x ≤ 5.0 — ile DP może przekroczyć `t_max` |
| `overrides` | obiekt `{godzina: 0\|1}` | h → stan | `{}` | godzina 0..23, stan 0 albo 1; dotyczy **tylko planu DP** |
| `model_params` | obiekt | — | `{}` | opcjonalna podmiana `alpha`, `beta`, `gamma`, `constant`, `delay` (0..6 h), `heater_power_kw` (> 0, kW); brak pola = wartość z `parametry.json` |

Wszystkie pola są opcjonalne — puste `{}` liczy domyślny scenariusz.

### 3.2. Wynik (HTTP 200)

| Pole | Typ | Jednostka | Znaczenie |
| ---- | --- | --------- | --------- |
| `scenario`, `t_min`, `t_max`, `t_start` | jak wejście | | echo parametrów, z którymi liczono |
| `hours` | int | h | długość doby (24) |
| `rows[]` | lista 24 obiektów | | jeden wiersz = jedna godzina |
| `rows[].hour` | int | h | 0..23 |
| `rows[].price_pln_kwh` | float | zł/kWh | cena RCE z pliku doby |
| `rows[].outside_temp_c` | float | °C | temperatura zewnętrzna |
| `rows[].solar_radiation_wm2` | float | W/m² | nasłonecznienie |
| `rows[].optimal_state` / `thermostat_state` | int 0\|1 | — | decyzja grzania DP / termostatu |
| `rows[].optimal_temp_c` / `thermostat_temp_c` | float | °C | temperatura wewnątrz |
| `rows[].optimal_cost_pln` / `thermostat_cost_pln` | float | zł | koszt w tej godzinie |
| `optimal`, `thermostat` | `PlanSummary` | | podsumowanie planu |
| `.cost_pln` | float | zł | koszt doby |
| `.energy_kwh` | float | kWh | zużyta energia |
| `.heating_hours` | int | h | liczba godzin grzania |
| `.hours_below_t_min` | int | h | godziny poniżej `t_min` |
| `.deficit_kh` | float | K·h | suma niedogrzania poniżej `t_min` |
| `.mean_temp_c` | float | °C | średnia temperatura wewnątrz |
| `saving_pln` | float | zł | `thermostat.cost_pln − optimal.cost_pln` |
| `saving_pct` | float | % | oszczędność względem termostatu; 0.0, gdy koszt termostatu = 0 |

Przykład żądania:

```json
{"scenario": "doba_szczyt_wieczorny", "t_min": 21.0, "t_max": 22.5, "t_start": 21.8}
```

Przykład odpowiedzi (skrócony — `rows` ma 24 elementy):

```json
{
  "scenario": "doba_szczyt_wieczorny", "hours": 24,
  "t_min": 21.0, "t_max": 22.5, "t_start": 21.8,
  "rows": [
    {"hour": 0, "price_pln_kwh": 0.5, "outside_temp_c": 1.0, "solar_radiation_wm2": 0.0,
     "optimal_state": 1, "optimal_temp_c": 21.64, "optimal_cost_pln": 0.75,
     "thermostat_state": 0, "thermostat_temp_c": 21.64, "thermostat_cost_pln": 0.0}
  ],
  "optimal":    {"cost_pln": 8.625,  "energy_kwh": 16.5, "heating_hours": 11, "hours_below_t_min": 0, "deficit_kh": 0.0,  "mean_temp_c": 21.87},
  "thermostat": {"cost_pln": 22.545, "energy_kwh": 24.0, "heating_hours": 16, "hours_below_t_min": 5, "deficit_kh": 0.92, "mean_temp_c": 21.65},
  "saving_pln": 13.92, "saving_pct": 61.74
}
```

### 3.3. Błędy

Błąd nigdy nie zwraca planu ani kosztu „0” — odpowiedź ma tylko pole `detail`.

| Sytuacja | Kod | Treść `detail` | Kto wykrywa |
| -------- | --- | -------------- | ----------- |
| Niepoprawny JSON (np. ucięty) | **422** | lista, `type: "json_invalid"` | FastAPI |
| Zły typ pola (np. `"t_min": "abc"`) | 422 | lista, `type: "float_parsing"`, `loc: ["body","t_min"]` | Pydantic |
| Wartość poza zakresem (np. `t_min: 40`) | 422 | lista, `type: "less_than_equal"` | Pydantic |
| `t_min > t_max` | 422 | lista, `msg: "Value error, t_min nie może być większe niż t_max"` | `OptimizeRequest.check_band` |
| Wymuszenie ≠ 0/1 | 422 | lista, `msg: "Value error, wymuszenie musi mieć wartość 0 albo 1"` | `OptimizeRequest.check_band` |
| Godzina wymuszenia poza 0..23 | 422 | tekst `"override hour 30 is outside 0..23"` | silnik (`optimizer._validate_overrides`) → `ValueError` |
| Nieznany scenariusz | 404 | tekst `"nieznany scenariusz 'x'; dostępne: …"` | `datasets.resolve` → `FileNotFoundError` |
| `NaN` w liczbie (JSON z `NaN`) | **500** | brak — błąd serwera | **wada**, patrz 3.5 |

`detail` ma dwa kształty: **lista obiektów** (błąd walidacji żądania) albo **tekst** (błąd z silnika).
GUI obsługuje oba (`readErrorDetail` w `apps/web/src/api/client.ts`) i pokazuje `msg` użytkownikowi.
Brak odpowiedzi serwera → `ApiError("Brak połączenia z API.", 0)`.

Uwaga: instrukcja Lab 5 podaje przykład 400 dla złego JSON — u nas FastAPI zwraca 422.
Przyjmujemy zachowanie frameworka i nie dodajemy osobnego 400.

### 3.4. Efekt uboczny i ponowienie

- Brak zapisu: endpoint tylko czyta CSV doby i `parametry.json`, nic nie tworzy ani nie zmienia.
- Ponowienie tego samego żądania daje identyczną odpowiedź (sprawdzone: dwa wywołania, `r1 == r2`).
  Można bezpiecznie ponawiać po błędzie sieci.
- Wyjątek: scenariusz `doba_live` jest nadpisywany przez `GET /api/live`. To samo żądanie
  z `scenario: "doba_live"` może dać inny wynik po pobraniu innej daty. Odpowiedź nie mówi,
  z jakiej daty są dane — to musi pokazać GUI (widget `features/live-data/`).

### 3.5. Kto sprawdza co

| Warstwa | Sprawdza | Nie sprawdza |
| ------- | -------- | ------------ |
| GUI (`ControlsPanel.tsx`) | trzyma `t_min ≤ t_max` (podbija drugie pole), wysyła tylko liczby z `NumberField` | zakresów 5–30 °C |
| API (`schemas.py`) | typy, zakresy, `t_min ≤ t_max`, wymuszenia 0/1 | czy godzina wymuszenia mieści się w dobie, sensowności `model_params` |
| Silnik (`optimizer.py`, `inputs.py`) | godziny wymuszeń 0..23, kolumny i liczba wierszy CSV | — |

Znane luki (do zgłoszenia jako Issues w przeglądzie, §8):

1. `NaN` w żądaniu → HTTP 500 zamiast 422 (walidacja odrzuca, ale serializacja komunikatu
   z `NaN` się wywraca). Kryterium: `{"t_start": NaN}` → 422.
2. `model_params` bez zakresów — np. `alpha: -5` zwraca 200 z fizycznie bezsensownym planem.
   Kryterium: ujemne `alpha`/`beta` → 422.
3. Termostat ignoruje `overrides` — porównanie z wymuszeniami nie jest symetryczne.
   Trzeba to opisać w GUI albo zastosować wymuszenia w obu planach.

---

## 4. Model danych

_(uzupełnia Osoba 3 — Patryk Uchman)_

Projekt nie ma bazy danych — model fizyczny to pliki. Decyzja (ADR, Oskar): `docs/decisions/`.

### 4.1. Model logiczny

| Obiekt | Co oznacza jeden rekord | Powiązania |
| ------ | ----------------------- | ---------- |
| Doba wejściowa | | |
| Parametry budynku | | |
| Uruchomienie porównania | | |
| Wynik metody | | |
| Obserwacja godzinowa | | |

### 4.2. Model fizyczny (pliki)

| Plik | Ścieżka | Format | Pola i typy | Klucz / unikalność |
| ---- | ------- | ------ | ----------- | ------------------ |
| | `data/processed/doba-live.csv` | CSV | | |
| | `packages/core/.../data/parametry.json` | JSON | | |
| | `results/lab4/comparison.csv` | CSV | | |
| | `results/lab4/observations.csv` | CSV | | |

### 4.3. Identyfikator uruchomienia i wersja danych

- Jak powiązać wynik z wersją danych (MD5 / commit — patrz `docs/experiment.md`):
- Jak unikamy nadpisania wyników różnych uruchomień:

---

## 5. Przepływ danych

_(uzupełnia Osoba 4 — Sebastian Rączka)_

Format przy co najmniej dwóch strzałkach; skąd odbiorca pozna datę ostatniego odświeżenia.

```mermaid
flowchart LR
```

---

## 6. Diagram sekwencji UML — UC-01

_(uzupełnia Osoba 4 — Sebastian Rączka)_

Uczestnicy: Użytkownik, GUI, API, Silnik (DP + termostat), źródła danych (dla `/api/live`).
Co najmniej jedna ścieżka błędna w `alt`/`else`. Kod także w `examples/lab5/sequence.mmd`.

```mermaid
sequenceDiagram
```

---

## 7. Co istnieje, co planowane, potrzebne zmiany

_(uzupełnia Osoba 5 — Oskar Wysocki)_

Decyzja architektoniczna: `docs/decisions/001-<temat>.md` (np. `001-storage.md` — pliki vs SQLite,
albo `001-api.md` — lokalny moduł vs osobna usługa API).

| Element | Status (istnieje / planowane) | Potrzebna zmiana | Właściciel |
| ------- | ----------------------------- | ---------------- | ---------- |
| | | | |

---

## 8. Przegląd projektu

_(uzupełnia Osoba 6 — Sebastian Król)_

Prześledzić UC-01 od wejścia do wyniku tylko z tej dokumentacji.

| Sprawdzenie | Wynik | Uwagi |
| ----------- | ----- | ----- |
| Nazwy pól zgodne z Lab 3 (`docs/data-dictionary.md`) | | |
| Metody zgodne z Lab 4 (`docs/experiment.md`) | | |
| Elementy diagramów zgodne z kodem | | |
| Da się wskazać wejście, wynik, moduł i zachowanie przy błędzie | | |

Znalezione niespójności i poprawki:

-

Issues (cel, kryterium odbioru, właściciel):

| Issue | Cel | Właściciel |
| ----- | --- | ---------- |
| | | |

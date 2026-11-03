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

_(uzupełnia Osoba 2 — Karol Brzozowski)_

Źródło prawdy: `apps/api/src/hems_api/schemas.py` i `apps/web/src/api/types.ts` (muszą być zgodne).
Testy: `apps/api/tests/test_api.py`.

| Element | Ustalenie |
| ------- | --------- |
| Operacja | `POST /api/optimize`, `Content-Type: application/json` |
| Wejście (pola, typy, jednostki) | |
| Sukces | |
| Błędna składnia | |
| Niepoprawne dane | |
| Efekt uboczny | |
| Kto sprawdza co (GUI / API / silnik) | |

Przykład żądania:

```json
```

Przykład odpowiedzi:

```json
```

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

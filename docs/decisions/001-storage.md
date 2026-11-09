# ADR-001: Zapis danych wejściowych i wyników — pliki CSV/JSON zamiast bazy SQLite

_Autor: Oskar Wysocki (Osoba 5). Data: 2026-11-09._

**Status:** przyjęta (opisuje stan istniejący w repo po Lab 3–4; obowiązuje dla Lab 5).

## Kontekst

- System liczy plan grzania dla **jednej doby** (24 rekordy godzinowe) i **jednego budynku**
  (`parametry.json`). Jeden użytkownik, lokalnie, bez kont (`docs/problem.md`, §1 `architecture.md`).
- Danych jest bardzo mało: doba to 24 wiersze × 4 kolumny (~1 KB), parametry budynku to 6 liczb,
  wynik jednego uruchomienia `scripts/compare_methods.py` to 2 pliki CSV (2 + 24 wiersze).
- Wyniki Lab 4 muszą dać się **odtworzyć i sprawdzić**: wersja danych to MD5 pliku z repo
  (`729ecf79df5d39a3ef5e9c64d8be77fe`) + commit (`docs/experiment.md`, §4.3 `architecture.md`).
  Prowadzący i zespół oglądają dane i wyniki bezpośrednio na GitHubie.
- `POST /api/optimize` niczego nie zapisuje (§3.4) — wynik żyje tylko w pamięci GUI.
  Zapis na dysk robią tylko: `GET /api/live` (`doba_live.csv`), `scripts/prepare_data.py`
  (`data/processed/doba-live.csv`) i `scripts/compare_methods.py` (`results/…`).
- Instrukcja Lab 5 zabrania tworzenia fikcyjnej bazy tylko po to, żeby narysować diagram.

## Decyzja

Dane wejściowe, parametry i wyniki przechowujemy **w plikach w repozytorium**, bez bazy danych:

| Co | Gdzie | Format |
| -- | ----- | ------ |
| surowe odpowiedzi źródeł | `data/raw/*-sample.json` | JSON (jak z PSE / Open-Meteo) |
| doba przetworzona (Lab 3) | `data/processed/doba-live.csv` | CSV, 4 kolumny, 24 wiersze |
| doby scenariuszy i doba live | `packages/core/src/heating_optimizer/data/doba_*.csv` | CSV, te same 4 kolumny |
| parametry budynku | `packages/core/src/heating_optimizer/data/parametry.json` | JSON |
| wyniki porównań | `results/<uruchomienie>/comparison.csv`, `observations.csv` | CSV |

Zasady (zgodne z modelem danych w §4 `architecture.md`):

1. **Uruchomienie = katalog** w `results/`. Nowe uruchomienie → nowy katalog, nie nadpisujemy starego.
2. **Wersja danych = MD5 pliku z repo + commit.** Wynik bez wskazania pliku wejściowego (kolumna `dane`)
   jest nieważny.
3. **Przed użyciem doba przechodzi kontrolę** (`scripts/check_data.py` albo `data_sources/builder.py`);
   błąd = raport, bez nowego pliku wyniku.
4. Schemat pliku (nazwy kolumn, jednostki) jest opisany w `docs/data-dictionary.md` i §4.2 —
   to jest nasz „schemat bazy”.

## Alternatywa: SQLite

Jedna baza `data/hems.db` z tabelami `doba_godzina`, `budynek`, `uruchomienie`, `wynik_metody`,
`obserwacja` (te same obiekty co w modelu logicznym §4.1), zapisywana przez API i skrypty.

Zalety, które tracimy:

- klucze i ograniczenia (`CHECK hour BETWEEN 0 AND 23`, `UNIQUE(uruchomienie, hour)`, `NOT NULL`)
  pilnowane przez bazę, a nie przez nasz kod,
- transakcje — zapis wyniku jest atomowy (wszystko albo nic),
- naturalny identyfikator uruchomienia (`id INTEGER PRIMARY KEY`, `created_at`) i historia wszystkich
  uruchomień, także z GUI,
- zapytania przekrojowe („wszystkie uruchomienia dla doby X”) bez pisania pętli po katalogach.

## Powód wyboru

- **Skala nie uzasadnia bazy.** Kilka plików po kilkadziesiąt wierszy; brak zapytań między uruchomieniami
  w wymaganiach R1–R6.
- **Odtwarzalność i przegląd.** CSV w repo ma wersję w gicie, MD5 da się policzyć jednym poleceniem,
  a zmianę widać w diffie na GitHubie. Plik `.db` jest binarny — diff i MD5 zmieniają się przy każdym
  zapisie (także przy zmianie metadanych SQLite), więc nie nadaje się na „wersję danych”.
- **Zgodność z Lab 3–4.** Cały istniejący kod (`inputs.py`, `prepare_data.py`, `check_data.py`,
  `compare_methods.py`, `check_lab4.py`) czyta i pisze CSV. Przejście na SQLite oznacza przepisanie
  każdego z tych miejsc, a nie dodanie nowej funkcji.
- **Zero nowych zależności.** `requirements.txt` ma tylko `pandas`; obraz Dockera API nie potrzebuje
  wolumenu na bazę ani migracji przy starcie.
- **Instrukcja Lab 5** — baza tworzona tylko pod diagram byłaby fikcyjna (API jej nie potrzebuje,
  bo `POST /api/optimize` nic nie zapisuje).

## Koszt i utrzymanie

| | Pliki (wybrane) | SQLite (odrzucone) |
| - | --------------- | ------------------ |
| Wdrożenie teraz | 0 — istnieje | `schema.sql`, warstwa zapisu/odczytu, import istniejących CSV, przepisanie 5 modułów/skryptów i ich testów; szacunkowo 2–3 dni pracy jednej osoby |
| Zależności | brak nowych | `sqlite3` jest w Pythonie, ale potrzebne migracje schematu i wolumen w `docker-compose.yml` |
| Kontrola poprawności | **nasza** — `check_data.py`, `builder.py`, `inputs.py`; każda luka to błąd (np. §2.4 luka 2: CSV z 2 godzinami daje plan) | ograniczenia w schemacie |
| Atomowość zapisu | **brak** — `save_as_csv` i `compare_methods.py` piszą wprost do pliku docelowego; przerwanie w trakcie zostawia niepełny plik | transakcja |
| Identyfikacja uruchomienia | konwencja nazw katalogów, łatwo ją złamać | klucz główny + `created_at` |
| Przegląd na GitHubie | czytelny diff CSV | plik binarny, trzeba eksportować |
| Utrzymanie | zmiana kolumny = zmiana `data-dictionary.md` + parserów | zmiana kolumny = migracja + parsery |

## Konsekwencja

- Ochrona przed nadpisaniem i powiązanie wyniku z wersją danych **musimy zapewnić sami** w kodzie
  skryptów — stąd zmiany Z-06, Z-07 w §7 `architecture.md`.
- Doba live jest jedna i jest nadpisywana przy każdym `GET /api/live`; sam plik nie mówi, z jakiej daty
  pochodzi, a ponieważ leży w śledzonym katalogu pakietu, każde pobranie zmienia `git status`.
  Trzeba dodać metadane i przenieść zapis poza repo (Z-08, Z-09).
- Historia obliczeń z GUI **nie istnieje** — użytkownik może tylko pobrać CSV planu (`ExportPlanButton`).
  To świadome ograniczenie, nie błąd.
- Dwa równoczesne `GET /api/live` mogą zapisać ten sam plik naraz. Przy jednym użytkowniku lokalnie
  akceptujemy to ryzyko; zapis przez plik tymczasowy + `os.replace` (Z-09) usuwa niepełny plik.

## Warunek ponownego rozważenia

Wracamy do decyzji (kandydat: SQLite, potem PostgreSQL), gdy spełni się **którykolwiek** warunek:

1. GUI ma zapisywać i pokazywać historię uruchomień (np. „porównaj z wczoraj”) — powstaje wymaganie
   na zapytania między uruchomieniami.
2. System obsługuje więcej niż jeden budynek albo więcej niż jednego użytkownika (konta).
3. API działa w więcej niż jednej instancji albo z równoczesnymi zapisami (ryzyko wyścigu przy plikach).
4. Liczba katalogów w `results/` przekroczy kilkadziesiąt i ich przeglądanie ręcznie przestanie wystarczać.
5. Pojawi się ciągłe pobieranie danych (np. codzienny import PSE) zamiast pojedynczych dób.

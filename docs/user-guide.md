# Instrukcja użytkownika: Optymalizator ogrzewania

Program wyznacza najtańszy plan grzania na jedną dobę (24 godziny) przy zmiennych cenach energii
i porównuje go z prostym termostatem. Plan musi utrzymać temperaturę w zadanym paśmie komfortu.

## 1. Wymagania

- Python 3.10+ (wiersz poleceń i API),
- Node 20+ (GUI w trybie deweloperskim) **albo** Docker Desktop (całość jednym poleceniem).

Instalacja (z katalogu repozytorium):

```bash
python -m venv .venv
# Windows PowerShell: .\.venv\Scripts\Activate.ps1
# Windows Git Bash:   source .venv/Scripts/activate
# Linux/macOS:        source .venv/bin/activate
python -m pip install -r requirements.txt -r requirements-dev.txt
```

## 2. Uruchomienie

### 2.1. Wiersz poleceń (główny przepływ UC-01)

```bash
python -m heating_optimizer --data data/processed/doba-live.csv --out wyniki/plan.csv
```

| Opcja | Znaczenie | Domyślnie |
|---|---|---|
| `--data` | nazwa scenariusza (lista: `--list`) albo ścieżka do pliku CSV doby | `doba_zmienna_cena` |
| `--list` | wypisuje dostępne scenariusze i kończy działanie | — |
| `--t-min`, `--t-max` | dolna i górna granica komfortu [°C] | 21.0, 22.5 |
| `--t-start` | temperatura w pomieszczeniu na początku doby [°C] | 21.8 |
| `--override GODZINA=STAN` | wymusza grzanie (1) lub jego brak (0) w danej godzinie, np. `--override 6=1`; można powtarzać | — |
| `--params` | plik JSON z parametrami modelu budynku | wbudowany `parametry.json` |
| `--out` | zapis wyników godzinowych do CSV (istniejący plik nie zostanie nadpisany) | brak zapisu |

Wbudowane scenariusze: `doba_live`, `doba_mroz`, `doba_slonecznie`, `doba_szczyt_wieczorny`,
`doba_zmienna_cena`.

### 2.2. Interfejs graficzny

- Docker: `docker compose up --build`, potem <http://localhost:8080>.
- Bez Dockera: `npm install`, następnie w dwóch terminalach `npm run api` i `npm run dev`,
  potem <http://localhost:5173>.

## 3. Dane wejściowe

Plik CSV z nagłówkiem `hour,price_pln_kwh,outside_temp_c,solar_radiation_wm2` i **dokładnie 24 wierszami**
dla godzin 0–23:

| Kolumna | Jednostka | Uwagi |
|---|---|---|
| `hour` | godzina 0–23 | każda godzina dokładnie raz |
| `price_pln_kwh` | zł/kWh | cena energii w danej godzinie |
| `outside_temp_c` | °C | temperatura zewnętrzna |
| `solar_radiation_wm2` | W/m² | nasłonecznienie, nie może być ujemne |

Puste wartości, `nan` i `inf` są odrzucane. Przykład poprawnej doby: `data/processed/doba-live.csv`.

## 4. Interpretacja wyniku

Program wypisuje tabelę godzinową i podsumowanie. Przykład dla `data/processed/doba-live.csv`
(ustawienia domyślne):

```
                            optymalizator  termostat
 Koszt energii [zł]                  5.35      11.15
 Energia [kWh]                        9.0       15.0
 Godziny grzania                        6         10
 Godziny poniżej T_min                  0          4
 Średnia temperatura [°C]           21.53      21.75

 Oszczędność: 5.81 zł (52.1%)
```

- **Tabela godzinowa:** `cena` (zł/kWh), `T_zew` (°C), a dla każdej metody stan grzania
  (`1` = grzanie włączone, `0` = wyłączone) i temperatura w pomieszczeniu `T_wew` (°C) na koniec godziny.
- **Koszt energii [zł]:** suma (energia × cena) za całą dobę. Niższy jest lepszy.
- **Energia [kWh]:** łączne zużycie energii na grzanie.
- **Godziny poniżej T_min:** liczba godzin, w których temperatura spadła poniżej dolnej granicy komfortu.
  Dla planu optymalnego powinno to być 0. Wartość większa od 0 oznacza, że przy tych danych
  i ustawieniach pasma nie da się utrzymać komfortu.
- **Oszczędność:** różnica kosztu termostat − optymalizator, w złotych i w procentach kosztu termostatu.

Plik `--out` zawiera kolumny: `hour, price_pln_kwh, outside_temp_c, solar_radiation_wm2,
optimal_state, optimal_temp_c, thermostat_state, thermostat_temp_c` (te same jednostki co wyżej).

Wynik dotyczy modelu budynku z pliku parametrów, a nie konkretnego domu. Ograniczenia metody opisuje
[`experiment.md`](experiment.md).

## 5. Komunikaty błędów

Przy błędzie program wypisuje komunikat zaczynający się od `Błąd:` i kończy się kodem 1, bez zapisu
pliku wyniku. Błędne opcje wiersza poleceń kończą się kodem 2.

| Komunikat (przykład) | Przyczyna | Co zrobić |
|---|---|---|
| `Błąd: doba-invalid.csv: niepełna doba — brakujące godziny [2, 3, …]` | w pliku brakuje godzin (nie ma 24 wierszy 0–23) | uzupełnić dane o brakujące godziny |
| `Błąd: nan.csv: godzina 5 ma wartość pustą lub nieskończoną` | pusta komórka, `nan` lub `inf` | poprawić wartość w podanej godzinie |
| `Błąd: …: wiersz N ma niepoprawną liczbę` | tekst zamiast liczby | poprawić wiersz N |
| `Błąd: …: godzina N ma ujemne nasłonecznienie` | ujemna wartość `solar_radiation_wm2` | poprawić wartość |
| `Błąd: …: godzina N występuje więcej niż raz` | zduplikowana godzina | usunąć duplikat |
| `Błąd: …: missing columns [...]` | brak wymaganej kolumny w nagłówku | poprawić nagłówek (patrz sekcja 3) |
| `Błąd: nieznany scenariusz 'X'; dostępne: …` | zła nazwa scenariusza lub ścieżka do nieistniejącego pliku | sprawdzić `--list` albo ścieżkę |
| `Błąd: plik wyniki/plan.csv już istnieje — podaj nową nazwę` | plik `--out` już istnieje | podać nową nazwę pliku |
| `Błąd: plik wyniku nie może nadpisać pliku wejściowego` | `--out` wskazuje plik wejściowy | podać inną ścieżkę |
| `Błąd: t_min must not be greater than t_max` | `--t-min` większe niż `--t-max` | poprawić pasmo komfortu |
| `Błąd: override hour 30 is outside 0..23` | godzina w `--override` spoza doby | podać godzinę 0–23 |
| `error: argument --override: oczekiwano GODZINA=0/1, otrzymano 'abc'` | zły format `--override` (kod 2) | użyć formatu np. `6=1` |

W GUI te same błędy wyświetlają się jako komunikat zwrócony przez API (HTTP 404: nie znaleziono
scenariusza, 422: niepoprawne dane, 502: błąd pobierania danych publicznych).

## 6. Testy

```bash
python -m pytest -v
```

Testy uruchamiają się też automatycznie w GitHub Actions przy każdym `push` i `pull_request`
(`.github/workflows/check.yml`). Raport (`test-report`) można pobrać ze strony przebiegu w zakładce
**Actions**. Plan testów i wyniki: [`tests.md`](tests.md).

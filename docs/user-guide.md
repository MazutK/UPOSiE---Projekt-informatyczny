# Instrukcja użytkownika: optymalizator ogrzewania

_Lab 7. Autor: Kacper Mazur. Sprawdza (bez podpowiedzi autora): Sebastian Król, wynik w `docs/tests.md`, sekcja 6._

## 1. Do czego służy

Program odpowiada na pytanie: **kiedy w ciągu najbliższej doby włączać grzanie elektryczne,
żeby utrzymać temperaturę w zadanym paśmie jak najtaniej przy taryfie dynamicznej?**

Dla jednej doby (24 godziny cen energii i pogody) program:

1. wyznacza najtańszy plan grzania godzina po godzinie (optymalizator DP),
2. liczy, co zrobiłby zwykły termostat na tych samych danych,
3. pokazuje koszt w zł, zużycie energii, godziny poniżej dolnej granicy komfortu i oszczędność.

Program **nie steruje** grzejnikiem, nie prognozuje cen i liczy dla jednego budynku referencyjnego
(parametry w `packages/core/src/heating_optimizer/data/parametry.json`).

## 2. Przygotowanie (raz)

Potrzebny Python 3.10+ (dla GUI także Node 20+). W katalogu repozytorium:

```bash
python -m venv .venv
# Windows (PowerShell):  .\.venv\Scripts\Activate.ps1
# Linux/macOS:           source .venv/bin/activate
python -m pip install -r requirements.txt -r requirements-dev.txt
```

Sprawdzenie, że wszystko działa: `python -m pytest` powinno zakończyć się komunikatem `passed`
bez `failed`.

## 3. Wyznaczenie planu z linii poleceń (CLI)

```bash
python -m heating_optimizer --data data/processed/doba-live.csv --out wyniki/plan-2026-10-13.csv
```

| Opcja | Znaczenie | Domyślnie |
|---|---|---|
| `--data` | plik CSV doby albo nazwa wbudowanego scenariusza (`--list` wypisuje scenariusze) | `doba_zmienna_cena` |
| `--t-min` | dolna granica komfortu [°C] | 21,0 |
| `--t-max` | górna granica komfortu [°C] | 22,5 |
| `--t-start` | temperatura w pomieszczeniu na początku doby [°C] | 21,8 |
| `--override GODZINA=0\|1` | wymuszenie stanu grzania w danej godzinie (można powtarzać, np. `--override 6=1`) | brak |
| `--out` | zapis planu do nowego pliku CSV | brak zapisu |

Wartości temperatur podaje się z kropką (`21.5`), nie z przecinkiem.

**Plik wejściowy** musi mieć kolumny `hour,price_pln_kwh,outside_temp_c,solar_radiation_wm2`
i dokładnie 24 godziny 0..23 (słownik pól: `docs/data-dictionary.md`).

## 4. Wyznaczenie planu w przeglądarce (GUI)

```bash
npm install          # raz
npm run api          # okno 1: API na porcie 8000
npm run dev          # okno 2: GUI
```

Otwórz http://localhost:5173 (albo `docker compose up --build` → http://localhost:8080).

1. W panelu **Parametry** wybierz **Scenariusz doby** (np. `doba_live` = doba rzeczywista).
2. Ustaw **Dolną granicę komfortu (T_min)**, **Górną granicę komfortu (T_max)** i
   **Temperaturę początkową (T_start)**. Plan przelicza się sam po każdej zmianie.
3. Opcjonalnie: **Wymuszenia godzin** (np. grzanie o 6:00) i **Dane publiczne (PSE + Open-Meteo)** →
   wybierz datę i **Pobierz dobę**.
4. **Pobierz plan godzinowy (CSV)** zapisuje plan na dysk.

## 5. Jak czytać wynik

Przykład dla `data/processed/doba-live.csv` (13.10.2026) i ustawień domyślnych:

```
                            optymalizator  termostat
 Koszt energii [zł]                  5.35      11.15
 Energia [kWh]                        9.0       15.0
 Godziny grzania                        6         10
 Godziny poniżej T_min                  0          4
 Średnia temperatura [°C]           21.53      21.75

 Oszczędność: 5.81 zł (52.1%)
```

- **Koszt energii** to koszt grzałki 1,5 kW w godzinach, w których plan ją włącza, po cenach z pliku.
- **Godziny poniżej T_min**: w ilu godzinach temperatura spadła poniżej dolnej granicy. 0 oznacza,
  że komfort był zachowany przez całą dobę. Najpierw liczy się komfort, potem koszt, więc tańszy plan
  nie „kupuje” oszczędności zimnem.
- **Oszczędność**: o ile plan DP jest tańszy od termostatu na tej samej dobie.
- **Tabela godzinowa / plik CSV**: `optimal_state` i `thermostat_state` (1 = grzanie włączone),
  `optimal_temp_c` i `thermostat_temp_c` (temperatura na koniec godziny).

**Ograniczenia wyniku:** to plan przy znanych z góry cenach i pogodzie dla budynku referencyjnego.
W prawdziwym domu oszczędność będzie inna (błędy prognozy, inne ocieplenie, inna moc grzejnika).
Poprawnie policzony plan nie gwarantuje takiej samej oszczędności w rzeczywistości.

## 6. Komunikaty błędów

| Komunikat | Przyczyna | Co zrobić |
|---|---|---|
| `Błąd: …: niepełna doba — brakujące godziny [2, …]` | w pliku brakuje godzin, są duplikaty albo luki | uzupełnij plik do 24 godzin 0..23 |
| `Błąd: …: wiersz N ma niepoprawną liczbę` | tekst albo przecinek zamiast liczby w danych | popraw wiersz N (liczby z kropką) |
| `Błąd: …: godzina H ma ujemne nasłonecznienie` | `solar_radiation_wm2` < 0 | sprawdź źródło danych |
| `Błąd: …: missing columns [...]` | brak wymaganej kolumny w nagłówku | dodaj kolumnę o dokładnej nazwie |
| `Błąd: plik … już istnieje — podaj nową nazwę` | `--out` wskazuje istniejący plik (program go nie nadpisze) | podaj inną nazwę pliku |
| `Błąd: plik wyniku nie może nadpisać pliku wejściowego` | `--out` = `--data` | podaj inny plik wyniku |
| `error: argument --t-min: wartość musi być skończoną liczbą` | `nan`, `inf` albo tekst w parametrze | podaj liczbę, np. `21.0` |
| `Błąd: t_min must not be greater than t_max` | dolna granica wyższa od górnej | zamień wartości |
| GUI: baner „Brak połączenia z API.” | nie działa `npm run api` | uruchom API i odśwież stronę |
| GUI: baner z opisem błędu (np. „t_min nie może być większe niż t_max”) | API odrzuciło ustawienia; stary plan jest ukrywany | popraw ustawienie wskazane w komunikacie |

Kod wyjścia CLI: 0 = sukces, 1 = błąd danych lub zapisu, 2 = błędny parametr wywołania.

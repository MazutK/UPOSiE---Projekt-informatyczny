# Projekt: optymalizator ogrzewania

Stan na 7 października 2026. Karta przedmiotu: `docs/Karta_projektu.docx`
(uzupełnić numer grupy i imiona).

## Co jest teraz

Monorepo z trzema warstwami:

| Ścieżka | Rola |
|---|---|
| `packages/core` | Silnik: model cieplny budynku, programowanie dynamiczne, termostat, przykładowe doby, CLI |
| `apps/api` | FastAPI: `GET /api/health`, `GET /api/scenarios`, `POST /api/optimize` |
| `apps/web` | React (Vite): panel parametrów, karty kosztów, wykresy, tabela godzinowa |
| `docker/` | Obrazy API (uvicorn) i GUI (nginx → `/api` na backend) |

GUI i API już się łączą. Na wbudowanych scenariuszach widać plan optymalny vs termostat,
koszt, kWh i oszczędność. Nie ma jeszcze danych z PSE, dodatkowych metod ani analizy wrażliwości.

## Jak to działa

Wejście: doba godzinowa (cena zł/kWh, temperatura na zewnątrz, nasłonecznienie W/m²)
plus pasmo komfortu `T_min`–`T_max` i temperatura startowa.

Model kroku 1 h:

```
T[t+1] = T[t] − α·(T[t] − T_zew[t]) + β·u[t − d] + γ·G[t] + c
```

Parametry (`parametry.json`) pochodzą z regresji na pomiarach **jednego budynku referencyjnego**.
`u` to decyzja 0/1 (grzać / nie), `d` to opóźnienie (domyślnie 2 h).

Dwa plany na tych samych danych:

1. **DP** — stan = temperatura (siatka 0,05 °C) + ostatnie `d` decyzji. Koszt leksykograficzny:
   najpierw dyskomfort (spadki poniżej `T_min`), potem pieniądze. Może nagrzać do
   `T_max + 1 °C` w tanich godzinach i przeczekać szczyt.
2. **Termostat** — włącza przy `T ≤ T_min`, wyłącza przy `T ≥ T_max`. Ceny ignoruje.

Wynik: harmonogram, temperatury, koszt, godziny poniżej `T_min`, oszczędność.

Format CSV (tego się nie zmienia w pojedynkę):

```
hour,price_pln_kwh,outside_temp_c,solar_radiation_wm2
```

Kontrakt HTTP: `apps/api/src/hems_api/schemas.py` i `apps/web/src/api/types.ts` — zmiana pól
w jednym commicie, po wpisie w tabeli decyzji poniżej.

## Co dodajemy dalej

Trzy rzeczy, żeby projekt spełniał wytyczne przedmiotu (dane publiczne, porównanie metod,
wsparcie decyzji), a nie został gołym GUI na syntetycznych CSV.

### 1. Dane publiczne (PSE + pogoda)

Wejście z prawdziwej doby: ceny godzinowe RCE (PSE) i pogoda (Open-Meteo), złożone do tego
samego CSV. Silnik się nie zmienia — dostaje te same kolumny.

Efekt: użytkownik wybiera datę, liczy się plan na realnych cenach, nie tylko na `doba_mroz`.

### 2. Porównanie metod

Obok DP i termostatu trzecia reguła, np. „grzej, gdy tanio i zimno”. Te same metryki:
zł, kWh, godziny poniżej `T_min`.

Efekt: da się uzasadnić DP liczbami (kiedy wygrywa, kiedy przy płaskiej cenie różnica zanika).

### 3. Analiza wrażliwości

Siatka parametrów, np. `T_min` albo `max_overshoot`, i wykres oszczędności.

Efekt: odpowiedź na pytanie „ile kosztuje cieplejsze pasmo?” — decyzja budżetowa, nie tylko
jeden plan na jedną dobę.

Czego nie robimy: kont, sklepu, CRUD, sterowania piecem na żywo, twierdzenia że model
opisuje każdy dom w Polsce.

## Roadmap — kto i w jakiej kolejności

Zasada: **jedna osoba = jeden zestaw folderów**. Cudzych plików nie refaktorujemy przy okazji.
Nowe feature’y idą do nowych katalogów. Osoba 1 w `App.tsx` tylko wstawia gotowy komponent.

### Krok 0 — wspólny start (wszyscy, 1 wieczór)

1. `docker compose up --build`, otworzyć http://localhost:8080, kliknąć scenariusze.
2. Przeczytać ten plik i kartę. Wpisać imiona przy Osobach 1–5.
3. Nie ruszamy `optimizer.py`, chyba że `pytest` nadal przechodzi.

### Krok 1 — widok działa na demo (osoby 1 i 2, równolegle)

**Osoba 1 — wynik (prawej kolumna GUI)**  
Pliki: `apps/web/src/App.tsx`, `features/charts/`, `features/summary/`, `styles/`, `components/Card.*`

- [ ] Układ desktop i wąski ekran
- [ ] Stany ładowania / błędu / braku danych przy wyniku
- [ ] Wykres temperatury (optymalizator, termostat, T_zew, pasmo komfortu)
- [ ] Wykres ceny i godzin grzania
- [ ] Karty: koszt, kWh, godziny poniżej T_min, oszczędność
- [ ] Tabela godzinowa

Odbiór: demo na `doba_szczyt_wieczorny`. Nie rusza API ani silnika.

**Osoba 2 — panel i klient HTTP**  
Pliki: `features/controls/`, `hooks/`, `api/`, `components/Field.*`

- [ ] Lista scenariuszy z `GET /api/scenarios`
- [ ] T_min, T_max, T_start, walidacja T_min ≤ T_max
- [ ] Przeliczanie po zmianie, bez migotania wykresów
- [ ] Komunikat, gdy API nie odpowiada
- [ ] Potem (nie blokuje 1): max_overshoot, wymuszenia godzin, wgranie CSV (pole dogadać z 3)

Odbiór: zmiana scenariusza / T_min zmienia liczby u Osoby 1. Nie rusza wykresów ani `optimizer.py`.

### Krok 2 — warstwa analityczna w Pythonie (osoby 3, 4, 5, równolegle do GUI)

Nie czekają na „gotowy design”. Najpierw kod + test, GUI na końcu.

**Osoba 3 — dane publiczne**  
Nowe: `packages/core/src/heating_optimizer/data_sources/`, `tests/test_data_sources.py`,
`apps/api` endpoint live, `apps/web/src/features/live-data/`

1. Parser RCE (PSE) → `price_pln_kwh` (test na zapisanej fixturze, bez sieci).
2. Parser Open-Meteo → `outside_temp_c`, `solar_radiation_wm2`.
3. Złożenie 24 wierszy CSV.
4. Endpoint, np. `GET /api/live?date=...` albo zapis scenariusza.
5. Jeden sprawdzony CSV w `packages/core/.../data/` do demo offline.
6. Mały widget: wybór daty. Wynik i tak leci przez istniejące `/api/optimize`.

Odbiór: data → plan. Parsera nie wpinamy w wykresy Osoby 1.

**Osoba 4 — porównanie metod**  
Nowe: `packages/core/src/heating_optimizer/baselines.py`, `tests/test_baselines.py`,
`POST /api/compare` (nie rozbijać `/optimize` bez zgody 2), `features/comparison/`

1. Owinąć istniejący termostat (nie kopiować).
2. Reguła zachłanna: grzej, gdy cena poniżej mediany i T blisko T_min.
3. Opcjonalnie trzecia: „utrzymuj T_min”, bez histerezy.
4. Wspólne metryki: koszt, kWh, godziny poniżej T_min, deficyt °C·h.
5. Tabela w GUI + 2–3 zdania: kiedy DP wygrywa, kiedy nie.

Odbiór: na szczycie wieczornym DP tańszy przy niegorszym komforcie. Nie zmienia `model.py`.

**Osoba 5 — wrażliwość i dokumentacja**  
Nowe: `packages/core/src/heating_optimizer/sensitivity.py`, `tests/test_sensitivity.py`,
`POST /api/sensitivity`, `features/sensitivity/`, ten plik i karta

1. Siatka np. T_min ∈ {20.5, 21.0, 21.5} albo max_overshoot ∈ {0, 0.5, 1.0}.
2. Dla każdej kombinacji: oszczędność zł i godziny poniżej T_min.
3. Tabela/wykres pod głównym widokiem + eksport CSV.
4. Imiona w karcie, numer grupy, kolejne wiersze w tabeli decyzji.
5. Ściągawka na demo: problem → dane → metoda → wynik.

Odbiór: widać liczbami, czy szersze pasmo zwiększa oszczędność. Nie pisze parsera PSE.

### Krok 3 — sklejenie (osoba 1 + autor feature’a)

Osoby 3/4/5 oddają komponent z własnego `features/...`. Osoba 1 dodaje import w `App.tsx`
pod istniejącymi wykresami (jedna linijka). Bez przebudowy layoutu „przy okazji”.

### Krok 4 — demo

`docker compose up --build`. Scenariusz syntetyczny, jedna doba z danych publicznych,
tabela metod, jedna siatka wrażliwości. Karta z imionami.

## Decyzje

Dopisujemy tutaj, nie tylko ustnie. Brak wiersza = decyzja nie obowiązuje.

| Data | Decyzja | Dlaczego |
|---|---|---|
| 2026-10-07 | Problem = najtańszy plan grzania przy cenach godzinowych, bez utraty komfortu | Realna decyzja, dane, model |
| 2026-10-07 | Metoda bazowa = DP + termostat | Porównanie metod; DP już jest i ma testy |
| 2026-10-07 | Monorepo: core / api / web | Równoległa praca bez mieszania silnika z GUI |
| 2026-10-07 | Uruchomienie przez Docker Compose (port 8080) | Ten sam start u każdego po klonie |
| 2026-10-07 | Model jako budynek referencyjny | Kalibracja z jednej pracy inżynierskiej |
| 2026-10-07 | MVP = silnik + API + widok na wbudowanych dobach | Publiczne dane i extra metody nie blokują demo |

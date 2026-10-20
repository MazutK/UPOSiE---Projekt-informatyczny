# Projekt: optymalizator ogrzewania

## 1. O czym jest projekt?

Wyobraź sobie dom z ogrzewaniem elektrycznym i taryfą, w której prąd co godzinę
ma inną cenę. Zwykły termostat nie patrzy na ceny. Włącza grzanie, gdy jest zimno,
i wyłącza, gdy jest ciepło. Przez to piec często chodzi wieczorem, kiedy prąd jest
najdroższy.

Ten projekt odpowiada na jedno pytanie:

> Kiedy przez najbliższe 24 godziny włączyć ogrzewanie, żeby w domu było ciepło,
> a rachunek był jak najniższy?

Aplikacja **nie steruje piecem na żywo**. To narzędzie do decyzji: dostaje dobę
(ceny + pogodę), liczy plan grzania i pokazuje, ile dałoby się zaoszczędzić
względem zwykłego termostatu.

**Dla kogo:** właściciel / najemca domu z ogrzewaniem elektrycznym i taryfą
dynamiczną.

**Co jest w zakresie:** plan na 24 godziny, ceny godzinowe, pogoda, porównanie
metod, koszt i komfort.

**Czego nie robimy:** kont użytkowników, sklepu, CRUD, sterowania urządzeniem,
automataki domowej, twierdzenia że model opisuje każdy dom w Polsce.
Model jest skalibrowany na **jednym budynku referencyjnym**.

Szerszy opis problemu: `docs/problem.md`. Źródła danych: `docs/data.md`.

---

## 2. Co znajduje się w projekcie obecnie i jak to działa?

### 2.1. Trzy warstwy, które już działają razem

To jest monorepo (jedno repo, kilka paczek). Całość już się łączy: klikasz
w przeglądarce, API woła silnik, wraca JSON, GUI rysuje wykresy.

| Warstwa | Ścieżka         | Co robi prostym językiem                                                                                                 |
| ------- | --------------- | ------------------------------------------------------------------------------------------------------------------------ |
| Silnik  | `packages/core` | Python. Wie, jak budynek stygnie i grzeje. Liczy najlepszy plan (DP) i plan termostatu. Ma przykładowe doby w CSV i CLI. |
| API     | `apps/api`      | FastAPI. Tłumaczy HTTP na wywołania silnika. Trzy endpointy: zdrowie, lista scenariuszy, optymalizacja.                  |
| GUI     | `apps/web`      | React (Vite). Panel parametrów po lewej, po prawej karty kosztów, wykresy i tabela godzinowa.                            |
| Docker  | `docker/`       | Składa API (uvicorn) i GUI (nginx). Nginx pod `/api` przekazuje ruch na backend.                                         |

Uruchomienie całego stosu:

```bash
docker compose up --build
```

Aplikacja: [http://localhost:8080](http://localhost:8080)

Bez Dockera (gdy ktoś pracuje nad kodem): patrz `README.md` — `npm run api`
i `npm run dev`, GUI na [http://localhost:5173](http://localhost:5173).

### 2.2. Co użytkownik widzi i klika (stan na dziś)

1. Otwiera GUI.
2. Wybiera **scenariusz doby** (gotowy CSV, np. mróz albo szczyt wieczorny).
3. Ustawia pasmo komfortu `T_min`–`T_max` i temperaturę startową.
4. GUI samo woła `POST /api/optimize`.
5. Dostaje dwa plany na tych samych danych: **optymalizator** i **termostat**.
6. Widzi oszczędność w zł, wykres temperatury, wykres ceny + godzin grzania
   oraz tabelę godzina po godzinie.

Czego jeszcze **nie ma** w GUI (silnik częściowo to umie, ekran nie):
dane z PSE/pogody na wybraną datę, trzecia metoda obok DP i termostatu,
analiza wrażliwości, wymuszenie „grzej o 7:00 niezależnie od optymalizacji”,
eksport planu do pliku.

### 2.3. Skąd biorą się dane wejściowe

Na razie **nie z internetu**. Są cztery wbudowane doby (pliki CSV):

| Scenariusz              | Co przedstawia                               |
| ----------------------- | -------------------------------------------- |
| `doba_zmienna_cena`     | łagodna zima, typowy przebieg cen (domyślny) |
| `doba_szczyt_wieczorny` | ostry szczyt cenowy 17–21                    |
| `doba_mroz`             | mróz do −10 °C                               |
| `doba_slonecznie`       | bezchmurny dzień zimowy                      |

Każdy wiersz = jedna godzina. **Tego formatu nie zmieniamy w pojedynkę:**

```
hour,price_pln_kwh,outside_temp_c,solar_radiation_wm2
```

Czyli: numer godziny, cena zł/kWh, temperatura na zewnątrz, nasłonecznienie W/m².

Parametry budynku są w `parametry.json` (regresja z pomiarów jednego domu).
Grzałka ma 1,5 kW. Opóźnienie `d` = 2 h: decyzja „grzej” zaczyna działać
na temperaturę dopiero po dwóch godzinach (bezwładność).

### 2.4. Model cieplny — co się dzieje co godzinę

Stan domu w godzinie `t` to temperatura wewnątrz `T[t]`.
Decyzja `u` to 0 albo 1 (nie grzej / grzej).

```
T[t+1] = T[t] − α·(T[t] − T_zew[t]) + β·u[t − d] + γ·G[t] + c
```

Po ludzku:

- im większa różnica między środkiem a zewnątrz, tym szybciej stygnie (`α`),
- grzanie podnosi temperaturę (`β`), ale z opóźnieniem `d`,
- słońce też trochę grzeje (`γ` · nasłonecznienie `G`),
- `c` to stała z kalibracji.

Pasmo komfortu: użytkownik chce `T_min`–`T_max`. Optymalizator może lekko
przekroczyć `T_max` (domyślnie +1 °C, `max_overshoot`), żeby nagrzać tanio
i przeczekać drogi szczyt.

### 2.5. Dwa plany, które już liczymy

Oba dostają **te same** ceny, pogodę, budynek i pasmo. Różnią się tylko regułą.

1. **DP (programowanie dynamiczne)** — „optymalizator”.
   Szuka najtańszego ciągu 24 decyzji 0/1. Stan to temperatura (siatka 0,05 °C)
   plus ostatnie `d` decyzji (żeby pamiętać opóźnienie).
   Koszt jest leksykograficzny: **najpierw** kara za zimno (spadki poniżej
   `T_min`), **potem** pieniądze. Nie poświęca komfortu, żeby zaoszczędzić złotówkę.

2. **Termostat** — baza do porównania.
   Włącza, gdy `T ≤ T_min`, wyłącza, gdy `T ≥ T_max`. **Ceny całkowicie ignoruje.**
   To jest „zwykły dom”, względem którego liczymy oszczędność.

Wynik obu: harmonogram (0/1 na każdą godzinę), temperatury, koszt, kWh,
godziny poniżej `T_min`, oszczędność zł i %.

### 2.6. Jak idzie request od kliknięcia do wykresu

```
Przeglądarka (React)
    │  POST /api/optimize  { scenario, t_min, t_max, t_start, ... }
    ▼
FastAPI  (apps/api)
    │  wczytuje CSV scenariusza + parametry budynku
    │  woła find_optimal_schedule(...)     → plan DP
    │  woła simulate_thermostat(...)       → plan termostatu
    ▼
JSON z wierszami godzinowymi + podsumowaniami
    ▼
GUI rysuje karty, wykresy, tabelę
```

Endpointy, które już są:

| Metoda | Ścieżka          | Po co                 |
| ------ | ---------------- | --------------------- |
| `GET`  | `/api/health`    | czy API żyje          |
| `GET`  | `/api/scenarios` | lista wbudowanych dób |
| `POST` | `/api/optimize`  | policz oba plany      |

Kontrakt (jakie pola wolno wysłać / wracają) jest w **dwóch** miejscach
i musi być zgodny:

- backend: `apps/api/src/hems_api/schemas.py`
- frontend: `apps/web/src/api/types.ts`

Zmiana pól = jeden commit, po wpisie w tabeli decyzji na dole tego pliku.
Nie ruszamy samego `optimizer.py`, chyba że `pytest` nadal przechodzi.

---

## 3. Jaka jest struktura plików? (co gdzie szukać)

Zasada: **nie szukaj po całym repo**. Każda warstwa ma swój folder.
Nowe rzeczy dokładamy jako **nowe pliki / nowe katalogi**, a nie
przerabiamy cudzych.

```
projekt si/
├── README.md                 ← jak uruchomić
├── docker-compose.yml        ← docker compose up --build
├── package.json              ← skrypty npm (dev, api, testy)
├── docs/                     ← ten plik, problem, dane, karta
├── docker/                   ← Dockerfile.api, Dockerfile.web, nginx.conf
├── packages/core/            ← SILNIK (Python)
├── apps/api/                 ← API (FastAPI)
└── apps/web/                 ← GUI (React)
```

### 3.1. Dokumentacja (`docs/`)

| Plik                  | Kiedy otworzyć                         |
| --------------------- | -------------------------------------- |
| `PROJEKT.md`          | ten plik — co robimy i kto co robi     |
| `problem.md`          | użytkownik, decyzja, wymagania         |
| `data.md`             | PSE, Open-Meteo, licencje              |
| `Karta_projektu.docx` | karta przedmiotu (imiona, numer grupy) |

### 3.2. Silnik (`packages/core/src/heating_optimizer/`)

Tu jest matematyka. Testy: `packages/core/tests/`.

| Plik                  | Co tam jest                                    |
| --------------------- | ---------------------------------------------- |
| `model.py`            | wzór na `T[t+1]`, opóźnienie, moc grzałki      |
| `optimizer.py`        | DP — `find_optimal_schedule`                   |
| `simulation.py`       | odtwórz temperatury z harmonogramu + termostat |
| `plan.py`             | wynik: harmonogram, koszty, kWh, deficyt       |
| `inputs.py`           | wczytanie CSV (kolumny, walidacja)             |
| `datasets.py`         | lista scenariuszy, `parametry.json`            |
| `cli.py`              | `python -m heating_optimizer` (bez GUI)        |
| `data/*.csv`          | cztery przykładowe doby                        |
| `data/parametry.json` | α, β, γ, delay, moc                            |

Jeśli chcesz **zmienić jak budynek stygnie** → `model.py`.
Jeśli chcesz **zmienić jak szukamy najtańszego planu** → `optimizer.py`
(ostrożnie, dużo testów).
Jeśli chcesz **dodać trzecią regułę** (np. „grzej gdy tanio”) → **nowy** plik
`baselines.py`, nie dopisuj tego w `optimizer.py`.

### 3.3. API (`apps/api/src/hems_api/`)

| Plik          | Co tam jest                            |
| ------------- | -------------------------------------- |
| `main.py`     | endpointy HTTP                         |
| `service.py`  | sklejenie: request → silnik → response |
| `schemas.py`  | kształt JSON-a (Pydantic)              |
| `settings.py` | CORS (localhost:5173 i :8080)          |

Testy: `apps/api/tests/test_api.py`.

Nowy endpoint = nowa funkcja w `main.py` + logika w `service.py` + schemat
w `schemas.py`. Istniejącego `/api/optimize` nie rozbijamy bez zgody osoby
od GUI / klienta HTTP.

### 3.4. GUI (`apps/web/src/`)

| Ścieżka                    | Co tam jest                                                                       |
| -------------------------- | --------------------------------------------------------------------------------- |
| `App.tsx`                  | układ strony: lewa kolumna + prawa kolumna. Tu tylko **wstawiamy** gotowe klocki. |
| `features/controls/`       | panel: scenariusz, T_min, T_max, T_start                                          |
| `features/charts/`         | wykres temperatury, wykres ceny i grzania                                         |
| `features/summary/`        | karty kosztów, tabela godzinowa                                                   |
| `hooks/useOptimization.ts` | pobierz scenariusze, wołaj `/optimize` przy zmianie ustawień                      |
| `api/client.ts`            | `fetch` do `/api/...`                                                             |
| `api/types.ts`             | te same pola co w `schemas.py`                                                    |
| `components/`              | `Card`, `Field` — wspólne cegiełki UI                                             |
| `styles/`                  | kolory, typografia, layout                                                        |

Nowy widok (porównanie metod, wrażliwość, eksport) = **nowy katalog**
`apps/web/src/features/nazwa/`. Osoba od layoutu w `App.tsx` dodaje jedną
linijkę importu. Nie przebudowujemy całej strony „przy okazji”.

### 3.5. Gdzie czego szukać — ściągawka

| Chcę…                            | Idę do…                                         |
| -------------------------------- | ----------------------------------------------- |
| zmienić wzór temperatury         | `packages/core/.../model.py`                    |
| zmienić DP                       | `packages/core/.../optimizer.py`                |
| dodać / poprawić CSV doby        | `packages/core/.../data/`                       |
| dodać pole w requeście HTTP      | `schemas.py` **i** `types.ts` razem             |
| zmienić karty / wykresy / tabelę | `apps/web/src/features/summary/` albo `charts/` |
| zmienić panel po lewej           | `features/controls/`                            |
| dodać nowy ekran                 | nowy `features/...` + import w `App.tsx`        |
| zmienić port / Docker            | `docker-compose.yml`, `docker/`                 |
| zrozumieć problem na ocenę       | `docs/problem.md`, `docs/data.md`               |

---

## 4. Co będziemy dalej robić?

MVP (silnik + API + GUI na wbudowanych CSV) **już jest**. Dokładamy cztery rzeczy. Trzy duże (dane publiczne, porównanie metod, wrażliwość) i jeden **mini-feature** (wymuszenia godzin + eksport planu + ściągawka na demo).

GUI na syntetycznych CSV samo w sobie nie wystarczy: potrzeba publicznych
danych, więcej niż dwóch metod i pytania „co jeśli zmienię T_min?”.

### 4.1. Dane publiczne (PSE + pogoda)

Wejście z prawdziwej doby: ceny godzinowe RCE z PSE i pogoda z Open-Meteo,
złożone do **tego samego** CSV (te same cztery kolumny). Silnik się nie
zmienia — dostaje te same pola.

Efekt: użytkownik wybiera datę, liczy się plan na realnych cenach, nie tylko
na `doba_mroz`.

### 4.2. Porównanie metod

Obok DP i termostatu trzecia reguła, np. „grzej, gdy tanio i zimno”.
Te same metryki: zł, kWh, godziny poniżej `T_min`.

Efekt: da się uzasadnić DP liczbami (kiedy wygrywa, kiedy przy płaskiej
cenie różnica zanika).

### 4.3. Analiza wrażliwości

Siatka parametrów, np. `T_min` albo `max_overshoot`, i wykres oszczędności.

Efekt: odpowiedź na pytanie „ile kosztuje cieplejsze pasmo?” — decyzja
budżetowa, nie tylko jeden plan na jedną dobę.

### 4.4. Mini-feature: wymuszenia godzin i eksport planu

Silnik **już umie** wymuszenia (`overrides`: „godzina 7 = na pewno grzej”).
API już przyjmuje to pole. GUI tego nie pokazuje. Szósta osoba robi:

- w GUI: zaznacz godziny, które mają być na sztywno włączone / wyłączone
  (np. „o 7:00 muszę mieć ciepło, bo wychodzę”),
- przycisk: pobierz aktualny plan jako CSV (ten, który widać na ekranie),
- ściągawkę na demo i imiona w karcie.

Efekt: użytkownik nie jest zakładnikiem optymalizatora — może wcisnąć swoje
ograniczenie i zabrać wynik ze sobą. To nadal wsparcie decyzji, nie nowy silnik.

Czego nadal nie robimy: kont, sklepu, sterowania piecem, wielu budynków.

---

## 5. Kto będzie robił daną rzecz i workflow krok po kroku

Zasada: **jedna osoba = jeden zestaw folderów**. Cudzych plików nie
refaktorujemy przy okazji. Nowe feature’y idą do nowych katalogów.
Osoba 1 w `App.tsx` tylko wstawia gotowy komponent.

Wpiszcie imiona (są też w `README.md`):

| Osoba | Imię | Odpowiada za                                      |
| ----- | ---- | ------------------------------------------------- |
| 1     | Sku  | prawa kolumna GUI (wynik)                         |
| 2     | Kma  | lewa kolumna GUI + klient HTTP                    |
| 3     | Owy  | dane publiczne PSE + Open-Meteo                   |
| 4     | Kba  | porównanie metod (trzecia reguła)                 |
| 5     | Sra  | analiza wrażliwości                               |
| 6     | Pum  | wymuszenia godzin, eksport CSV, karta i ściągawka |

Kolejność poniżej jest po to, żeby nikt na nikogo nie czekał tydzień.
Krok 1 i krok 2 idą **równolegle**. Potem sklejenie, potem demo.

---

### Krok 0 — wspólny start (wszyscy, jeden wieczór)

Cel: każdy ma działającą aplikację i wie, gdzie klikać.

1. Zainstalować Docker Desktop.
2. W katalogu repo: `docker compose up --build`.
3. Otworzyć http://localhost:8080.
4. Kliknąć wszystkie cztery scenariusze, zmienić `T_min`, zobaczyć że liczby
   i wykresy się zmieniają.
5. Przeczytać ten plik, `docs/problem.md` i kartę.
6. Wpisać imiona przy Osobach 1–6 w tabeli powyżej oraz w karcie.
7. Nie ruszamy `optimizer.py`, chyba że `pytest` nadal przechodzi.

Odbiór kroku 0: u każdego wstaje GUI, każdy wie którą osobą jest.

---

### Krok 1 — widok działa na demo (osoby 1 i 2, równolegle)

Nie czekacie na dane z PSE. Pracujecie na wbudowanych CSV.

#### Osoba 1 — wynik (prawa kolumna GUI)

**Twoje pliki:** `apps/web/src/App.tsx`, `features/charts/`, `features/summary/`,
`styles/`, `components/Card.*`

Czego nie ruszasz: API, silnika, panelu po lewej, `optimizer.py`.

Zrób to w tej kolejności:

1. Uruchom GUI (krok 0) i zobacz, co już jest: karty, dwa wykresy, tabela.
2. Dopnij układ: desktop (panel lewo, wynik prawo) i wąski ekran (jedna kolumna).
3. Stany prawej kolumny:
   - liczy (`Liczę plan…`),
   - błąd (API padło — komunikat, nie pusty ekran),
   - brak danych.
4. Wykres temperatury: optymalizator, termostat, T_zew, pasmo `T_min`–`T_max`.
5. Wykres ceny i godzin grzania (kiedy DP grzeje, kiedy termostat).
6. Karty: koszt, kWh, godziny poniżej `T_min`, oszczędność.
7. Tabela godzinowa (godzina, cena, obie decyzje, obie temperatury).
8. Sprawdź na scenariuszu `doba_szczyt_wieczorny` — tam różnica DP vs termostat
   jest najbardziej oczywista.

Odbiór: da się na demo pokazać wynik na wbudowanej dobie, czytelnie na laptopie
i na węższym oknie. Nie wołasz nowych endpointów.

#### Osoba 2 — panel i klient HTTP

**Twoje pliki:** `features/controls/`, `hooks/`, `api/`, `components/Field.*`

Czego nie ruszasz: wykresów Osoby 1, `optimizer.py`.

Zrób to w tej kolejności:

1. Lista scenariuszy z `GET /api/scenarios` (nie wpisuj nazw na sztywno).
2. Pola `T_min`, `T_max`, `T_start`. Walidacja: `T_min ≤ T_max`
   (jak użytkownik podbije min powyżej max, max też idzie w górę — tak jest dziś).
3. Każda zmiana pola od razu woła `/api/optimize` (tak jest w haku).
   Dopilnuj, żeby wykresy Osoby 1 nie migały przy każdym klawiszu
   (nie wysyłaj półwpisanego śmiecia; liczby z pól `NumberField` są OK).
4. Komunikat, gdy API nie odpowiada („Brak połączenia z API” już jest w kliencie —
   ma dojść do użytkownika, nie tylko do konsoli).
5. Pole `max_overshoot` (silnik i API już to mają, panel jeszcze nie).
   To nie blokuje Osoby 1.
6. Jeśli zmieniasz kształt JSON-a: edytujesz `api/types.ts` **i** dajesz znać
   osobie, która trzyma `schemas.py`. Jeden commit, wiersz w tabeli decyzji.

Odbiór: zmiana scenariusza albo `T_min` zmienia liczby i wykresy u Osoby 1.

---

### Krok 2 — warstwa analityczna i mini-feature (osoby 3, 4, 5, 6)

Nie czekacie na „gotowy design”. Najpierw kod + test w Pythonie.
GUI na końcu, jako własny katalog `features/...`.
Osoba 1 wstawi to do `App.tsx` w kroku 3.

Te cztery rzeczy są niezależne od siebie. Możecie iść równolegle.

#### Osoba 3 — dane publiczne

**Nowe pliki (nie edytujesz cudzych feature’ów):**

- `packages/core/src/heating_optimizer/data_sources/`
- `packages/core/tests/test_data_sources.py`
- endpoint live w `apps/api`
- `apps/web/src/features/live-data/`

Zrób to w tej kolejności:

1. Parser RCE (PSE) → kolumna `price_pln_kwh`.
   Test na **zapisanej fixturze** (plik z przykładową odpowiedzią), bez sieci
   na CI. Sieć tylko ręcznie.
2. Parser Open-Meteo → `outside_temp_c`, `solar_radiation_wm2`.
   Ten sam układ: fixture + test.
3. Złożenie 24 wierszy do formatu CSV z rozdziału 2.3.
   Jeśli którejś godziny brakuje — jasny błąd, nie cicha dziura.
4. Jeden sprawdzony CSV z prawdziwej doby wrzuć do
   `packages/core/src/heating_optimizer/data/` (demo offline, gdy PSE padnie).
5. Endpoint, np. `GET /api/live?date=YYYY-MM-DD`, albo zapis nowego scenariusza
   i potem zwykłe `/api/optimize`. **Nie wpinaj parsera w wykresy Osoby 1.**
6. Mały widget w `features/live-data/`: wybór daty, przycisk „pobierz dobę”.
   Wynik i tak leci przez istniejące `/api/optimize`.
7. Krótka notka w `docs/data.md`: data testu, skąd wzięte, co zrobić gdy API
   źródła nie odpowiada (plan awaryjny = wbudowany CSV z punktu 4).

Odbiór: wybieram datę → dostaję plan. Na demo działa też bez internetu
(zapisany CSV).

#### Osoba 4 — porównanie metod

**Nowe pliki:**

- `packages/core/src/heating_optimizer/baselines.py`
- `packages/core/tests/test_baselines.py`
- `POST /api/compare` (nie rozbijać `/optimize` bez zgody Osoby 2)
- `apps/web/src/features/comparison/`

Zrób to w tej kolejności:

1. Owinąć istniejący termostat z `simulation.py` — **nie kopiuj** tej funkcji.
2. Dodać regułę zachłanną: grzej, gdy cena jest poniżej mediany z doby
   **i** temperatura jest blisko `T_min`. (Dokładny próg zapisz w tym pliku
   w tabeli decyzji, jak ustalicie.)
3. Opcjonalnie trzecia: „utrzymuj `T_min`”, bez histerezy termostatu.
4. Wspólne metryki dla każdej metody: koszt zł, kWh, godziny poniżej `T_min`,
   deficyt °C·h (to już jest na `Plan`).
5. Test: na `doba_szczyt_wieczorny` DP jest tańszy przy niegorszym komforcie
   niż zachłanna i termostat.
6. Endpoint `POST /api/compare` zwraca tabelkę metod, nie surowe wykresy.
7. W GUI: tabela (i ewentualnie mały wykres słupkowy) + 2–3 zdania na ekranie:
   kiedy DP wygrywa, kiedy przy płaskiej cenie różnica zanika.

Czego nie ruszasz: `model.py`, wykresów Osoby 1.

Odbiór: na szczycie wieczornym widać liczbami, że DP jest tańszy i nie jest
zimniej. Na demo da się to powiedzieć bez zaglądania w kod.

#### Osoba 5 — analiza wrażliwości

**Nowe pliki:**

- `packages/core/src/heating_optimizer/sensitivity.py`
- `packages/core/tests/test_sensitivity.py`
- `POST /api/sensitivity`
- `apps/web/src/features/sensitivity/`

Zrób to w tej kolejności:

1. Ustal siatkę (wpisz w tabelę decyzji), np.
   `T_min ∈ {20.5, 21.0, 21.5}` albo `max_overshoot ∈ {0, 0.5, 1.0}`.
   Reszta parametrów stała (ten sam scenariusz, ten sam `T_max` / start).
2. Dla każdej kombinacji policz: oszczędność zł vs termostat oraz godziny
   poniżej `T_min`. Wywołuj istniejące `find_optimal_schedule` i
   `simulate_thermostat` — nie pisz drugiego DP.
3. Test: siatka 3 punktów zwraca 3 wiersze, liczby są skończone, kolejność
   parametru rosnąca.
4. Endpoint `POST /api/sensitivity` przyjmuje scenariusz + listę wartości.
5. W GUI pod głównym widokiem: tabela albo wykres oszczędności w funkcji
   parametru.
6. Przycisk eksportu tej tabeli do CSV (to jest wynik wrażliwości;
   eksport **planu godzinowego** robi Osoba 6 — nie dublujcie tego).

Czego nie ruszasz: parsera PSE, `model.py`.

Odbiór: widać liczbami, czy szersze / cieplejsze pasmo zwiększa oszczędność
i czy psuje komfort. Na pytanie „a jak obniżymy T_min o pół stopnia?”
jest wykres, nie zgadywanie.

#### Osoba 6 — wymuszenia godzin, eksport planu, karta i ściągawka

To jest celowo mniejszy kawałek niż 3/4/5, ale **widać go na demo**.
Silnik i API już przyjmują `overrides` (słownik `godzina → 0|1`).
GUI i dokumentacja końcowa — Twoje.

**Nowe / Twoje pliki:**

- `apps/web/src/features/overrides/` (albo analogiczna nazwa)
- `apps/web/src/features/export/` (może być jeden katalog `features/plan-tools/`)
- ten plik (`docs/PROJEKT.md`) i `docs/Karta_projektu.docx` — imiona, numer grupy
- krótka ściągawka demo, np. `docs/DEMO.md` (nowy plik, nie rozpychaj karty)

Czego nie ruszasz: `optimizer.py`, parsera PSE, wykresów (Osoba 1 je trzyma).
Wymuszenia idą **istniejącym** `POST /api/optimize` (pole `overrides`).
Nie dodawaj nowego endpointu, dopóki istniejący wystarcza.

Zrób to w tej kolejności:

1. Przeczytaj w `schemas.py` pole `overrides` i w `ControlsPanel` zobacz, że
   panel tego nie wysyła. Dogadaj z Osobą 2: albo dodajesz kontrolkę w swoim
   `features/overrides/` i podajesz `overrides` do tego samego stanu ustawień,
   albo Osoba 2 wystawia w haku miejsce na ten słownik, a Ty tylko UI.
   Nie edytuj całego panelu „przy okazji”.
2. UI: 24 komórki / lista godzin. Klikanie: bez wymuszenia → wymuś grzanie (1)
   → wymuś wyłączenie (0) → z powrotem bez wymuszenia.
   Po zmianie plan ma się przeliczyć (to samo `useOptimization`).
3. Sprawdź ręcznie: scenariusz `doba_szczyt_wieczorny`, wymuś grzanie o 18:00
   (drogi szczyt). Koszt ma wzrosnąć, w tabeli Osoby 1 godzina 18 ma być 1.
4. Przycisk „Pobierz plan CSV”: z aktualnego `OptimizeResponse` złóż plik
   (godzina, cena, decyzja DP, T DP, decyzja termostatu, T termostatu, koszt).
   To jest czysty frontend — nie trzeba Pythona.
5. Imiona i numer grupy w karcie. Kolejne wiersze w tabeli decyzji poniżej,
   gdy zespół coś ustali.
6. Ściągawka na demo, max 1 strona: problem → dane → metoda → wynik → gdzie
   kliknąć wymuszenie i eksport. Pięć zdań, które da się powiedzieć przy
   ekranie bez czytania kodu.

Odbiór: na demo widać „muszę grzać o 7:00” i da się ściągnąć CSV.
Karta ma imiona. Nie piszesz parsera i nie ruszasz DP.

---

### Krok 3 — sklejenie (osoba 1 + autor feature’a)

Osoby 3, 4, 5 i 6 oddają **gotowy komponent** ze swojego `features/...`.
Osoba 1 dodaje import w `App.tsx` pod istniejącymi wykresami (jedna linijka
na feature). Bez przebudowy layoutu „przy okazji”.

Kolejność wstawiania na stronę (żeby demo miało sens od góry):

1. To, co już jest: karty, temperatura, cena, tabela.
2. Widget daty (Osoba 3) — albo zostaje w lewym panelu, jeśli tak dogadacie z 2.
3. Wymuszenia (Osoba 6) — blisko panelu / nad tabelą.
4. Tabela metod (Osoba 4).
5. Wykres wrażliwości (Osoba 5).
6. Przycisk eksportu planu (Osoba 6).

Jeśli komponent nie mieści się w układzie, poprawia to Osoba 1 razem z autorem,
nie cała szóstka naraz.

---

### Krok 4 — demo (wszyscy)

1. `docker compose up --build`.
2. Scenariusz syntetyczny (`doba_szczyt_wieczorny`) — widać DP vs termostat.
3. Jedna doba z danych publicznych (albo zapisany CSV Osoby 3, gdy sieć padnie).
4. Tabela metod (Osoba 4).
5. Jedna siatka wrażliwości (Osoba 5).
6. Jedno wymuszenie godziny + pobrany CSV (Osoba 6).
7. Karta z imionami i numerem grupy.

Kto co mówi przy ekranie — według ściągawki Osoby 6. Nie improwizujemy
z kodem na żywo.

---

## 6. Decyzje

Dopisujemy tutaj, nie tylko ustnie. Brak wiersza = decyzja nie obowiązuje.

| Data       | Decyzja                                                                                                                 | Dlaczego                                                          |
| ---------- | ----------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------- |
| 2026-10-07 | Problem = najtańszy plan grzania przy cenach godzinowych, bez utraty komfortu                                           | Realna decyzja, dane, model                                       |
| 2026-10-07 | Metoda bazowa = DP + termostat                                                                                          | Porównanie metod; DP już jest i ma testy                          |
| 2026-10-07 | Monorepo: core / api / web                                                                                              | Równoległa praca bez mieszania silnika z GUI                      |
| 2026-10-07 | Uruchomienie przez Docker Compose (port 8080)                                                                           | Ten sam start u każdego po klonie                                 |
| 2026-10-07 | Model jako budynek referencyjny                                                                                         | Kalibracja z jednej pracy inżynierskiej                           |
| 2026-10-07 | MVP = silnik + API + widok na wbudowanych dobach                                                                        | Publiczne dane i extra metody nie blokują demo                    |
| 2026-10-19 | wymuszenia godzin + eksport planu + kartę/ściągawkę                                                                     | Silnik już ma `overrides`; GUI i dokumentacja końcowa były dziurą |
| 2026-10-19 | Nowe feature’y (live data, compare, sensitivity, overrides/export) = nowe katalogi, sklejenie w `App.tsx` przez Osobę 1 | Żeby nikt nie nadpisywał cudzego layoutu                          |

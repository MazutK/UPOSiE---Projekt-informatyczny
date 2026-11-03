# Optymalizator ogrzewania

Najtańszy plan grzania przy zmiennych cenach energii, porównany z termostatem.

Opis projektu, jak działa silnik i podział pracy zespołu: [`docs/PROJEKT.md`](docs/PROJEKT.md).

## Linki

- [Opis problemu](docs/problem.md)
- [Analiza danych](docs/data.md)

## Uruchomienie

Potrzebny jest [Docker Desktop](https://www.docker.com/products/docker-desktop/).

```bash
docker compose up --build
```

Aplikacja: [http://localhost:8080](http://localhost:8080)

Zatrzymanie: `Ctrl+C`, potem `docker compose down`.

## Uruchomienie bez Dockera (praca nad kodem)

Python 3.10+ i Node 20+.

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-dev.txt
npm install

npm run api
npm run dev
```

GUI: [http://localhost:5173](http://localhost:5173)


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
```bash
python -m pip install -r requirements.txt
python scripts/prepare_data.py data/raw/pse-rce-sample.json data/raw/open-meteo-sample.json data/processed/doba-live.csv
python scripts/check_data.py data/processed/doba-live.csv
```
## Porównanie metod (Lab 4)
Pytanie, źródła, warunki, wyniki i ograniczenia: [`docs/experiment.md`](docs/experiment.md).
Wariant bazowy = termostat, metoda = plan DP. Te same dane: `data/processed/doba-live.csv` (Lab 3).
Brak nowych pakietów — wystarczy `requirements.txt`. Brak losowania (ziarno niepotrzebne).

```bash
python -m venv .venv
# Windows: .\.venv\Scripts\Activate.ps1   |   Linux/macOS: source .venv/bin/activate
python -c "import sys; print(sys.executable)"   # ma wskazywać .venv
python -m pip install -r requirements.txt

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
wrażliwość: 11,39 zł vs 7,28 zł (−36,1 %). Po ponownym uruchomieniu `git status results/` nie pokazuje zmian.

Demo z instrukcji (opcjonalnie): `python examples/lab4/compare_forecasts.py examples/lab4/data/popyt.csv examples/lab4/results/okno3 --window 3`

## Projekt architektury (Lab 5)
Granice, UC-01, kontrakt, model danych, diagramy i przegląd: [`docs/architecture.md`](docs/architecture.md).
Decyzja o zapisie: [`docs/decisions/001-storage.md`](docs/decisions/001-storage.md). Diagramy: `docs/diagrams/`.

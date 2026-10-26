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

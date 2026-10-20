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

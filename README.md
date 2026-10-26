# Trace — API Observability MVP

A lightweight API monitoring service built with **FastAPI**, **SQLAlchemy**, and **PostgreSQL**. Automatically records endpoint requests, HTTP status codes, and response latency, then exposes aggregate metrics endpoints.

## Run with Docker

```bash
docker compose up --build
```

Open http://localhost:8000/docs and try `GET /demo/42`, `GET /metrics/summary`, and `GET /metrics/endpoints`.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Local mode defaults to SQLite; Docker Compose uses PostgreSQL.

## Tests

```bash
pytest -q
```

## Architecture

FastAPI middleware measures request durations, stores each request in the database, and makes aggregated counts and average latency available through REST endpoints. `/metrics` calls are excluded from collection to avoid self-inflating metrics. This is an MVP, not a production monitoring system: authentication, batching, retention, tracing, percentiles, dashboards, and load testing are future enhancements.

## Next steps

- React/TypeScript dashboard with charts
- Endpoint latency percentiles and time-window filters
- Asynchronous/batched metric writes
- Load testing and reproducible performance measurements
- Auth and metrics retention

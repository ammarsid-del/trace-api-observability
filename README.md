# Trace — API Observability Platform

A full-stack **API monitoring MVP** with a React/TypeScript dashboard, FastAPI request instrumentation, and PostgreSQL metrics storage. Built to explore API performance, monitoring, and backend engineering.

## Tech stack

- **Frontend:** React, TypeScript, Vite, CSS, SVG charts
- **Backend:** Python, FastAPI, SQLAlchemy
- **Database:** PostgreSQL with Docker Compose; SQLite fallback for local Python development
- **Quality:** Pytest, GitHub Actions (backend tests and frontend build)

## Quick start

Requires Docker and Docker Compose.

```bash
git clone https://github.com/ammarsid-del/trace-api-observability.git
cd trace-api-observability
docker compose up --build
```

- Dashboard: http://localhost:5173
- FastAPI docs: http://localhost:8000/docs
- Health endpoint: http://localhost:8000/health

Generate example traffic:

```bash
for i in $(seq 1 25); do curl -s http://localhost:8000/demo/$i > /dev/null; done
```

Refresh the dashboard to see collected requests.

## API

| Endpoint | Purpose |
| --- | --- |
| `GET /health` | Health check |
| `GET /demo/{item_id}` | Sample instrumented route |
| `GET /metrics/summary?hours=24` | Request count, average latency, 5xx errors, error rate |
| `GET /metrics/endpoints?hours=24` | Per-route request counts, latency, errors |
| `GET /metrics/timeseries?hours=24` | Hourly request counts |

Supported time windows: 1–720 hours. Dashboard offers 1 hour, 24 hours, and 7 days.

## Develop locally

Backend:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Frontend in another terminal:

```bash
cd frontend
npm install
npm run dev
```

## Run checks

```bash
pytest -q
cd frontend && npm install && npm run build
```

GitHub Actions runs both checks on pushes and pull requests.

## Architecture and limitations

FastAPI middleware measures response time and records the request path, method, status, and duration. PostgreSQL stores the events; aggregate endpoints power the React dashboard. Metrics routes are excluded to avoid self-inflating request statistics.

**This is an MVP, not a production-grade observability service.** Each monitored request currently performs a synchronous database write; high-volume traffic would require buffered asynchronous ingestion. The service also lacks authentication, data retention policies, distributed tracing, and production deployment. The hourly series returns only buckets with data, and the UI currently uses an SVG chart without a charting library.

## Next milestones

- Add p50/p95/p99 latency and time-window trend charts
- Add integration tests against PostgreSQL
- Add buffered ingestion and load-test benchmarks
- Deploy backend and frontend; capture screenshots and a demo

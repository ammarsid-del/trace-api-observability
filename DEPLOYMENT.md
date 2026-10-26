# Deploy Trace (Render API + Vercel dashboard)

Trace currently runs locally. A public deployment needs **three** services:
1. A managed PostgreSQL database
2. A FastAPI web service on Render
3. A Vite/React static frontend on Vercel

Never put a database password or API secret in GitHub or in a `VITE_*` variable.

## 1. Database

In Render, create a PostgreSQL database. Copy its **internal** connection URL for use by a Render web service in the same region. Use a URL that starts with `postgresql://` or `postgresql+psycopg://`; the API uses psycopg v3, so if the provided URL begins `postgresql://`, change only that prefix to `postgresql+psycopg://` when setting the environment variable.

Review Render's current plan pricing and availability before provisioning.

## 2. API service

Render > New > Web Service > connect `ammarsid-del/trace-api-observability`.

- Branch: `main`
- Runtime: Python
- Root directory: repository root
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Health check path: `/health`
- Environment: `DATABASE_URL` = your database connection URL
- Environment: `CORS_ORIGINS` = the HTTPS domain of your deployed Vercel frontend (set after creating it)

Do not deploy using the current local SQLite fallback: ephemeral disks can lose metrics between restarts.

Once deployed, confirm `https://YOUR-API.onrender.com/health` returns `{"status":"ok"}`.

## 3. Dashboard

Vercel > Add New > Project > import the same GitHub repository.

- Root directory: `frontend`
- Framework preset: Vite
- Build command: `npm run build`
- Output directory: `dist`
- Environment variable: `VITE_API_URL` = `https://YOUR-API.onrender.com` (no trailing slash)

Deploy, copy the Vercel production URL, and set Render's `CORS_ORIGINS` to that exact origin. Redeploy the API if necessary.

**Important:** Vite embeds `VITE_API_URL` at build time; changing it requires a new frontend deployment.

## 4. Verify

- Visit your Vercel URL
- Open your API docs and send a demo request to `GET /demo/42`
- Refresh the dashboard
- Confirm counts and latency percentiles update
- Verify no CORS errors in the browser console

## 5. Benchmark locally (not against hosted services)

```bash
python3 scripts/benchmark.py --url http://localhost:8000/demo/42 --requests 500 --concurrency 10
```

Run at least three trials. Record environment, configuration, sample size, and all results before writing any performance claim on a resume.

## Security and scale notes

The API is a portfolio MVP with unauthenticated metrics endpoints and a public demo route. Never send real user data, tokens, or private paths to this public demo. Do not use this service to monitor private production applications without adding authentication, authorization, retention policies, and request-path sanitization. Metrics currently use one synchronous database write per request, so throughput is limited.

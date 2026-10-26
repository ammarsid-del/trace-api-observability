"""Trace: a small, inspectable API observability service."""
import os
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, func, select, case
from sqlalchemy.orm import DeclarativeBase, Session
from fastapi import FastAPI, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from app.stats import latency_percentiles

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./trace.db")
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
    pool_pre_ping=True,
)

class Base(DeclarativeBase):
    pass

class RequestMetric(Base):
    __tablename__ = "request_metrics"
    id = Column(Integer, primary_key=True)
    path = Column(String(300), nullable=False, index=True)
    method = Column(String(12), nullable=False)
    status_code = Column(Integer, nullable=False)
    duration_ms = Column(Float, nullable=False)
    recorded_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    yield

app = FastAPI(title="Trace API Observability", version="0.2.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:5173").split(","),
    allow_methods=["GET"],
    allow_headers=["*"],
)

@app.middleware("http")
async def collect_metrics(request: Request, call_next):
    start = time.perf_counter()
    status = 500
    try:
        response = await call_next(request)
        status = response.status_code
        return response
    finally:
        duration = (time.perf_counter() - start) * 1000
        if not request.url.path.startswith("/metrics") and request.url.path not in ("/docs", "/openapi.json"):
            with Session(engine) as session:
                session.add(RequestMetric(
                    path=request.url.path[:300], method=request.method,
                    status_code=status, duration_ms=duration,
                ))
                session.commit()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/demo/{item_id}")
def demo(item_id: int):
    return {"item_id": item_id, "message": "Example instrumented endpoint"}

@app.get("/metrics/summary")
def metrics_summary(hours: int = Query(default=24, ge=1, le=720)):
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    with Session(engine) as session:
        total, avg_ms, errors = session.execute(
            select(
                func.count(RequestMetric.id),
                func.avg(RequestMetric.duration_ms),
                func.sum(case((RequestMetric.status_code >= 500, 1), else_=0)),
            ).where(RequestMetric.recorded_at >= cutoff)
        ).one()
        latencies = session.scalars(select(RequestMetric.duration_ms).where(RequestMetric.recorded_at >= cutoff)).all()
        return {
            **latency_percentiles(latencies),
            "requests": total,
            "average_latency_ms": round(avg_ms or 0, 2),
            "server_errors": errors or 0,
            "error_rate_percent": round((errors or 0) * 100 / total, 2) if total else 0,
            "window_hours": hours,
        }

@app.get("/metrics/endpoints")
def metrics_endpoints(hours: int = Query(default=24, ge=1, le=720)):
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    with Session(engine) as session:
        rows = session.execute(
            select(RequestMetric.path, RequestMetric.method,
                   func.count(RequestMetric.id), func.avg(RequestMetric.duration_ms),
                   func.sum(case((RequestMetric.status_code >= 500, 1), else_=0)))
            .where(RequestMetric.recorded_at >= cutoff)
            .group_by(RequestMetric.path, RequestMetric.method)
            .order_by(func.count(RequestMetric.id).desc())
        ).all()
        result = []
        for path, method, count, avg, errors in rows:
            latencies = session.scalars(
                select(RequestMetric.duration_ms).where(
                    RequestMetric.recorded_at >= cutoff,
                    RequestMetric.path == path,
                    RequestMetric.method == method,
                )
            ).all()
            result.append({
                **latency_percentiles(latencies),
                "path": path, "method": method, "requests": count,
                "average_latency_ms": round(avg or 0, 2), "server_errors": errors or 0,
            })
        return result

@app.get("/metrics/timeseries")
def metrics_timeseries(hours: int = Query(default=24, ge=1, le=720)):
    """Return per-hour request counts. Bucketing in Python keeps SQLite/Postgres compatible."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    with Session(engine) as session:
        stamps = session.scalars(
            select(RequestMetric.recorded_at)
            .where(RequestMetric.recorded_at >= cutoff)
            .order_by(RequestMetric.recorded_at)
        ).all()
    counts = {}
    for stamp in stamps:
        bucket = stamp.replace(minute=0, second=0, microsecond=0)
        key = bucket.isoformat()
        counts[key] = counts.get(key, 0) + 1
    return [{"hour": hour, "requests": count} for hour, count in sorted(counts.items())]

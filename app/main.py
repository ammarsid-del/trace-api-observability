"""Trace: lightweight API request monitoring MVP."""
import os
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, func, select, case
from sqlalchemy.orm import DeclarativeBase, Session
from fastapi import FastAPI, Request

DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./trace.db')
engine = create_engine(DATABASE_URL, connect_args={'check_same_thread': False} if DATABASE_URL.startswith('sqlite') else {}, pool_pre_ping=True)

class Base(DeclarativeBase):
    pass

class RequestMetric(Base):
    __tablename__ = 'request_metrics'
    id = Column(Integer, primary_key=True)
    path = Column(String(300), nullable=False, index=True)
    method = Column(String(12), nullable=False)
    status_code = Column(Integer, nullable=False)
    duration_ms = Column(Float, nullable=False)
    recorded_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    yield

app = FastAPI(title='Trace API Observability', version='0.1.0', lifespan=lifespan)

@app.middleware('http')
async def collect_metrics(request: Request, call_next):
    start = time.perf_counter()
    status = 500
    try:
        response = await call_next(request)
        status = response.status_code
        return response
    finally:
        duration = (time.perf_counter() - start) * 1000
        # Skip metrics endpoints to avoid monitoring requests changing their own statistics.
        if not request.url.path.startswith('/metrics'):
            with Session(engine) as session:
                session.add(RequestMetric(path=request.url.path[:300], method=request.method,
                    status_code=status, duration_ms=duration))
                session.commit()

@app.get('/health')
def health():
    return {'status': 'ok'}

@app.get('/demo/{item_id}')
def demo(item_id: int):
    return {'item_id': item_id, 'message': 'Example instrumented endpoint'}

@app.get('/metrics/summary')
def metrics_summary():
    with Session(engine) as session:
        total, avg_ms, errors = session.execute(select(func.count(RequestMetric.id), func.avg(RequestMetric.duration_ms),
            func.sum(case((RequestMetric.status_code >= 500, 1), else_=0)))).one()
        return {'requests': total, 'average_latency_ms': round(avg_ms or 0, 2), 'server_errors': errors or 0}

@app.get('/metrics/endpoints')
def metrics_endpoints():
    with Session(engine) as session:
        rows = session.execute(select(RequestMetric.path, RequestMetric.method,
            func.count(RequestMetric.id), func.avg(RequestMetric.duration_ms))
            .group_by(RequestMetric.path, RequestMetric.method)
            .order_by(func.count(RequestMetric.id).desc())).all()
        return [{'path': p, 'method': m, 'requests': n, 'average_latency_ms': round(ms, 2)} for p, m, n, ms in rows]

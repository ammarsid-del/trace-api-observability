from app.stats import percentile, latency_percentiles

def test_nearest_rank_percentiles():
    values = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    assert percentile(values, 50) == 50
    assert percentile(values, 95) == 100
    assert percentile(values, 99) == 100
    assert percentile([3, 1, 2], 50) == 2
    assert percentile([], 95) == 0
    assert latency_percentiles([1, 2, 3]) == {
        "p50_latency_ms": 2,
        "p95_latency_ms": 3,
        "p99_latency_ms": 3,
    }

def test_percentile_invalid_input():
    try:
        percentile([1, 2], 101)
        assert False, "Expected ValueError"
    except ValueError:
        pass

from fastapi.testclient import TestClient
from app.main import app

def test_api_exposes_latency_percentiles():
    with TestClient(app) as client:
        assert client.get("/demo/10").status_code == 200
        summary = client.get("/metrics/summary").json()
        assert summary["p50_latency_ms"] >= 0
        assert summary["p95_latency_ms"] >= summary["p50_latency_ms"]
        assert summary["p99_latency_ms"] >= summary["p95_latency_ms"]
        endpoints = client.get("/metrics/endpoints").json()
        assert all("p95_latency_ms" in row for row in endpoints)

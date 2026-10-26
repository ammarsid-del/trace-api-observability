from fastapi.testclient import TestClient
from app.main import app

def test_metrics_endpoints_and_windows():
    with TestClient(app) as client:
        assert client.get("/demo/1").status_code == 200
        assert client.get("/demo/not-a-number").status_code == 422
        summary = client.get("/metrics/summary?hours=24")
        assert summary.status_code == 200
        body = summary.json()
        assert body["requests"] >= 2
        assert body["window_hours"] == 24
        assert 0 <= body["error_rate_percent"] <= 100
        endpoints = client.get("/metrics/endpoints?hours=24")
        assert endpoints.status_code == 200
        assert any(x["path"] == "/demo/1" for x in endpoints.json())
        timeseries = client.get("/metrics/timeseries?hours=24")
        assert timeseries.status_code == 200
        assert isinstance(timeseries.json(), list)

def test_invalid_time_window():
    with TestClient(app) as client:
        assert client.get("/metrics/summary?hours=0").status_code == 422
        assert client.get("/metrics/endpoints?hours=721").status_code == 422

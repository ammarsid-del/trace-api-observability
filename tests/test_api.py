from fastapi.testclient import TestClient
from app.main import app

def test_request_metrics():
    with TestClient(app) as client:
        assert client.get('/health').status_code == 200
        assert client.get('/demo/42').json()['item_id'] == 42
        summary = client.get('/metrics/summary')
        assert summary.status_code == 200
        assert summary.json()['requests'] >= 2
        endpoints = client.get('/metrics/endpoints').json()
        assert any(e['path'] == '/demo/42' for e in endpoints)

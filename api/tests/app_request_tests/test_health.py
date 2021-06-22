from fastapi.testclient import TestClient

from api.app import app


def test_health(redis_db):
    client = TestClient(app)
    response = client.get("/health")
    assert response.json() == {
        "running": True,
        "service_status": [
            {"is_healthy": True, "message": "ping succeeded", "service": "redis"},
            {"is_healthy": False, "message": "Could not perform test call.", "service": "rvig"},
        ],
    }

import pytest
from fastapi.testclient import TestClient

from api.app import app


def test_unhealth():
    client = TestClient(app)

    with pytest.raises(RuntimeError):
        response = client.get("/unhealth")

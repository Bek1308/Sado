from fastapi.testclient import TestClient

from sado.main import create_app


def test_health_reports_ok_with_app_identity() -> None:
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "name": "Sado", "version": "0.1.0"}

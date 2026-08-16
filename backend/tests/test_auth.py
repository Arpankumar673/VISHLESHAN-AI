from uuid import uuid4
from fastapi.testclient import TestClient


def test_unauthenticated_request_rejected(unauth_client: TestClient):
    random_id = uuid4()
    response = unauth_client.get(f"/api/v1/companies/{random_id}")
    assert response.status_code == 401
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "UNAUTHENTICATED"


def test_malformed_auth_header_rejected(unauth_client: TestClient):
    random_id = uuid4()
    response = unauth_client.get(
        f"/api/v1/companies/{random_id}",
        headers={"Authorization": "InvalidTokenWithoutBearer"},
    )
    assert response.status_code == 401
    data = response.json()
    assert data["error"]["code"] == "UNAUTHENTICATED"


def test_authenticated_request_accepted(client: TestClient):
    # With client fixture (dependency override), protected route should pass auth
    random_id = uuid4()
    response = client.get(f"/api/v1/companies/{random_id}")
    # Passes auth, returns 404 because company does not exist
    assert response.status_code == 404
    data = response.json()
    assert data["error"]["code"] == "NOT_FOUND"

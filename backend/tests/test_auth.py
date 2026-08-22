import time
from uuid import uuid4
import pytest
import jwt
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
from fastapi.testclient import TestClient
from app.core.security import get_current_user, AuthenticatedUser, ALLOWED_ALGORITHMS
from app.core.errors import AuthenticationError


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


@pytest.mark.asyncio
async def test_get_current_user_missing_header():
    with pytest.raises(AuthenticationError, match="Authorization header is missing"):
        await get_current_user(None)


@pytest.mark.asyncio
async def test_get_current_user_malformed_header():
    with pytest.raises(AuthenticationError, match="Malformed Authorization header"):
        await get_current_user("Basic dXNlcjpwYXNz")


@pytest.mark.asyncio
async def test_get_current_user_invalid_algorithm_rejection():
    import base64
    import json

    header = base64.urlsafe_b64encode(json.dumps({"alg": "RS512", "typ": "JWT"}).encode()).decode().rstrip("=")
    payload = base64.urlsafe_b64encode(json.dumps({"sub": str(uuid4()), "exp": int(time.time()) + 3600}).encode()).decode().rstrip("=")
    signature = base64.urlsafe_b64encode(b"fakesignature").decode().rstrip("=")
    invalid_token = f"{header}.{payload}.{signature}"

    with pytest.raises(AuthenticationError, match="The specified alg value 'RS512' is not allowed"):
        await get_current_user(f"Bearer {invalid_token}")


@pytest.mark.asyncio
async def test_get_current_user_hs256_valid_token(monkeypatch):
    secret = "test-secret-key-12345"
    monkeypatch.setattr("app.core.config.settings.SUPABASE_JWT_SECRET", secret)

    user_id = str(uuid4())
    payload = {
        "sub": user_id,
        "email": "testuser@example.com",
        "role": "authenticated",
        "exp": int(time.time()) + 3600,
    }
    token = jwt.encode(payload, secret, algorithm="HS256")

    user = await get_current_user(f"Bearer {token}")
    assert isinstance(user, AuthenticatedUser)
    assert str(user.id) == user_id
    assert user.email == "testuser@example.com"
    assert user.role == "authenticated"


@pytest.mark.asyncio
async def test_get_current_user_hs256_invalid_signature(monkeypatch):
    secret = "correct-secret"
    monkeypatch.setattr("app.core.config.settings.SUPABASE_JWT_SECRET", secret)

    user_id = str(uuid4())
    wrong_token = jwt.encode({"sub": user_id, "exp": int(time.time()) + 3600}, "wrong-secret", algorithm="HS256")

    with pytest.raises(AuthenticationError, match="Invalid authentication token"):
        await get_current_user(f"Bearer {wrong_token}")


@pytest.mark.asyncio
async def test_get_current_user_expired_token(monkeypatch):
    secret = "test-secret"
    monkeypatch.setattr("app.core.config.settings.SUPABASE_JWT_SECRET", secret)

    user_id = str(uuid4())
    expired_payload = {
        "sub": user_id,
        "exp": int(time.time()) - 3600,
    }
    expired_token = jwt.encode(expired_payload, secret, algorithm="HS256")

    with pytest.raises(AuthenticationError, match="Authentication token has expired"):
        await get_current_user(f"Bearer {expired_token}")


@pytest.mark.asyncio
async def test_get_current_user_es256_valid_token(monkeypatch):
    # Generate real EC key pair for ES256 testing
    private_key = ec.generate_private_key(ec.SECP256R1())
    public_key = private_key.public_key()

    user_id = str(uuid4())
    payload = {
        "sub": user_id,
        "email": "es256user@example.com",
        "role": "authenticated",
        "exp": int(time.time()) + 3600,
    }
    token = jwt.encode(payload, private_key, algorithm="ES256", headers={"kid": "test-key-id"})

    # Mock PyJWKClient to return the public key
    class MockSigningKey:
        key = public_key

    class MockJWKSClient:
        def get_signing_key_from_jwt(self, _token):
            return MockSigningKey()

    monkeypatch.setattr("app.core.security.get_jwks_client", lambda: MockJWKSClient())

    user = await get_current_user(f"Bearer {token}")
    assert isinstance(user, AuthenticatedUser)
    assert str(user.id) == user_id
    assert user.email == "es256user@example.com"
    assert user.role == "authenticated"


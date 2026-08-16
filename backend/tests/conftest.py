import uuid
from typing import Generator
import pytest
from fastapi.testclient import TestClient
from app.core.security import AuthenticatedUser, get_current_user
from app.main import app

TEST_USER_ID = uuid.uuid4()
OTHER_USER_ID = uuid.uuid4()


@pytest.fixture
def mock_user() -> AuthenticatedUser:
    return AuthenticatedUser(
        id=TEST_USER_ID,
        email="researcher@vishleshan.ai",
        role="user",
    )


@pytest.fixture
def other_user() -> AuthenticatedUser:
    return AuthenticatedUser(
        id=OTHER_USER_ID,
        email="other@vishleshan.ai",
        role="user",
    )


@pytest.fixture
def client(mock_user: AuthenticatedUser) -> Generator[TestClient, None, None]:
    app.dependency_overrides[get_current_user] = lambda: mock_user
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def unauth_client() -> Generator[TestClient, None, None]:
    app.dependency_overrides.clear()
    with TestClient(app) as test_client:
        yield test_client

from datetime import datetime, timezone
from uuid import uuid4
from fastapi.testclient import TestClient
from app.core.errors import AuthorizationError, NotFoundError
from app.core.security import AuthenticatedUser, get_current_user
from app.main import app
from app.schemas.research import (
    ResearchRunResponse,
    ResearchStatus,
    StartResearchResponse,
)
from app.services.research_service import get_research_service


class MockResearchService:
    def __init__(self, owner_id):
        self.owner_id = owner_id
        self.sample_run_id = uuid4()
        self.sample_company_id = uuid4()

    def start_research(self, user_id, company_name, company_url=None):
        return StartResearchResponse(
            research_run_id=self.sample_run_id,
            company_id=self.sample_company_id,
            status=ResearchStatus.QUEUED,
        )

    def get_research_status(self, run_id, user_id):
        if run_id != self.sample_run_id:
            raise NotFoundError(f"Research run with ID {run_id} not found")
        if user_id != self.owner_id:
            raise AuthorizationError("You do not have access to this research run")
        now = datetime.now(timezone.utc)
        return ResearchRunResponse(
            research_run_id=self.sample_run_id,
            company_id=self.sample_company_id,
            user_id=self.owner_id,
            status=ResearchStatus.QUEUED,
            created_at=now,
            updated_at=now,
        )


def test_start_research_validation_empty_name(client: TestClient):
    response = client.post("/api/v1/research", json={"company_name": ""})
    assert response.status_code == 422
    data = response.json()
    assert data["error"]["code"] == "VALIDATION_ERROR"


def test_start_research_success(client: TestClient, mock_user: AuthenticatedUser):
    mock_svc = MockResearchService(owner_id=mock_user.id)
    app.dependency_overrides[get_research_service] = lambda: mock_svc
    try:
        response = client.post(
            "/api/v1/research",
            json={"company_name": "Google", "company_url": "google.com"},
        )
        assert response.status_code == 201
        data = response.json()
        assert "data" in data
        assert data["data"]["status"] == "queued"
        assert data["data"]["research_run_id"] == str(mock_svc.sample_run_id)
    finally:
        app.dependency_overrides.pop(get_research_service, None)


def test_get_research_status_owner_success(client: TestClient, mock_user: AuthenticatedUser):
    mock_svc = MockResearchService(owner_id=mock_user.id)
    app.dependency_overrides[get_research_service] = lambda: mock_svc
    try:
        response = client.get(f"/api/v1/research/{mock_svc.sample_run_id}")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert data["data"]["research_run_id"] == str(mock_svc.sample_run_id)
        assert data["data"]["status"] == "queued"
    finally:
        app.dependency_overrides.pop(get_research_service, None)


def test_get_research_status_unauthorized_other_user(client: TestClient, other_user: AuthenticatedUser):
    mock_svc = MockResearchService(owner_id=uuid4())  # Different owner
    app.dependency_overrides[get_current_user] = lambda: other_user
    app.dependency_overrides[get_research_service] = lambda: mock_svc
    try:
        response = client.get(f"/api/v1/research/{mock_svc.sample_run_id}")
        assert response.status_code == 403
        data = response.json()
        assert data["error"]["code"] == "PERMISSION_DENIED"
    finally:
        app.dependency_overrides.pop(get_research_service, None)
        app.dependency_overrides.pop(get_current_user, None)


def test_get_research_status_not_found(client: TestClient, mock_user: AuthenticatedUser):
    mock_svc = MockResearchService(owner_id=mock_user.id)
    app.dependency_overrides[get_research_service] = lambda: mock_svc
    try:
        random_id = uuid4()
        response = client.get(f"/api/v1/research/{random_id}")
        assert response.status_code == 404
        data = response.json()
        assert data["error"]["code"] == "NOT_FOUND"
    finally:
        app.dependency_overrides.pop(get_research_service, None)

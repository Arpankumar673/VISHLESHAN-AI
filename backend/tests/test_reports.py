from datetime import datetime, timezone
from uuid import uuid4
from fastapi.testclient import TestClient
from app.core.errors import AuthorizationError, NotFoundError
from app.core.security import AuthenticatedUser, get_current_user
from app.main import app
from app.schemas.report import ReportResponse
from app.services.report_service import get_report_service


class MockReportService:
    def __init__(self, owner_id):
        self.owner_id = owner_id
        self.sample_report_id = uuid4()
        self.sample_company_id = uuid4()
        self.sample_run_id = uuid4()

    def get_report(self, report_id, user_id):
        if report_id != self.sample_report_id:
            raise NotFoundError(f"Report with ID {report_id} not found")
        if user_id != self.owner_id:
            raise AuthorizationError("You do not have access to this intelligence report")
        now = datetime.now(timezone.utc)
        return ReportResponse(
            id=self.sample_report_id,
            company_id=self.sample_company_id,
            research_run_id=self.sample_run_id,
            title="Company Intelligence Report — Infosys Limited",
            content={"overview": {"name": "Infosys Limited"}},
            report_version="1.0",
            created_at=now,
            updated_at=now,
        )


def test_get_report_owner_success(client: TestClient, mock_user: AuthenticatedUser):
    mock_svc = MockReportService(owner_id=mock_user.id)
    app.dependency_overrides[get_report_service] = lambda: mock_svc
    try:
        response = client.get(f"/api/v1/reports/{mock_svc.sample_report_id}")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert data["data"]["id"] == str(mock_svc.sample_report_id)
        assert data["data"]["title"] == "Company Intelligence Report — Infosys Limited"
    finally:
        app.dependency_overrides.pop(get_report_service, None)


def test_get_report_unauthorized_other_user(client: TestClient, other_user: AuthenticatedUser):
    mock_svc = MockReportService(owner_id=uuid4())  # Different owner
    app.dependency_overrides[get_current_user] = lambda: other_user
    app.dependency_overrides[get_report_service] = lambda: mock_svc
    try:
        response = client.get(f"/api/v1/reports/{mock_svc.sample_report_id}")
        assert response.status_code == 403
        data = response.json()
        assert data["error"]["code"] == "PERMISSION_DENIED"
    finally:
        app.dependency_overrides.pop(get_report_service, None)
        app.dependency_overrides.pop(get_current_user, None)


def test_get_report_not_found(client: TestClient, mock_user: AuthenticatedUser):
    mock_svc = MockReportService(owner_id=mock_user.id)
    app.dependency_overrides[get_report_service] = lambda: mock_svc
    try:
        random_id = uuid4()
        response = client.get(f"/api/v1/reports/{random_id}")
        assert response.status_code == 404
        data = response.json()
        assert data["error"]["code"] == "NOT_FOUND"
    finally:
        app.dependency_overrides.pop(get_report_service, None)

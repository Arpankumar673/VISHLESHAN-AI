from datetime import datetime, timezone
from uuid import uuid4
from fastapi.testclient import TestClient
from app.main import app
from app.schemas.common import PaginatedData
from app.schemas.research import ResearchRunResponse, ResearchStatus
from app.services.history_service import get_history_service


class MockHistoryService:
    def __init__(self, owner_id):
        self.owner_id = owner_id

    def get_history(self, user_id, status=None, page=1, page_size=20):
        now = datetime.now(timezone.utc)
        items = [
            ResearchRunResponse(
                research_run_id=uuid4(),
                company_id=uuid4(),
                user_id=user_id,
                status=ResearchStatus.COMPLETED,
                created_at=now,
                updated_at=now,
            )
        ]
        return PaginatedData(
            items=items,
            total=1,
            page=page,
            page_size=page_size,
            total_pages=1,
        )


def test_get_history_success(client: TestClient, mock_user):
    mock_svc = MockHistoryService(owner_id=mock_user.id)
    app.dependency_overrides[get_history_service] = lambda: mock_svc
    try:
        response = client.get("/api/v1/history?page=1&page_size=10")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert data["data"]["total"] == 1
        assert len(data["data"]["items"]) == 1
        assert data["data"]["items"][0]["status"] == "completed"
    finally:
        app.dependency_overrides.pop(get_history_service, None)

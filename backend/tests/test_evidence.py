from datetime import datetime, timezone
from uuid import uuid4
from fastapi.testclient import TestClient
from app.core.errors import NotFoundError
from app.main import app
from app.schemas.evidence import EvidenceResponse, SourceType, VerificationStatus
from app.services.evidence_service import get_evidence_service


class MockEvidenceService:
    def __init__(self):
        self.sample_evidence_id = uuid4()
        self.sample_company_id = uuid4()
        self.sample_run_id = uuid4()

    def get_evidence_by_id(self, evidence_id):
        if evidence_id != self.sample_evidence_id:
            raise NotFoundError(f"Evidence record with ID {evidence_id} not found")
        now = datetime.now(timezone.utc)
        return EvidenceResponse(
            id=self.sample_evidence_id,
            company_id=self.sample_company_id,
            research_run_id=self.sample_run_id,
            claim="Company is registered with Registrar of Companies",
            evidence_text="CIN record found in MCA database matching company name.",
            source_url="https://mca.gov.in",
            source_title="Ministry of Corporate Affairs",
            source_type=SourceType.GOVERNMENT,
            reliability_score=1.0,
            confidence_score=0.98,
            verification_status=VerificationStatus.VERIFIED,
            observed_at=now,
            created_at=now,
            updated_at=now,
        )


def test_get_evidence_by_id_success(client: TestClient):
    mock_svc = MockEvidenceService()
    app.dependency_overrides[get_evidence_service] = lambda: mock_svc
    try:
        response = client.get(f"/api/v1/evidence/{mock_svc.sample_evidence_id}")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert data["data"]["id"] == str(mock_svc.sample_evidence_id)
        assert data["data"]["source_type"] == "government"
        assert data["data"]["verification_status"] == "verified"
    finally:
        app.dependency_overrides.pop(get_evidence_service, None)


def test_get_evidence_by_id_not_found(client: TestClient):
    mock_svc = MockEvidenceService()
    app.dependency_overrides[get_evidence_service] = lambda: mock_svc
    try:
        random_id = uuid4()
        response = client.get(f"/api/v1/evidence/{random_id}")
        assert response.status_code == 404
        data = response.json()
        assert data["error"]["code"] == "NOT_FOUND"
    finally:
        app.dependency_overrides.pop(get_evidence_service, None)

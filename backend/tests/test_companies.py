from datetime import datetime, timezone
from uuid import uuid4
from fastapi.testclient import TestClient
from app.main import app
from app.schemas.company import CompanyResponse
from app.schemas.evidence import EvidenceResponse, SourceType, VerificationStatus
from app.services.company_service import get_company_service


class MockCompanyService:
    def __init__(self):
        self.sample_id = uuid4()

    def get_company(self, company_id):
        if company_id == self.sample_id:
            now = datetime.now(timezone.utc)
            return CompanyResponse(
                id=self.sample_id,
                name="Infosys Limited",
                normalized_name="infosys limited",
                official_domain="infosys.com",
                description="Information technology consulting company",
                industry="Information Technology",
                headquarters="Bengaluru, India",
                created_at=now,
                updated_at=now,
                identifiers=[],
            )
        from app.core.errors import NotFoundError
        raise NotFoundError(f"Company with ID {company_id} not found")

    def get_company_evidence(self, company_id):
        if company_id == self.sample_id:
            now = datetime.now(timezone.utc)
            return [
                EvidenceResponse(
                    id=uuid4(),
                    company_id=self.sample_id,
                    research_run_id=uuid4(),
                    claim="Official corporate domain is verified",
                    evidence_text="DNS and registration certificates verify domain.",
                    source_url="https://infosys.com",
                    source_type=SourceType.OFFICIAL_COMPANY,
                    reliability_score=1.0,
                    confidence_score=0.95,
                    verification_status=VerificationStatus.VERIFIED,
                    observed_at=now,
                    created_at=now,
                    updated_at=now,
                )
            ]
        return []


def test_invalid_uuid_returns_422(client: TestClient):
    response = client.get("/api/v1/companies/not-a-valid-uuid")
    assert response.status_code == 422
    data = response.json()
    assert data["error"]["code"] == "VALIDATION_ERROR"


def test_company_not_found(client: TestClient):
    random_id = uuid4()
    response = client.get(f"/api/v1/companies/{random_id}")
    assert response.status_code == 404
    data = response.json()
    assert data["error"]["code"] == "NOT_FOUND"


def test_get_company_success(client: TestClient):
    mock_svc = MockCompanyService()
    app.dependency_overrides[get_company_service] = lambda: mock_svc
    try:
        response = client.get(f"/api/v1/companies/{mock_svc.sample_id}")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert data["data"]["name"] == "Infosys Limited"
        assert data["data"]["official_domain"] == "infosys.com"
    finally:
        app.dependency_overrides.pop(get_company_service, None)


def test_get_company_evidence_success(client: TestClient):
    mock_svc = MockCompanyService()
    app.dependency_overrides[get_company_service] = lambda: mock_svc
    try:
        response = client.get(f"/api/v1/companies/{mock_svc.sample_id}/evidence")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert len(data["data"]) == 1
        assert data["data"][0]["verification_status"] == "verified"
    finally:
        app.dependency_overrides.pop(get_company_service, None)

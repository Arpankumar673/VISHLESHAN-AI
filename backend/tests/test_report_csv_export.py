import csv
import io
from uuid import uuid4
from fastapi.testclient import TestClient
from app.core.security import AuthenticatedUser, get_current_user
from app.main import app
from app.services.report_export_service import ReportExportService


class DummyReportRepo:
    def __init__(self, report_id, run_id, company_id, user_id):
        self.report_id = str(report_id)
        self.run_id = str(run_id)
        self.company_id = str(company_id)
        self.user_id = str(user_id)

    def get_by_id(self, r_id):
        if str(r_id) == self.report_id:
            return {
                "id": self.report_id,
                "research_run_id": self.run_id,
                "company_id": self.company_id,
                "created_at": "2026-08-22T07:00:00Z",
                "companies": {"name": "Google LLC"},
                "research_runs": {"user_id": self.user_id},
                "content": {
                    "overview": {
                        "name": "Google LLC",
                        "description": "Multinational technology corporate entity.\nSpecializes in search, cloud & AI.",
                        "official_domain": "google.com",
                    },
                    "trust_score": {
                        "score": 92.5,
                        "risk_level": "low",
                        "explanation": "High reliability score.",
                    },
                    "final_decision_summary": {
                        "decision": "Verified identity baseline for Google LLC.",
                        "verdict_label": "Verified Identity Baseline",
                    },
                    "risk_score_explanation": {
                        "factors": ["Domain verified", "HTTPS active"],
                    },
                    "recruitment_risk": {
                        "job_offer_risk": "low",
                    },
                },
            }
        return None

    def get_by_research_run_id(self, run_id):
        return self.get_by_id(self.report_id)


class DummyEvidenceRepo:
    def get_by_research_run_id(self, run_id):
        return [
            {
                "claim": "Official domain is google.com, verified via HTTPS",
                "evidence_text": "HTTP 200 response from https://google.com.\nCanonical title: 'Google'",
                "source_url": "https://google.com",
                "source_title": "Google Official Homepage",
                "source_type": "official_website",
                "reliability_score": 0.95,
                "confidence_score": 0.98,
                "verification_status": "verified",
                "agent_name": "verification_agent",
                "observed_at": "2026-08-22T07:00:00Z",
                "published_at": "2026-08-01T00:00:00Z",
                "content_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            },
            {
                "claim": "Official recruitment portal located at https://careers.google.com",
                "evidence_text": "Careers link observed on official website footer.",
                "source_url": "https://careers.google.com",
                "source_title": "Google Careers",
                "source_type": "official_careers",
                "reliability_score": 0.92,
                "confidence_score": 0.90,
                "verification_status": "verified",
                "agent_name": "news_hiring_agent",
                "observed_at": "2026-08-22T07:01:00Z",
                "published_at": None,
                "content_hash": "a1b2c3d4e5f67890123456789abcdef0123456789abcdef0123456789abcdef0",
            },
        ]


def test_generate_report_csv_atomic_rows():
    user_id = uuid4()
    report_id = uuid4()
    run_id = uuid4()
    company_id = uuid4()

    dummy_report_repo = DummyReportRepo(report_id, run_id, company_id, user_id)
    dummy_evidence_repo = DummyEvidenceRepo()

    service = ReportExportService(
        report_repo=dummy_report_repo,
        evidence_repo=dummy_evidence_repo,
    )

    csv_text = service.generate_report_csv(report_id=report_id, user_id=user_id)

    assert csv_text is not None
    assert len(csv_text) > 0

    reader = csv.reader(io.StringIO(csv_text))
    rows = list(reader)

    # Check header
    header = rows[0]
    expected_columns = [
        "report_id",
        "research_run_id",
        "company_id",
        "company_name",
        "section",
        "subsection",
        "claim_key",
        "claim",
        "claim_value",
        "evidence_text",
        "source_url",
        "source_title",
        "source_type",
        "source_tier",
        "reliability_score",
        "confidence_score",
        "verification_status",
        "risk_level",
        "risk_score",
        "agent_name",
        "agent_version",
        "observed_at",
        "published_at",
        "content_hash",
        "is_conflicted",
        "is_verified",
        "uncertainty_reason",
        "record_type",
    ]
    assert header == expected_columns

    # Verify atomic evidence rows
    evidence_row_1 = rows[1]
    assert evidence_row_1[0] == str(report_id)
    assert evidence_row_1[3] == "Google LLC"
    assert evidence_row_1[4] == "16. Evidence Explorer"
    assert evidence_row_1[7] == "Official domain is google.com, verified via HTTPS"
    assert evidence_row_1[10] == "https://google.com"
    assert evidence_row_1[13] == "Tier 1 (Official)"
    assert evidence_row_1[16] == "verified"
    assert evidence_row_1[19] == "verification_agent"
    assert evidence_row_1[23] == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    assert evidence_row_1[25] == "true"
    assert evidence_row_1[27] == "evidence"


def test_export_report_csv_endpoint(client: TestClient, mock_user: AuthenticatedUser):
    report_id = uuid4()
    run_id = uuid4()
    company_id = uuid4()

    dummy_report_repo = DummyReportRepo(report_id, run_id, company_id, mock_user.id)
    dummy_evidence_repo = DummyEvidenceRepo()

    from app.services.report_export_service import ReportExportService

    export_svc = ReportExportService(
        report_repo=dummy_report_repo,
        evidence_repo=dummy_evidence_repo,
    )

    app.dependency_overrides[get_current_user] = lambda: mock_user

    try:
        # Patch ReportExportService inside endpoint
        import app.api.reports as reports_api
        old_class = reports_api.ReportExportService
        reports_api.ReportExportService = lambda: export_svc

        response = client.get(f"/api/v1/reports/{report_id}/export/csv")
        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]
        assert "attachment; filename=" in response.headers["content-disposition"]
        assert "report_id,research_run_id,company_id" in response.text
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        reports_api.ReportExportService = old_class

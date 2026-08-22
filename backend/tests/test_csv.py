import io
from fastapi.testclient import TestClient
from app.core.security import AuthenticatedUser
from app.main import app
from app.services.csv_service import CsvAnalysisService


def test_csv_service_deterministic_analysis():
    csv_data = (
        "company_name,job_title,salary,location\n"
        "Google,Software Engineer,150000,Mountain View\n"
        "Microsoft,Product Manager,140000,Redmond\n"
        "Google,Software Engineer,150000,Mountain View\n"  # Duplicate row
        "Amazon,Data Scientist,,Seattle\n"  # Missing salary
    )

    service = CsvAnalysisService()
    result = service.analyze_csv(csv_data.encode("utf-8"), filename="test_jobs.csv")

    assert result.filename == "test_jobs.csv"
    assert result.quality_overview.total_rows == 4
    assert result.quality_overview.total_columns == 4
    assert result.quality_overview.duplicate_rows_count == 1
    assert result.company_detection.detected is True
    assert result.company_detection.company_column == "company_name"
    assert "Google" in result.company_detection.sample_company_names


def test_analyze_csv_endpoint_authenticated(client: TestClient, mock_user: AuthenticatedUser):
    csv_content = b"company_name,revenue,employees\nTechCorp,1000000,50\nInnovateInc,2000000,100\n"

    response = client.post(
        "/api/v1/csv/analyze",
        files={"file": ("test_companies.csv", csv_content, "text/csv")},
    )

    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert data["data"]["quality_overview"]["total_rows"] == 2
    assert data["data"]["company_detection"]["company_column"] == "company_name"


def test_analyze_csv_invalid_file_extension(client: TestClient, mock_user: AuthenticatedUser):
    response = client.post(
        "/api/v1/csv/analyze",
        files={"file": ("test.exe", b"invalid binary", "application/octet-stream")},
    )

    assert response.status_code in [400, 422]

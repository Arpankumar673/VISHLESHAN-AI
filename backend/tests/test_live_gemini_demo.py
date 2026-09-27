import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock, PropertyMock
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings
from app.services.gemini_live_service import gemini_live_service, GeminiLiveService

client = TestClient(app)


def mock_gemini_response_for(company_name: str, domain: str = "") -> dict:
    """Helper to generate a valid structured response corresponding to the requested company."""
    return {
        "company_identity": {
            "name": company_name,
            "official_website": f"https://{domain}" if domain else f"https://{company_name.lower().replace(' ', '')}.com",
            "description": f"{company_name} is a leading enterprise recognized globally.",
            "industry": "Technology and Services",
            "headquarters": "Bengaluru, India" if "India" in company_name or company_name in ["TCS", "Infosys", "HCLTech", "Hindustan Aeronautics Limited"] else "California, USA",
            "founded": "1980",
            "company_type": "Public Corporation",
        },
        "executive_summary": f"{company_name} operates across global digital, software, and engineering services.",
        "business_overview": {
            "products_services": ["Cloud Platforms", "Consulting", "Enterprise Software"],
            "target_market": "Global Enterprise Clients",
            "business_model": "B2B Technology Services",
        },
        "corporate_information": {
            "founders": ["Founder A", "Founder B"],
            "leadership": ["CEO Person"],
            "locations": ["Headquarters", "Global Delivery Centers"],
            "employee_count": "50,000+",
        },
        "technology_and_digital_presence": {
            "technology_focus": ["Artificial Intelligence", "Cloud Native", "Cybersecurity"],
            "digital_presence": f"Active official website at {domain or company_name.lower() + '.com'}.",
            "engineering_presence": "Extensive enterprise development and engineering contributions.",
        },
        "news_and_reputation": {
            "positive_signals": ["Ranked top employer", "Major digital transformation contract win"],
            "negative_or_risk_signals": [],
            "recent_developments": ["Expanded operations and strategic cloud partnership in 2026."],
        },
        "certificates_and_registrations": [
            {
                "name": "ISO 27001",
                "issuer": "International Organization for Standardization",
                "status": "VERIFIED",
                "evidence": f"Corporate filings confirm ISO/IEC security compliance for {company_name}.",
            }
        ],
        "regulatory_information": [
            {
                "item": "Corporate Identification Registry Filing",
                "authority": "Ministry of Corporate Affairs / Registrar",
                "status": "VERIFIED",
                "evidence": "Incorporated public legal entity in good standing.",
            }
        ],
        "recruitment_analysis": {
            "risk_level": "LOW",
            "signals": ["Official careers portal verified", "Strict institutional hiring policy"],
            "explanation": "No fraudulent impersonation or deceptive job-offer scams detected on official domain.",
        },
        "risk_analysis": {
            "overall_level": "LOW",
            "risks": ["Standard competitive technology market dynamics."],
        },
        "trust_analysis": {
            "score": None,
            "confidence": 0.92,
            "status": "VERIFIED",
            "explanation": f"Corroborated public operational signals for {company_name}.",
        },
        "conflicts": [],
        "limitations": [
            "Data synthesized from verified public web records and official disclosures."
        ],
        "sources": [
            {
                "title": f"{company_name} Official Portal",
                "url": f"https://{domain or company_name.lower() + '.com'}",
                "source_type": "OFFICIAL",
                "reliability": "HIGH",
                "note": "Primary corporate domain.",
            },
            {
                "title": f"{company_name} Corporate Registry",
                "url": "https://mca.gov.in",
                "source_type": "GOVERNMENT",
                "reliability": "HIGH",
                "note": "Public statutory incorporation record.",
            },
        ],
    }


# ==============================================================================
# 1. INPUT VALIDATION TESTS
# ==============================================================================

def test_missing_company_name_returns_422_or_400():
    """Validates that empty or missing company name is rejected."""
    resp = client.post("/api/v1/demo/company-report", json={"company_name": ""})
    assert resp.status_code in [400, 422]

    resp2 = client.post("/api/v1/demo/company-report", json={})
    assert resp2.status_code == 422


# ==============================================================================
# 2. PRESENTATION COMPANIES TESTS (MANDATORY TEST LIST)
# ==============================================================================

TEST_COMPANIES = [
    ("HackIndia", "https://hackindia.xyz"),
    ("HCLTech", "https://hcltech.com"),
    ("Hindustan Aeronautics Limited", "https://hal-india.co.in"),
    ("Google", "https://google.com"),
    ("Microsoft", "https://microsoft.com"),
    ("TCS", "https://tcs.com"),
    ("Infosys", "https://infosys.com"),
    ("Zoho", "https://zoho.com"),  # Arbitrary local company
]


@pytest.mark.parametrize("company_name, official_url", TEST_COMPANIES)
def test_company_report_generation_for_required_companies(company_name, official_url):
    """
    Tests that for each required company:
    1. Returns 200 OK
    2. mode == 'LIVE_GEMINI_DEMO'
    3. Returned company name matches the requested company
    4. NEVER returns Google LLC when another company was requested!
    """
    domain = official_url.replace("https://", "").replace("http://", "")
    mock_gemini_data = mock_gemini_response_for(company_name, domain)

    # Patch effective API key and Gemini API call
    with patch.object(type(settings), "effective_gemini_api_key", new_callable=PropertyMock, return_value="test-gemini-key"):
        with patch.object(
            gemini_live_service,
            "_call_gemini_api",
            return_value=(mock_gemini_data, "GOOGLE_SEARCH_GROUNDED"),
        ):
            resp = client.post(
                "/api/v1/demo/company-report",
                json={"company_name": company_name, "official_url": official_url},
            )

            assert resp.status_code == 200
            data = resp.json()["data"]

            assert data["mode"] == "LIVE_GEMINI_DEMO"
            assert data["company"]["name"] == company_name
            assert data["report"]["company"]["name"] == company_name
            assert data["source_status"] in ["GOOGLE_SEARCH_GROUNDED", "AI_KNOWLEDGE_ONLY"]

            # Strict acceptance test: Company name must NOT be mismatched!
            if company_name != "Google":
                assert data["company"]["name"] != "Google LLC"
                assert "Google LLC" not in data["report"]["title"]


# ==============================================================================
# 3. CRITICAL INTEGRITY ACCEPTANCE TEST (SECTION 15)
# ==============================================================================

def test_critical_acceptance_rejection_of_mismatched_company():
    """
    SECTION 15:
    Request: HackIndia
    Returned: Google LLC
    EXPECTED: FAIL REQUEST (Never render Google LLC)
    """
    # Simulate Gemini returning Google LLC when HackIndia was requested
    hallucinated_data = mock_gemini_response_for("Google LLC", "google.com")

    with patch.object(type(settings), "effective_gemini_api_key", new_callable=PropertyMock, return_value="test-gemini-key"):
        with patch.object(
            gemini_live_service,
            "_call_gemini_api",
            return_value=(hallucinated_data, "AI_KNOWLEDGE_ONLY"),
        ):
            resp = client.post(
                "/api/v1/demo/company-report",
                json={"company_name": "HackIndia"},
            )

            # MUST fail request with integrity error, NEVER render Google LLC!
            assert resp.status_code in [422, 500]
            assert "Google LLC" not in str(resp.json().get("data", {}))


def test_critical_acceptance_rejection_of_hcltech_to_hackindia():
    """
    SECTION 15:
    Request: HCLTech
    Returned: HackIndia
    EXPECTED: FAIL REQUEST (Never render mismatched company)
    """
    mismatched_data = mock_gemini_response_for("HackIndia", "hackindia.xyz")

    with patch.object(type(settings), "effective_gemini_api_key", new_callable=PropertyMock, return_value="test-gemini-key"):
        with patch.object(
            gemini_live_service,
            "_call_gemini_api",
            return_value=(mismatched_data, "AI_KNOWLEDGE_ONLY"),
        ):
            # HackIndia was returned when HCLTech was requested
            # Since canonical name is enforced or validated, the returned name must match requested
            resp = client.post(
                "/api/v1/demo/company-report",
                json={"company_name": "HCLTech"},
            )
            # MUST fail request with integrity error, NEVER return HackIndia for HCLTech!
            assert resp.status_code in [422, 500]
            assert "HackIndia" not in str(resp.json().get("data", {}))


# ==============================================================================
# 4. CACHE ISOLATION TEST (SECTION 11)
# ==============================================================================

def test_cache_isolation_between_companies():
    """
    SECTION 11:
    HackIndia cache != Google cache
    HCLTech cache != HackIndia cache
    """
    service = GeminiLiveService()
    key_hack = service._get_cache_key("HackIndia", "https://hackindia.xyz")
    key_google = service._get_cache_key("Google", "https://google.com")
    key_hcl = service._get_cache_key("HCLTech", "https://hcltech.com")

    assert key_hack != key_google
    assert key_hack != key_hcl
    assert key_google != key_hcl


# ==============================================================================
# 5. ERROR HANDLING TEST (SECTION 12)
# ==============================================================================

def test_gemini_failure_returns_clean_retry_error_never_google():
    """
    SECTION 12:
    Gemini API quota/error -> show 'Gemini API temporarily unavailable. Please retry.'
    NEVER show Google LLC.
    """
    with patch.object(type(settings), "effective_gemini_api_key", new_callable=PropertyMock, return_value="test-gemini-key"):
        with patch.object(
            gemini_live_service,
            "_call_gemini_api",
            side_effect=RuntimeError("API status 429 Quota Exceeded"),
        ):
            resp = client.post(
                "/api/v1/demo/company-report",
                json={"company_name": "HackIndia"},
            )

            assert resp.status_code == 502
            body = resp.json()
            assert "temporarily unavailable" in body["error"]["message"]
            # Absolutely no Google LLC fallback
            assert "Google" not in json.dumps(body)


def test_missing_api_key_returns_informative_503():
    """When no Gemini API key is configured in backend environment."""
    with patch.object(type(settings), "effective_gemini_api_key", new_callable=PropertyMock, return_value=None):
        with patch.dict("os.environ", {}, clear=True):
            resp = client.post(
                "/api/v1/demo/company-report",
                json={"company_name": "HackIndia"},
            )
            assert resp.status_code == 503
            assert "not configured" in resp.json()["error"]["message"]

import json
import pytest
from unittest.mock import patch, PropertyMock
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings
from app.services.gemini_live_service import gemini_live_service, GeminiLiveService

client = TestClient(app)


def mock_gemini_response_for(company_name: str, domain: str = "") -> dict:
    """Helper to generate a rich structured response corresponding to the requested company."""
    dom = domain or f"{company_name.lower().replace(' ', '')}.com"
    official_site = f"https://{dom}"
    return {
        "company_identity": {
            "name": company_name,
            "legal_name": f"{company_name} Incorporated",
            "common_name": company_name,
            "official_website": official_site,
            "description": f"{company_name} is a leading global enterprise delivering innovative solutions.",
            "industry": "Artificial Intelligence & Enterprise Cloud",
            "sector": "Information Technology",
            "headquarters": "Bengaluru, Karnataka, India" if any(k in company_name for k in ["India", "TCS", "Infosys", "HCLTech", "Hindustan Aeronautics Limited", "HAL", "HackIndia"]) else "San Francisco, California, USA",
            "country": "India" if any(k in company_name for k in ["India", "TCS", "Infosys", "HCLTech", "Hindustan Aeronautics Limited", "HAL", "HackIndia"]) else "United States",
            "founded": "2015",
            "company_type": "Public Corporation / Enterprise",
            "parent_organization": None,
            "subsidiaries": [f"{company_name} Labs", f"{company_name} Global"],
        },
        "executive_summary": f"{company_name} operates across frontier digital, software, and engineering domains with global client impact.",
        "business_overview": {
            "products_services": [
                {
                    "name": "Frontier AI Platform",
                    "description": "High-throughput foundational model API serving millions of queries daily.",
                    "source_url": f"{official_site}/platform",
                },
                {
                    "name": "Enterprise Cloud Suite",
                    "description": "Enterprise cloud security, managed infrastructure, and automation services.",
                    "source_url": f"{official_site}/cloud",
                },
                {
                    "name": "Developer SDKs",
                    "description": "Comprehensive client libraries and developer tools.",
                    "source_url": f"{official_site}/developers",
                },
            ],
            "target_market": "Global Enterprise Clients, Developers, and Institutional Customers",
            "business_model": "B2B SaaS and Enterprise Licensing",
            "major_segments": ["Enterprise Solutions", "Cloud Services", "Research"],
            "geographic_presence": "North America, Europe, Asia-Pacific",
        },
        "corporate_information": {
            "founders": ["Founder Alpha", "Founder Beta"],
            "leadership": [
                {"name": "Jane Doe", "role": "Chief Executive Officer", "source_url": f"{official_site}/leadership"},
                {"name": "John Smith", "role": "Chief Technology Officer", "source_url": f"{official_site}/leadership"},
            ],
            "locations": ["Global HQ", "Regional Technology Centers"],
            "employee_count": "5,000+ employees",
        },
        "technology_and_digital_presence": {
            "technology_domains": ["Artificial Intelligence", "Large Language Models", "Cybersecurity", "Cloud Architecture"],
            "engineering_focus": ["High-Performance Computing", "Distributed Infrastructure", "API Systems"],
            "products_or_platforms": ["Core Model Service", "Developer Console"],
            "developer_resources": ["REST APIs", "Python SDK", "Node.js SDK", "Documentation"],
            "open_source_presence": ["Public GitHub repositories and research benchmarks"],
            "digital_presence": f"Active official website at {dom} and global developer ecosystem.",
        },
        "digital_presence_links": {
            "official_website": official_site,
            "careers_page": f"{official_site}/careers",
            "linkedin_url": f"https://linkedin.com/company/{company_name.lower().replace(' ', '')}",
            "github_url": f"https://github.com/{company_name.lower().replace(' ', '')}",
            "developer_portal": f"{official_site}/docs",
        },
        "news_and_reputation": {
            "positive_signals": ["Ranked top innovation employer", "Strategic cloud partnership expansion"],
            "negative_or_risk_signals": [],
            "recent_developments": [
                {
                    "date": "2025-2026",
                    "title": "Next-Generation Architecture Unveiled",
                    "summary": f"{company_name} released its next-generation platform to enterprise clients worldwide.",
                    "significance": "Expands market reach and technical differentiation.",
                    "source_url": f"{official_site}/news/latest",
                    "source_name": "Corporate Disclosures",
                },
                {
                    "date": "2025",
                    "title": "Global Cloud Infrastructure Expansion",
                    "summary": "Announced partnership with leading hyperscale cloud providers.",
                    "significance": "Improves regional compute availability.",
                    "source_url": f"{official_site}/news/cloud-partnership",
                    "source_name": "Industry Media",
                },
            ],
        },
        "financial_and_funding": {
            "funding_rounds": "Series E / Public Institutional Backing",
            "investors": ["Tier 1 Venture Capital", "Strategic Sovereign Funds"],
            "valuation": "Multi-billion dollar valuation",
            "revenue": "Public financial reporting",
            "market_cap_or_ticker": "Public Equity / Disclosed",
        },
        "certificates_and_compliance": [
            {
                "name": "ISO/IEC 27001",
                "issuer": "International Organization for Standardization",
                "identifier": "ISO-27001-VERIFIED",
                "issued_date": "2024",
                "status": "VERIFIED",
                "evidence": f"Audited information security management system for {company_name}.",
                "source_url": f"{official_site}/trust",
            },
            {
                "name": "SOC 2 Type II",
                "issuer": "American Institute of CPAs (AICPA)",
                "identifier": None,
                "issued_date": "2025",
                "status": "VERIFIED",
                "evidence": "Annual independent audit of security, availability, and confidentiality controls.",
                "source_url": f"{official_site}/security",
            },
        ],
        "regulatory_information": [
            {
                "registry_or_authority": "Ministry of Corporate Affairs / SEC Registrar",
                "registration_type": "Corporate Entity Incorporation",
                "identifier": None,
                "status": "VERIFIED",
                "evidence": f"Incorporated public commercial entity in good standing.",
                "source_url": "https://mca.gov.in",
            }
        ],
        "recruitment_analysis": {
            "official_careers_url": f"{official_site}/careers",
            "hiring_presence": "Active hiring across global engineering and product roles",
            "job_categories": ["AI Research", "Software Engineering", "Product Management", "Security"],
            "recruitment_channels": ["Direct careers portal", "Official LinkedIn Recruiter", "University Campus Drives"],
            "risk_signals": [],
            "risk_level": "LOW",
            "explanation": "No fraudulent recruitment signals or deceptive job-offer scams detected on official domain.",
        },
        "competitors": [
            {
                "name": "Competitor Alpha",
                "comparison_basis": "Competes in frontier AI models and enterprise platform services",
                "source_url": "https://example.com/comp1",
            },
            {
                "name": "Competitor Beta",
                "comparison_basis": "Competes in cloud-native developer tooling and API infrastructure",
                "source_url": "https://example.com/comp2",
            },
        ],
        "risk_analysis": {
            "overall_level": "LOW",
            "risks": ["Standard competitive market dynamics and regulatory AI compliance oversight."],
        },
        "conflicts": [],
        "limitations": [
            "Certain private corporate registration numbers require manual statutory registry lookups."
        ],
        "evidence": [
            {
                "id": "EV-001",
                "claim": f"{company_name} official primary domain active at {dom}",
                "source_title": f"{company_name} Official Portal",
                "source_url": official_site,
                "source_type": "OFFICIAL",
                "source_date": "2026",
                "confidence": 0.98,
                "verification_status": "VERIFIED",
                "reason": "Direct DNS and HTTPS resolution confirmed.",
            },
            {
                "id": "EV-002",
                "claim": f"{company_name} headquarters operational in verified jurisdiction",
                "source_title": f"{company_name} Corporate Overview",
                "source_url": f"{official_site}/about",
                "source_type": "OFFICIAL",
                "source_date": "2026",
                "confidence": 0.95,
                "verification_status": "VERIFIED",
                "reason": "Corporate filings corroborate operational headquarters.",
            },
            {
                "id": "EV-003",
                "claim": f"Executive leadership verified under CEO Jane Doe",
                "source_title": f"{company_name} Leadership Disclosures",
                "source_url": f"{official_site}/leadership",
                "source_type": "OFFICIAL",
                "source_date": "2026",
                "confidence": 0.92,
                "verification_status": "VERIFIED",
                "reason": "Public corporate governance records.",
            },
            {
                "id": "EV-004",
                "claim": "Official careers portal maintained on primary domain",
                "source_title": f"{company_name} Careers",
                "source_url": f"{official_site}/careers",
                "source_type": "OFFICIAL",
                "source_date": "2026",
                "confidence": 0.94,
                "verification_status": "VERIFIED",
                "reason": "Careers URL resolves directly under primary domain.",
            },
            {
                "id": "EV-005",
                "claim": "ISO 27001 Information Security certification verified",
                "source_title": "Independent Audit Confirmation",
                "source_url": f"{official_site}/trust",
                "source_type": "GOVERNMENT",
                "source_date": "2025",
                "confidence": 0.90,
                "verification_status": "VERIFIED",
                "reason": "Security trust disclosures confirmed.",
            },
            {
                "id": "EV-006",
                "claim": "Frontier AI Platform deployed to global enterprise users",
                "source_title": "Product Documentation",
                "source_url": f"{official_site}/platform",
                "source_type": "OFFICIAL",
                "source_date": "2026",
                "confidence": 0.95,
                "verification_status": "VERIFIED",
                "reason": "Public developer documentation.",
            },
            {
                "id": "EV-007",
                "claim": "Developer SDKs published for multi-language ecosystem",
                "source_title": "Developer Resources",
                "source_url": f"{official_site}/developers",
                "source_type": "OFFICIAL",
                "source_date": "2026",
                "confidence": 0.93,
                "verification_status": "VERIFIED",
                "reason": "Public GitHub and package repositories.",
            },
            {
                "id": "EV-008",
                "claim": "Statutory corporate registration in good standing",
                "source_title": "Corporate Regulatory Authority",
                "source_url": "https://mca.gov.in",
                "source_type": "REGISTRY",
                "source_date": "2025",
                "confidence": 0.90,
                "verification_status": "VERIFIED",
                "reason": "Public legal entity status confirmed.",
            },
            {
                "id": "EV-009",
                "claim": "Recent technology architecture expansion announced",
                "source_title": "Industry News Disclosures",
                "source_url": f"{official_site}/news/latest",
                "source_type": "NEWS",
                "source_date": "2025-2026",
                "confidence": 0.88,
                "verification_status": "VERIFIED",
                "reason": "Corroborated across major business news outlets.",
            },
            {
                "id": "EV-010",
                "claim": "Low recruitment fraud and impersonation risk profile",
                "source_title": "Forensic Recruitment Screening",
                "source_url": f"{official_site}/careers",
                "source_type": "OFFICIAL",
                "source_date": "2026",
                "confidence": 0.92,
                "verification_status": "VERIFIED",
                "reason": "No fraudulent recruiting signals detected.",
            },
        ],
        "sources": [
            {"title": f"{company_name} Official Portal", "url": official_site, "source_type": "OFFICIAL", "reliability": "HIGH", "note": "Primary corporate domain."},
            {"title": f"{company_name} Careers Channel", "url": f"{official_site}/careers", "source_type": "OFFICIAL", "reliability": "HIGH", "note": "Verified careers portal."},
            {"title": f"{company_name} Product Documentation", "url": f"{official_site}/platform", "source_type": "OFFICIAL", "reliability": "HIGH", "note": "Developer platform specifications."},
            {"title": f"{company_name} Trust & Security Portal", "url": f"{official_site}/trust", "source_type": "OFFICIAL", "reliability": "HIGH", "note": "Compliance disclosures."},
            {"title": "Corporate Registration Authority", "url": "https://mca.gov.in", "source_type": "GOVERNMENT", "reliability": "HIGH", "note": "Public corporate registry."},
            {"title": "Industry Technology Media", "url": "https://techcrunch.com", "source_type": "NEWS", "reliability": "MEDIUM", "note": "Technology news coverage."},
            {"title": "Global Business News", "url": "https://reuters.com", "source_type": "NEWS", "reliability": "HIGH", "note": "Financial and corporate news."},
            {"title": "Open Source Community", "url": "https://github.com", "source_type": "OTHER", "reliability": "MEDIUM", "note": "Public repository presence."},
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
    ("OpenAI", "https://openai.com"),
    ("Triangle Mind", "https://trianglemind.com"),
]


@pytest.mark.parametrize("company_name, official_url", TEST_COMPANIES)
def test_company_report_generation_for_required_companies(company_name, official_url):
    """
    Tests that for each required company:
    1. Returns 200 OK
    2. mode == 'LIVE_GEMINI_DEMO'
    3. Returned company name matches the requested company
    4. NEVER returns Google LLC when another company was requested!
    5. Source status is recognized
    6. Contains deep multi-category fields
    """
    domain = official_url.replace("https://", "").replace("http://", "")
    mock_gemini_data = mock_gemini_response_for(company_name, domain)

    with patch.object(type(settings), "effective_gemini_api_key", new_callable=PropertyMock, return_value="test-gemini-key"):
        with patch.object(
            gemini_live_service,
            "_call_gemini_api",
            return_value=(mock_gemini_data, "LIVE_GOOGLE_SEARCH_GROUNDED"),
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
            assert data["source_status"] in ["LIVE_GOOGLE_SEARCH_GROUNDED", "GOOGLE_SEARCH_GROUNDED", "AI_KNOWLEDGE_MODE", "AI_KNOWLEDGE_ONLY"]

            # Strict acceptance test: Company name must NOT be mismatched!
            if company_name != "Google":
                assert data["company"]["name"] != "Google LLC"
                assert "Google LLC" not in data["report"]["title"]

            # Depth verification
            report_content = data["report"]["content"]
            assert "source_summary" in report_content
            assert report_content["source_summary"]["total_sources"] >= 5
            assert len(report_content["evidence"]) >= 8
            assert len(report_content["overview"]["products_services_detailed"]) >= 2
            assert len(report_content["corporate_governance"]["leadership_detailed"]) >= 1
            assert len(report_content["competitors"]) >= 1
            assert "technology_domains" in report_content["technology_reputation"]
            assert report_content["recruitment_analysis"]["risk_level"] in ["LOW", "MEDIUM", "HIGH", "UNABLE_TO_VERIFY"]


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
    hallucinated_data = mock_gemini_response_for("Google LLC", "google.com")

    with patch.object(type(settings), "effective_gemini_api_key", new_callable=PropertyMock, return_value="test-gemini-key"):
        with patch.object(
            gemini_live_service,
            "_call_gemini_api",
            return_value=(hallucinated_data, "AI_KNOWLEDGE_MODE"),
        ):
            resp = client.post(
                "/api/v1/demo/company-report",
                json={"company_name": "HackIndia"},
            )

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
            return_value=(mismatched_data, "AI_KNOWLEDGE_MODE"),
        ):
            resp = client.post(
                "/api/v1/demo/company-report",
                json={"company_name": "HCLTech"},
            )
            assert resp.status_code in [422, 500]
            assert "HackIndia" not in str(resp.json().get("data", {}))


# ==============================================================================
# 4. COMPANY NAME NORMALIZATION TESTS (SECTION 21)
# ==============================================================================

def test_company_name_normalization_openai():
    """Lowercase 'openai' resolves and normalizes to 'OpenAI'."""
    mock_data = mock_gemini_response_for("openai", "openai.com")
    mock_data["company_identity"]["name"] = "openai"

    with patch.object(type(settings), "effective_gemini_api_key", new_callable=PropertyMock, return_value="test-gemini-key"):
        with patch.object(
            gemini_live_service,
            "_call_gemini_api",
            return_value=(mock_data, "LIVE_GOOGLE_SEARCH_GROUNDED"),
        ):
            resp = client.post(
                "/api/v1/demo/company-report",
                json={"company_name": "openai"},
            )
            assert resp.status_code == 200
            data = resp.json()["data"]
            assert data["company"]["name"] == "OpenAI"
            assert data["report"]["company"]["name"] == "OpenAI"


def test_company_name_normalization_hal():
    """Acronym 'hal' resolves and normalizes to 'Hindustan Aeronautics Limited'."""
    mock_data = mock_gemini_response_for("Hindustan Aeronautics Limited", "hal-india.co.in")

    with patch.object(type(settings), "effective_gemini_api_key", new_callable=PropertyMock, return_value="test-gemini-key"):
        with patch.object(
            gemini_live_service,
            "_call_gemini_api",
            return_value=(mock_data, "LIVE_GOOGLE_SEARCH_GROUNDED"),
        ):
            resp = client.post(
                "/api/v1/demo/company-report",
                json={"company_name": "hal"},
            )
            assert resp.status_code == 200
            data = resp.json()["data"]
            assert "Hindustan Aeronautics Limited" in data["company"]["name"]


# ==============================================================================
# 5. CACHE ISOLATION TEST (SECTION 11)
# ==============================================================================

def test_cache_isolation_between_companies():
    """
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
# 6. ERROR HANDLING TEST (SECTION 12)
# ==============================================================================

def test_gemini_failure_returns_clean_retry_error_never_google():
    """
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

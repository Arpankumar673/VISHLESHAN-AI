from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
import httpx
import pytest

from app.research.agents.base import AgentInput, AgentResponse, AgentResult
from app.research.agents.verification_agent import VerificationAgent, _normalize_host
from app.research.models import NormalizedEvidence, SourceFinding, utc_now
from app.schemas.evidence import SourceType, VerificationStatus


# Helper to construct mock httpx responses
def _make_mock_response(status_code: int = 200, text: str = "", url: str = "https://google.com"):
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    mock_resp.text = text
    mock_resp.url = url
    return mock_resp


# ------------------------------------------------------------
# 1. HTTP 200 Reachable Domain (Fully Verified Case)
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_verification_agent_http_200_reachable_domain():
    agent = VerificationAgent()
    run_id = uuid4()
    company_id = uuid4()

    inp = AgentInput(
        research_run_id=run_id,
        company_id=company_id,
        company_name="Google LLC",
        company_url="https://google.com",
    )

    html = "<html><head><title>Google LLC - Official Site</title></head><body>Welcome to Google</body></html>"
    mock_resp = _make_mock_response(200, html, "https://google.com")

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        result = await agent.run(inp)

    assert result.status == "completed"
    assert result.metadata["domain_verified"] is True
    assert result.metadata["verification_state"] == "verified"
    assert result.metadata["verification_confidence"] >= 0.90
    assert len(result.evidence) == 2
    assert all(e.verification_status == VerificationStatus.VERIFIED for e in result.evidence)


# ------------------------------------------------------------
# 2. HTTP 301 -> 200 Redirect
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_verification_agent_redirect_200():
    agent = VerificationAgent()
    inp = AgentInput(
        research_run_id=uuid4(),
        company_id=uuid4(),
        company_name="Google LLC",
        company_url="google.com",
    )

    html = "<html><head><title>Google Corporate</title></head></html>"
    # Redirects from google.com to www.google.com
    mock_resp = _make_mock_response(200, html, "https://www.google.com/")

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        result = await agent.run(inp)

    assert result.status == "completed"
    assert result.metadata["verification_state"] == "verified"


# ------------------------------------------------------------
# 3. HTTP 404 Error -> Unable to Verify
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_verification_agent_http_404():
    agent = VerificationAgent()
    inp = AgentInput(
        research_run_id=uuid4(),
        company_id=uuid4(),
        company_name="Ghost Corp",
        company_url="ghostcorp12345.com",
    )

    mock_resp = _make_mock_response(404, "Not Found", "https://ghostcorp12345.com")

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        result = await agent.run(inp)

    assert result.status == "completed"
    assert result.metadata["verification_state"] == "unable_to_verify"
    assert result.evidence[0].verification_status == VerificationStatus.UNABLE_TO_VERIFY


# ------------------------------------------------------------
# 4. HTTP 500 Error -> Unable to Verify
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_verification_agent_http_500():
    agent = VerificationAgent()
    inp = AgentInput(
        research_run_id=uuid4(),
        company_id=uuid4(),
        company_name="Failing Server Inc",
        company_url="failserver.com",
    )

    mock_resp = _make_mock_response(500, "Internal Server Error", "https://failserver.com")

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        result = await agent.run(inp)

    assert result.metadata["verification_state"] == "unable_to_verify"


# ------------------------------------------------------------
# 5. Connection Timeout -> Unable to Verify
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_verification_agent_timeout():
    agent = VerificationAgent()
    inp = AgentInput(
        research_run_id=uuid4(),
        company_id=uuid4(),
        company_name="Slow Corp",
        company_url="slowcorp.com",
    )

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = httpx.TimeoutException("Connection timed out after 5.0s")
        result = await agent.run(inp)

    assert result.status == "completed"
    assert result.metadata["verification_state"] == "unable_to_verify"
    assert any("Connection timeout" in w for w in result.warnings)


# ------------------------------------------------------------
# 6. Connection Failure / DNS Failure -> Unable to Verify
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_verification_agent_connection_failure():
    agent = VerificationAgent()
    inp = AgentInput(
        research_run_id=uuid4(),
        company_id=uuid4(),
        company_name="Offline Corp",
        company_url="offlinecorp.test",
    )

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = httpx.ConnectError("Failed to resolve host")
        result = await agent.run(inp)

    assert result.metadata["verification_state"] == "unable_to_verify"


# ------------------------------------------------------------
# 7. Invalid SSL Certificate -> Handled Gracefully
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_verification_agent_invalid_ssl():
    agent = VerificationAgent()
    inp = AgentInput(
        research_run_id=uuid4(),
        company_id=uuid4(),
        company_name="Bad Cert LLC",
        company_url="badcert.com",
    )

    # Agent uses verify=False for dev resilience; if HTTP 200 returns with title, it proceeds safely
    html = "<html><head><title>Bad Cert LLC Official</title></head></html>"
    mock_resp = _make_mock_response(200, html, "https://badcert.com")

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        result = await agent.run(inp)

    assert result.status == "completed"


# ------------------------------------------------------------
# 8. Canonical Domain Match
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_verification_agent_canonical_match():
    agent = VerificationAgent()
    inp = AgentInput(
        research_run_id=uuid4(),
        company_id=uuid4(),
        company_name="Acme Systems",
        company_url="acmesystems.com",
    )

    html = '<html><head><title>Acme Systems Portal</title><link rel="canonical" href="https://acmesystems.com/"></head></html>'
    mock_resp = _make_mock_response(200, html, "https://acmesystems.com/")

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        result = await agent.run(inp)

    assert result.metadata["verification_state"] == "verified"


# ------------------------------------------------------------
# 9. Canonical Domain Mismatch / Redirect Collision -> Conflicting
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_verification_agent_canonical_mismatch():
    agent = VerificationAgent()
    inp = AgentInput(
        research_run_id=uuid4(),
        company_id=uuid4(),
        company_name="Acme Systems",
        company_url="acmesystems-fake.com",
    )

    # Redirects from acmesystems-fake.com to malicious-other-company.com
    mock_resp = _make_mock_response(200, "<html><title>Other Entity</title></html>", "https://malicious-other-company.com")

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        result = await agent.run(inp)

    assert result.metadata["verification_state"] == "conflicting"
    assert result.evidence[0].verification_status == VerificationStatus.CONFLICTING


# ------------------------------------------------------------
# 10. Matching Identity Title
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_verification_agent_matching_title():
    agent = VerificationAgent()
    inp = AgentInput(
        research_run_id=uuid4(),
        company_id=uuid4(),
        company_name="Nvidia Corporation",
        company_url="nvidia.com",
    )

    html = "<html><head><title>NVIDIA Official Site | AI Computing</title></head></html>"
    mock_resp = _make_mock_response(200, html, "https://nvidia.com")

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        result = await agent.run(inp)

    assert result.metadata["verification_state"] == "verified"


# ------------------------------------------------------------
# 11. Unrelated Identity Title (Generates UNVERIFIED status)
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_verification_agent_unrelated_title():
    agent = VerificationAgent()
    inp = AgentInput(
        research_run_id=uuid4(),
        company_id=uuid4(),
        company_name="Apex Robotics",
        company_url="apexrobotics.com",
    )

    # Title mentions a completely generic string without matching company name keywords
    html = "<html><head><title>Domain Parked Page - Buy This Domain</title></head></html>"
    mock_resp = _make_mock_response(200, html, "https://apexrobotics.com")

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        result = await agent.run(inp)

    assert result.metadata["verification_state"] == "unverified"


# ------------------------------------------------------------
# 12. Missing HTML Title
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_verification_agent_missing_title():
    agent = VerificationAgent()
    inp = AgentInput(
        research_run_id=uuid4(),
        company_id=uuid4(),
        company_name="Apex Robotics",
        company_url="apexrobotics.com",
    )

    html = "<html><head></head><body>No title tag here</body></html>"
    mock_resp = _make_mock_response(200, html, "https://apexrobotics.com")

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        result = await agent.run(inp)

    # Without title or name match, cannot verify identity
    assert result.metadata["verification_state"] == "unverified"


# ------------------------------------------------------------
# 13. Missing Canonical Link
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_verification_agent_missing_canonical():
    agent = VerificationAgent()
    inp = AgentInput(
        research_run_id=uuid4(),
        company_id=uuid4(),
        company_name="Intel Corp",
        company_url="intel.com",
    )

    html = "<html><head><title>Intel Corporation Official Site</title></head></html>"
    mock_resp = _make_mock_response(200, html, "https://intel.com")

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        result = await agent.run(inp)

    assert result.metadata["verification_state"] == "verified"


# ------------------------------------------------------------
# 14. Malformed HTML Output
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_verification_agent_malformed_html():
    agent = VerificationAgent()
    inp = AgentInput(
        research_run_id=uuid4(),
        company_id=uuid4(),
        company_name="Malformed Inc",
        company_url="malformed.com",
    )

    html = "<<<<title>>Malformed Inc Title<<<<</title>>random corrupt bytes"
    mock_resp = _make_mock_response(200, html, "https://malformed.com")

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        result = await agent.run(inp)

    assert result.status == "completed"


# ------------------------------------------------------------
# 15. Matching Upstream official_domain Claim
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_verification_agent_matching_upstream_claim():
    agent = VerificationAgent()

    upstream_ev = NormalizedEvidence(
        claim="CompanyResearchAgent claims official domain is google.com",
        evidence_text="Official website.",
        source_url="https://google.com",
        source_type=SourceType.OFFICIAL_COMPANY,
        observed_at=utc_now(),
        reliability_score=0.9,
        confidence_score=0.9,
        verification_status=VerificationStatus.VERIFIED,
        agent_name="company_research",
        content_hash="1" * 64,
        claim_key="official_domain",
        claim_value="google.com",
        category="identity_verification",
    )

    inp = AgentInput(
        research_run_id=uuid4(),
        company_id=uuid4(),
        company_name="Google LLC",
        company_url="google.com",
        previous_evidence=[upstream_ev],
    )

    html = "<html><head><title>Google LLC - Search Engine</title></head></html>"
    mock_resp = _make_mock_response(200, html, "https://google.com")

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        result = await agent.run(inp)

    assert result.metadata["verification_state"] == "verified"


# ------------------------------------------------------------
# 16. Conflicting Upstream official_domain Claim
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_verification_agent_conflicting_upstream_claim():
    agent = VerificationAgent()

    inp = AgentInput(
        research_run_id=uuid4(),
        company_id=uuid4(),
        company_name="Phish Corp",
        company_url="phishcorp-legit.com",
        context={"conflicting_domain": "phishcorp-scam.com"},
    )

    result = await agent.run(inp)
    assert result.metadata["verification_state"] == "conflicting"


# ------------------------------------------------------------
# 17. VERIFIED Requires Sufficient Evidence
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_verification_agent_verified_requires_sufficient_evidence():
    agent = VerificationAgent()
    inp = AgentInput(
        research_run_id=uuid4(),
        company_id=uuid4(),
        company_name="Test Entity",
        company_url=None,
    )

    result = await agent.run(inp)
    assert result.metadata["verification_state"] != "verified"


# ------------------------------------------------------------
# 18. HTTP 200 Alone Does NOT Produce VERIFIED
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_verification_agent_http_200_alone_not_verified():
    agent = VerificationAgent()
    inp = AgentInput(
        research_run_id=uuid4(),
        company_id=uuid4(),
        company_name="Quantum Computing Inc",
        company_url="quantumcomp.com",
    )

    # HTTP 200 returns a generic blank page without matching name keywords
    html = "<html><head><title>Under Construction</title></head><body>Blank</body></html>"
    mock_resp = _make_mock_response(200, html, "https://quantumcomp.com")

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        result = await agent.run(inp)

    # Must NOT produce VERIFIED
    assert result.metadata["verification_state"] != "verified"
    assert result.metadata["verification_state"] == "unverified"


# ------------------------------------------------------------
# 19. Title Match Alone Does NOT Produce VERIFIED
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_verification_agent_title_match_alone_not_verified():
    agent = VerificationAgent()
    inp = AgentInput(
        research_run_id=uuid4(),
        company_id=uuid4(),
        company_name="Unreachable Corp",
        company_url="unreachablecorp.com",
    )

    # If domain fails HTTP probe (e.g. 500 error), title match cannot verify domain
    mock_resp = _make_mock_response(500, "<html><title>Unreachable Corp</title></html>", "https://unreachablecorp.com")

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        result = await agent.run(inp)

    assert result.metadata["verification_state"] != "verified"


# ------------------------------------------------------------
# 20. Technical Failure Does NOT Produce HIGH RISK / FRAUD
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_verification_agent_technical_failure_not_fraud():
    agent = VerificationAgent()
    inp = AgentInput(
        research_run_id=uuid4(),
        company_id=uuid4(),
        company_name="Down Server LLC",
        company_url="downserver.com",
    )

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = httpx.ConnectTimeout("Connection timeout")
        result = await agent.run(inp)

    # Technical failure maps to UNABLE_TO_VERIFY, NOT CONFLICTING or FRAUD
    assert result.metadata["verification_state"] == "unable_to_verify"
    assert result.evidence[0].verification_status == VerificationStatus.UNABLE_TO_VERIFY


# ------------------------------------------------------------
# 21. Platform Domain Rejection
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_verification_agent_platform_domain_rejection():
    agent = VerificationAgent()
    inp = AgentInput(
        research_run_id=uuid4(),
        company_id=uuid4(),
        company_name="Wikipedia Project",
        company_url="https://wikipedia.org",
    )

    result = await agent.run(inp)

    # wikipedia.org cannot be verified as an official company domain
    assert result.metadata["verification_state"] == "unable_to_verify"


# ------------------------------------------------------------
# 22. claim_key Metadata Attachment
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_verification_agent_claim_key_metadata():
    agent = VerificationAgent()
    inp = AgentInput(
        research_run_id=uuid4(),
        company_id=uuid4(),
        company_name="Meta Platforms",
        company_url="meta.com",
    )

    html = "<html><head><title>Meta - Official Site</title></head></html>"
    mock_resp = _make_mock_response(200, html, "https://meta.com")

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        result = await agent.run(inp)

    assert len(result.evidence) >= 1
    claim_key = getattr(result.evidence[0], "claim_key", None) or getattr(result.evidence[0], "raw_metadata", {}).get("claim_key")
    assert claim_key == "official_domain"


# ------------------------------------------------------------
# 23. claim_value Metadata Attachment
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_verification_agent_claim_value_metadata():
    agent = VerificationAgent()
    inp = AgentInput(
        research_run_id=uuid4(),
        company_id=uuid4(),
        company_name="Meta Platforms",
        company_url="meta.com",
    )

    html = "<html><head><title>Meta Platforms Corporate</title></head></html>"
    mock_resp = _make_mock_response(200, html, "https://meta.com")

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        result = await agent.run(inp)

    claim_value = getattr(result.evidence[0], "claim_value", None) or getattr(result.evidence[0], "raw_metadata", {}).get("claim_value")
    assert claim_value == "meta.com"


# ------------------------------------------------------------
# 24. Provenance Attribute Preservation
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_verification_agent_provenance_preservation():
    agent = VerificationAgent()
    inp = AgentInput(
        research_run_id=uuid4(),
        company_id=uuid4(),
        company_name="Tesla Inc",
        company_url="tesla.com",
    )

    html = "<html><head><title>Tesla Official Site</title></head></html>"
    mock_resp = _make_mock_response(200, html, "https://tesla.com")

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        result = await agent.run(inp)

    ev = result.evidence[0]
    assert ev.agent_name == "verification"
    assert ev.source_type == SourceType.OFFICIAL_COMPANY
    assert ev.source_url == "https://tesla.com"
    assert ev.reliability_score > 0.0


# ------------------------------------------------------------
# 25. SHA-256 Content Hash Preservation
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_verification_agent_sha256_preservation():
    agent = VerificationAgent()
    inp = AgentInput(
        research_run_id=uuid4(),
        company_id=uuid4(),
        company_name="Oracle Corp",
        company_url="oracle.com",
    )

    html = "<html><head><title>Oracle Cloud Applications</title></head></html>"
    mock_resp = _make_mock_response(200, html, "https://oracle.com")

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        result = await agent.run(inp)

    for ev in result.evidence:
        assert isinstance(ev.content_hash, str)
        assert len(ev.content_hash) == 64


# ------------------------------------------------------------
# 26. Legacy Signature Compatibility
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_verification_agent_legacy_signature_compatibility():
    agent = VerificationAgent()
    run_id = uuid4()
    company_id = uuid4()

    html = "<html><head><title>Apple Official Site</title></head></html>"
    mock_resp = _make_mock_response(200, html, "https://apple.com")

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        result = await agent.execute(
            research_run_id=run_id,
            company_id=company_id,
            company_name="Apple Inc.",
            domain="apple.com",
        )

    assert isinstance(result, AgentResult)
    assert result.agent_name == "verification"
    assert result.status == "completed"
    assert result.metadata["domain_verified"] is True
    assert result.metadata["verification_state"] == "verified"


# ------------------------------------------------------------
# 27. SSRF Localhost Rejection
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_verification_agent_ssrf_localhost_rejection():
    agent = VerificationAgent()
    inp = AgentInput(
        research_run_id=uuid4(),
        company_id=uuid4(),
        company_name="Localhost Hacking Attempt",
        company_url="localhost",
    )

    result = await agent.run(inp)
    assert result.metadata["verification_state"] == "unable_to_verify"
    assert "SSRF" in result.evidence[0].evidence_text or "invalid" in result.evidence[0].evidence_text.lower()


# ------------------------------------------------------------
# 28. SSRF Private IP Rejection
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_verification_agent_ssrf_private_ip_rejection():
    agent = VerificationAgent()
    inp = AgentInput(
        research_run_id=uuid4(),
        company_id=uuid4(),
        company_name="Private Subnet Probe",
        company_url="192.168.1.1",
    )

    result = await agent.run(inp)
    assert result.metadata["verification_state"] == "unable_to_verify"


# ------------------------------------------------------------
# 29. Independent Search Corroboration
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_verification_agent_independent_search_corroboration():
    agent = VerificationAgent()
    inp = AgentInput(
        research_run_id=uuid4(),
        company_id=uuid4(),
        company_name="Acme International",
        company_url="acme-corp.com",
    )

    html = "<html><head><title>Acme International Corp</title></head></html>"
    mock_resp = _make_mock_response(200, html, "https://acme-corp.com")

    mock_search_finding = SourceFinding(
        claim="Acme International official domain acme-corp.com corroborated via public search",
        evidence_text="DuckDuckGo discovery corroborated acme-corp.com as official site for Acme International",
        source_url="https://duckduckgo.com/?q=Acme+International",
        source_title="Acme Search Result",
        source_type=SourceType.NEWS,
    )

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get, \
         patch.object(agent.search_adapter, "collect", new_callable=AsyncMock) as mock_search:
        mock_get.return_value = mock_resp
        mock_search.return_value = [mock_search_finding]

        result = await agent.run(inp)

    assert result.status == "completed"
    assert result.metadata["verification_state"] == "verified"
    assert len(result.evidence) >= 3


# ------------------------------------------------------------
# 30. Registration Unavailable Returns Graceful State
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_verification_agent_registration_unavailable_returns_unable_to_verify():
    agent = VerificationAgent()
    inp = AgentInput(
        research_run_id=uuid4(),
        company_id=uuid4(),
        company_name="Unregistered Startup",
        company_url="unregistered123.org",
    )

    mock_resp = _make_mock_response(404, "Not Found", "https://unregistered123.org")

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        result = await agent.run(inp)

    assert result.metadata["verification_state"] == "unable_to_verify"
    assert not any("fraud" in w.lower() for w in result.warnings)


# ------------------------------------------------------------
# 31. Certification Unavailable Graceful Handling
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_verification_agent_certification_unavailable_graceful():
    agent = VerificationAgent()
    inp = AgentInput(
        research_run_id=uuid4(),
        company_id=uuid4(),
        company_name="Uncertified Corp",
        company_url="uncertifiedcorp.com",
    )

    html = "<html><head><title>Uncertified Corp Homepage</title></head></html>"
    mock_resp = _make_mock_response(200, html, "https://uncertifiedcorp.com")

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        result = await agent.run(inp)

    assert result.status == "completed"
    assert result.metadata["verification_state"] == "verified"


# ------------------------------------------------------------
# 32. Partial Source Failure Resilience
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_verification_agent_partial_source_failure_resilience():
    agent = VerificationAgent()
    inp = AgentInput(
        research_run_id=uuid4(),
        company_id=uuid4(),
        company_name="Resilient Systems",
        company_url="resilientsystems.com",
    )

    html = "<html><head><title>Resilient Systems Corporate Portal</title></head></html>"
    mock_resp = _make_mock_response(200, html, "https://resilientsystems.com")

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get, \
         patch.object(agent.search_adapter, "collect", side_effect=RuntimeError("Search service timeout")):
        mock_get.return_value = mock_resp

        result = await agent.run(inp)

    assert result.status == "completed"
    assert result.metadata["verification_state"] == "verified"


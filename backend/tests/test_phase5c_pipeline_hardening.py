import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
import pytest

from app.research.agents.base import AgentInput, AgentResult, AgentStatus
from app.research.agents.company_research_agent import CompanyResearchAgent
from app.research.agents.evidence_trust_agent import EvidenceTrustAgent
from app.research.agents.risk_analysis_agent import RiskAnalysisAgent
from app.research.models import IdentityResult, NormalizedEvidence, SourceFinding, utc_now
from app.research.normalizer import EvidenceNormalizer
from app.research.sources.search import PublicSearchAdapter
from app.schemas.evidence import SourceType, VerificationStatus


# ------------------------------------------------------------
# Scenario A: Verified Company with Strong Evidence
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_scenario_a_verified_company_strong_evidence():
    ev1 = NormalizedEvidence(
        claim="Google LLC operates official domain google.com",
        evidence_text="Verified homepage title.",
        source_url="https://google.com",
        source_type=SourceType.OFFICIAL_COMPANY,
        observed_at=utc_now(),
        reliability_score=0.95,
        confidence_score=0.95,
        verification_status=VerificationStatus.VERIFIED,
        agent_name="company_research",
        content_hash="a" * 64,
    )
    ev2 = NormalizedEvidence(
        claim="Google LLC registered corporate entity",
        evidence_text="Active SEC filing.",
        source_url="https://sec.gov/edgar/google",
        source_type=SourceType.OFFICIAL_COMPANY,
        observed_at=utc_now(),
        reliability_score=0.98,
        confidence_score=0.98,
        verification_status=VerificationStatus.VERIFIED,
        agent_name="company_research",
        content_hash="b" * 64,
    )

    trust_agent = EvidenceTrustAgent()
    inp = AgentInput(
        research_run_id=uuid4(),
        company_id=uuid4(),
        company_name="Google LLC",
        previous_evidence=[ev1, ev2],
    )
    trust_res = await trust_agent.run(inp)

    assert trust_res.status == "completed"
    assert trust_res.metadata["preliminary_trust_score"] >= 80.0
    assert trust_res.metadata["preliminary_risk_level"] == "low"  # low risk


# ------------------------------------------------------------
# Scenario B: Company with No Resolvable Domain
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_scenario_b_no_resolvable_domain():
    search_adapter = PublicSearchAdapter()

    # Mock DuckDuckGo returning no abstract URL or meta URL
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"AbstractText": "", "AbstractURL": "", "meta": {}}
        mock_get.return_value = mock_resp

        resolved_domain = await search_adapter.resolve_domain("Obscure Local Entity 123")
        assert resolved_domain is None

    # Agent execution with no domain
    mock_search = AsyncMock()
    mock_search.collect.return_value = [
        SourceFinding(
            claim="Obscure Local Entity 123 operates in region",
            evidence_text="Local directory entry.",
            source_url="https://directory.test/123",
            source_type=SourceType.OTHER,
        )
    ]
    mock_official = AsyncMock()

    agent = CompanyResearchAgent(search_adapter=mock_search, official_adapter=mock_official)
    inp = AgentInput(
        research_run_id=uuid4(),
        company_id=uuid4(),
        company_name="Obscure Local Entity 123",
    )

    result = await agent.run(inp)
    assert result.status == "completed"
    assert len(result.evidence) == 1
    mock_official.collect.assert_not_called()  # Official adapter skipped when domain is None


# ------------------------------------------------------------
# Scenario C: Company with Only One Evidence Source
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_scenario_c_one_evidence_source():
    ev = NormalizedEvidence(
        claim="Acme Corp summary profile",
        evidence_text="Overview of Acme Corp.",
        source_url="https://en.wikipedia.org/wiki/Acme",
        source_type=SourceType.NEWS,
        observed_at=utc_now(),
        reliability_score=0.7,
        confidence_score=0.7,
        verification_status=VerificationStatus.UNVERIFIED,
        agent_name="company_research",
        content_hash="c" * 64,
    )

    trust_agent = EvidenceTrustAgent()
    inp = AgentInput(
        research_run_id=uuid4(),
        company_id=uuid4(),
        company_name="Acme Corp",
        previous_evidence=[ev],
    )
    trust_res = await trust_agent.run(inp)

    assert trust_res.status == "completed"
    assert 0.0 <= trust_res.metadata["preliminary_trust_score"] <= 100.0


# ------------------------------------------------------------
# Scenario D: Company with Contradictory Evidence
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_scenario_d_contradictory_evidence():
    ev_support = NormalizedEvidence(
        claim="Alpha Corp was founded in 2010",
        evidence_text="Filing lists founding date 2010.",
        source_url="https://registry.gov/alpha",
        source_type=SourceType.OFFICIAL_COMPANY,
        observed_at=utc_now(),
        reliability_score=0.9,
        confidence_score=0.9,
        verification_status=VerificationStatus.VERIFIED,
        agent_name="company_research",
        content_hash="d1" + "0" * 62,
    )
    ev_contradict = NormalizedEvidence(
        claim="Alpha Corp was founded in 2022",
        evidence_text="Blog post claims 2022 founding.",
        source_url="https://blog.test/alpha",
        source_type=SourceType.NEWS,
        observed_at=utc_now(),
        reliability_score=0.4,
        confidence_score=0.4,
        verification_status=VerificationStatus.UNVERIFIED,
        agent_name="news_hiring",
        content_hash="d2" + "0" * 62,
    )

    risk_agent = RiskAnalysisAgent()
    inp = AgentInput(
        research_run_id=uuid4(),
        company_id=uuid4(),
        company_name="Alpha Corp",
        company_url="https://alphacorp.com",
        previous_evidence=[ev_support, ev_contradict],
    )
    risk_res = await risk_agent.run(inp)

    assert risk_res.status == "completed"
    assert "risk_score" in risk_res.metadata


# ------------------------------------------------------------
# Scenario E: One Research Adapter Failure
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_scenario_e_one_adapter_failure():
    mock_search = AsyncMock()
    mock_search.collect.side_effect = ConnectionError("Search API timeout")

    mock_official = AsyncMock()
    mock_official.collect.return_value = [
        SourceFinding(
            claim="Beta Inc operates official domain betainc.com",
            evidence_text="Official site.",
            source_url="https://betainc.com",
            source_type=SourceType.OFFICIAL_COMPANY,
        )
    ]

    agent = CompanyResearchAgent(search_adapter=mock_search, official_adapter=mock_official)
    inp = AgentInput(
        research_run_id=uuid4(),
        company_id=uuid4(),
        company_name="Beta Inc",
        company_url="https://betainc.com",
    )

    result = await agent.run(inp)
    assert result.status == "partial"
    assert len(result.evidence) == 1
    assert any("Public search query encountered error" in w for w in result.warnings)


# ------------------------------------------------------------
# Scenario F: Multiple Research Adapter Failures
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_scenario_f_multiple_adapter_failures():
    mock_search = AsyncMock()
    mock_search.collect.side_effect = TimeoutError("DNS failure")

    mock_official = AsyncMock()
    mock_official.collect.side_effect = TimeoutError("HTTP timeout")

    agent = CompanyResearchAgent(search_adapter=mock_search, official_adapter=mock_official)
    inp = AgentInput(
        research_run_id=uuid4(),
        company_id=uuid4(),
        company_name="Gamma Corp",
        company_url="https://gammacorp.test",
    )

    result = await agent.run(inp)
    assert result.status == "failed"
    assert len(result.evidence) == 0
    assert len(result.errors) > 0


# ------------------------------------------------------------
# Scenario G: Empty Evidence
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_scenario_g_empty_evidence():
    trust_agent = EvidenceTrustAgent()
    inp = AgentInput(
        research_run_id=uuid4(),
        company_id=uuid4(),
        company_name="Empty Corp",
        previous_evidence=[],
    )
    trust_res = await trust_agent.run(inp)

    assert trust_res.status in ("completed", "partial")
    assert trust_res.metadata["preliminary_trust_score"] >= 0.0
    assert len(trust_res.evidence) == 0


# ------------------------------------------------------------
# Scenario H: Duplicate Evidence
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_scenario_h_duplicate_evidence():
    ev_original = NormalizedEvidence(
        claim="Delta Tech operates official domain deltatech.com",
        evidence_text="Official website.",
        source_url="https://deltatech.com",
        source_type=SourceType.OFFICIAL_COMPANY,
        observed_at=utc_now(),
        reliability_score=0.9,
        confidence_score=0.95,
        verification_status=VerificationStatus.VERIFIED,
        agent_name="company_research",
        content_hash="e" * 64,
    )
    # Duplicate with same content hash
    ev_duplicate = NormalizedEvidence(
        claim="Delta Tech operates official domain deltatech.com",
        evidence_text="Official website.",
        source_url="https://deltatech.com",
        source_type=SourceType.OFFICIAL_COMPANY,
        observed_at=utc_now(),
        reliability_score=0.9,
        confidence_score=0.95,
        verification_status=VerificationStatus.VERIFIED,
        agent_name="company_research",
        content_hash="e" * 64,
    )

    trust_agent = EvidenceTrustAgent()
    inp = AgentInput(
        research_run_id=uuid4(),
        company_id=uuid4(),
        company_name="Delta Tech",
        previous_evidence=[ev_original, ev_duplicate],
    )
    trust_res = await trust_agent.run(inp)

    assert trust_res.status == "completed"
    # EvidenceTrustAgent deduplicates by content_hash
    assert len(trust_res.evidence) == 1


# ------------------------------------------------------------
# Scenario I: Unverified Evidence Only
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_scenario_i_unverified_evidence_only():
    ev = NormalizedEvidence(
        claim="Epsilon LLC unverified press mention",
        evidence_text="Unconfirmed press release.",
        source_url="https://prnews.test/epsilon",
        source_type=SourceType.NEWS,
        observed_at=utc_now(),
        reliability_score=0.5,
        confidence_score=0.5,
        verification_status=VerificationStatus.UNVERIFIED,
        agent_name="news_hiring",
        content_hash="f" * 64,
    )

    risk_agent = RiskAnalysisAgent()
    inp = AgentInput(
        research_run_id=uuid4(),
        company_id=uuid4(),
        company_name="Epsilon LLC",
        previous_evidence=[ev],
    )
    risk_res = await risk_agent.run(inp)

    assert risk_res.status == "completed"
    # Unverified evidence / low confidence must NOT automatically cause High Risk / Fraud label
    assert risk_res.metadata["overall_risk_level"] in ("low", "medium")


# ------------------------------------------------------------
# Scenario J: Critical Domain Collision
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_scenario_j_critical_domain_collision():
    ev_legit = NormalizedEvidence(
        claim="Zeta Systems operates official domain zetasystems.com",
        evidence_text="Official portal.",
        source_url="https://zetasystems.com",
        source_type=SourceType.OFFICIAL_COMPANY,
        observed_at=utc_now(),
        reliability_score=0.9,
        confidence_score=0.9,
        verification_status=VerificationStatus.VERIFIED,
        agent_name="company_research",
        content_hash="j1" + "0" * 62,
    )
    ev_fake = NormalizedEvidence(
        claim="Zeta Systems operates official domain zetasystems-spoof.com",
        evidence_text="Phishing portal claim.",
        source_url="https://zetasystems-spoof.com",
        source_type=SourceType.OFFICIAL_COMPANY,
        observed_at=utc_now(),
        reliability_score=0.9,
        confidence_score=0.9,
        verification_status=VerificationStatus.CONFLICTING,
        agent_name="company_research",
        content_hash="j2" + "0" * 62,
    )

    risk_agent = RiskAnalysisAgent()
    inp = AgentInput(
        research_run_id=uuid4(),
        company_id=uuid4(),
        company_name="Zeta Systems",
        company_url="https://zetasystems.com",
        previous_evidence=[ev_legit, ev_fake],
    )
    risk_res = await risk_agent.run(inp)

    assert risk_res.status == "completed"
    # Critical domain collision should trigger risk analysis
    assert risk_res.metadata["overall_risk_level"] in ("medium", "high")

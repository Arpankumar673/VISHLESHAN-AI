from datetime import datetime, timezone
from uuid import UUID, uuid4
import pytest
from app.research.agents.base import AgentResponse
from app.research.agents.company_research_agent import CompanyResearchAgent
from app.research.agents.evidence_trust_agent import EvidenceTrustAgent
from app.research.agents.news_hiring_agent import NewsHiringAgent
from app.research.agents.orchestrator import MultiAgentOrchestrator
from app.research.agents.report_agent import ReportAgent
from app.research.agents.risk_analysis_agent import RiskAnalysisAgent
from app.research.agents.technology_reputation_agent import TechnologyReputationAgent
from app.research.agents.verification_agent import VerificationAgent
from app.research.models import NormalizedEvidence
from app.research.normalizer import EvidenceNormalizer
from app.schemas.evidence import SourceType, VerificationStatus


# ------------------------------------------------------------
# 1. Agent Contract Validation (All 7 Specialized Agents)
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_agent_contracts_and_envelopes():
    run_id = uuid4()
    company_id = uuid4()
    company_name = "Microsoft"
    domain = "microsoft.com"

    agents = [
        CompanyResearchAgent(),
        VerificationAgent(),
        NewsHiringAgent(),
        TechnologyReputationAgent(),
        RiskAnalysisAgent(),
    ]

    collected_responses = []

    for agent in agents:
        resp = await agent.execute(
            research_run_id=run_id,
            company_id=company_id,
            company_name=company_name,
            domain=domain,
        )

        assert isinstance(resp, AgentResponse)
        assert resp.agent_name == agent.agent_name
        assert resp.agent_version == "1.0"
        assert resp.status in ("completed", "partial", "failed")
        assert resp.research_run_id == run_id
        assert isinstance(resp.evidence, list)
        assert isinstance(resp.warnings, list)
        assert isinstance(resp.errors, list)
        assert isinstance(resp.metadata, dict)
        collected_responses.append(resp)

    # Test Evidence & Trust Agent aggregation contract
    trust_agent = EvidenceTrustAgent()
    trust_resp = await trust_agent.execute(
        research_run_id=run_id,
        company_id=company_id,
        company_name=company_name,
        domain=domain,
        context={"agent_responses": collected_responses},
    )
    assert trust_resp.agent_name == "evidence_trust"
    assert trust_resp.status == "completed"
    assert len(trust_resp.evidence) > 0

    # Test Report Agent contract
    report_agent = ReportAgent()
    rep_resp = await report_agent.execute(
        research_run_id=run_id,
        company_id=company_id,
        company_name=company_name,
        domain=domain,
        context={"evidence": trust_resp.evidence},
    )
    assert rep_resp.agent_name == "report_agent"
    assert rep_resp.status == "completed"
    assert "report_content" in rep_resp.metadata


# ------------------------------------------------------------
# 2. Evidence Common Contract Validation
# ------------------------------------------------------------
def test_evidence_common_contract():
    now = datetime.now(timezone.utc)
    ev = NormalizedEvidence(
        claim="Microsoft operates azure.microsoft.com cloud platform",
        evidence_text="Verified enterprise cloud computing portal.",
        source_url="https://azure.microsoft.com",
        source_title="Azure Cloud",
        source_type=SourceType.OFFICIAL_COMPANY,
        observed_at=now,
        reliability_score=0.90,
        confidence_score=0.95,
        verification_status=VerificationStatus.VERIFIED,
        agent_name="company_research",
        content_hash=EvidenceNormalizer.compute_hash(
            "Microsoft operates azure.microsoft.com cloud platform",
            "https://azure.microsoft.com",
            "Verified enterprise cloud computing portal.",
        ),
    )

    ev_dict = ev.model_dump()
    required_keys = [
        "claim",
        "evidence_text",
        "source_url",
        "source_title",
        "source_type",
        "published_at",
        "observed_at",
        "reliability_score",
        "confidence_score",
        "verification_status",
        "agent_name",
        "content_hash",
    ]
    for k in required_keys:
        assert k in ev_dict


# ------------------------------------------------------------
# 3. Partial Agent Failure & Resiliency
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_orchestrator_handles_partial_agent_failure():
    # Mock one agent to raise an error
    failing_news_agent = NewsHiringAgent()
    async def mock_fail(*args, **kwargs):
        raise RuntimeError("News feed network timeout")
    failing_news_agent.execute = mock_fail

    orchestrator = MultiAgentOrchestrator(news_hiring_agent=failing_news_agent)
    run_id = uuid4()
    company_id = uuid4()

    result = await orchestrator.execute_run(
        research_run_id=run_id,
        company_id=company_id,
        company_name="Infosys",
        company_url="infosys.com",
    )

    # The research run should NOT crash fatally; it should complete partially with other agents' evidence
    assert result.status in ("completed", "partial")
    assert len(result.evidence_items) > 0
    assert result.identity.canonical_name == "Infosys"


# ------------------------------------------------------------
# 4. Correlation Traceability Verification
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_research_run_correlation_id():
    orchestrator = MultiAgentOrchestrator()
    run_id = uuid4()
    company_id = uuid4()

    result = await orchestrator.execute_run(
        research_run_id=run_id,
        company_id=company_id,
        company_name="Apple",
        company_url="apple.com",
    )

    assert result.research_run_id == run_id
    assert result.company_id == company_id
    for ev in result.evidence_items:
        # Hashing and provenance must be valid
        assert len(ev.content_hash) == 64

from datetime import datetime, timezone
from uuid import uuid4
import pytest
from app.research.agents.base import AgentInput, AgentResponse, AgentResult
from app.research.agents.evidence_trust_agent import EvidenceTrustAgent
from app.research.models import NormalizedEvidence
from app.schemas.evidence import SourceType, VerificationStatus


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


# ------------------------------------------------------------
# 1. Standard Execution via AgentInput
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_evidence_trust_agent_standard_execution():
    agent = EvidenceTrustAgent()
    run_id = uuid4()
    company_id = uuid4()

    ev1 = NormalizedEvidence(
        claim="Claim 1: Domain is registered",
        evidence_text="Verified domain.",
        source_url="https://example.com",
        source_type=SourceType.OFFICIAL_COMPANY,
        observed_at=utc_now(),
        reliability_score=0.90,
        confidence_score=0.95,
        verification_status=VerificationStatus.VERIFIED,
        agent_name="verification",
        content_hash="1" * 64,
    )

    ev2 = NormalizedEvidence(
        claim="Claim 2: Company is active",
        evidence_text="Active operations.",
        source_url="https://en.wikipedia.org/wiki/Example",
        source_type=SourceType.NEWS,
        observed_at=utc_now(),
        reliability_score=0.80,
        confidence_score=0.85,
        verification_status=VerificationStatus.VERIFIED,
        agent_name="company_research",
        content_hash="2" * 64,
    )

    inp = AgentInput(
        research_run_id=run_id,
        company_id=company_id,
        company_name="Example Corp",
        company_url="https://example.com",
        previous_evidence=[ev1, ev2],
    )

    result = await agent.run(inp)

    assert isinstance(result, AgentResult)
    assert isinstance(result, AgentResponse)
    assert result.agent_name == "evidence_trust"
    assert result.status == "completed"
    assert result.research_run_id == run_id
    assert result.execution_time_ms > 0.0

    # Verification of metrics
    assert result.metadata["total_evidence"] == 2
    assert result.metadata["verified_count"] == 2
    assert result.metadata["avg_reliability"] == 0.85
    assert result.metadata["preliminary_trust_score"] == 85.0
    assert result.metadata["preliminary_risk_level"] == "low"
    assert len(result.evidence) == 2


# ------------------------------------------------------------
# 2. Legacy Execution Signature Compatibility
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_evidence_trust_agent_legacy_signature():
    agent = EvidenceTrustAgent()
    run_id = uuid4()
    company_id = uuid4()

    ev1 = NormalizedEvidence(
        claim="Legacy test evidence",
        evidence_text="Evidence text.",
        source_url="https://test.com",
        source_type=SourceType.OFFICIAL_COMPANY,
        observed_at=utc_now(),
        reliability_score=0.90,
        confidence_score=0.90,
        verification_status=VerificationStatus.VERIFIED,
        agent_name="verification",
        content_hash="a" * 64,
    )

    prev_agent_result = AgentResult(
        agent_name="verification",
        status="completed",
        research_run_id=run_id,
        evidence=[ev1],
    )

    result = await agent.execute(
        research_run_id=run_id,
        company_id=company_id,
        company_name="TestCorp",
        domain="test.com",
        context={"agent_responses": [prev_agent_result]},
    )

    assert isinstance(result, AgentResult)
    assert result.agent_name == "evidence_trust"
    assert result.status == "completed"
    assert result.metadata["total_evidence"] == 1
    assert len(result.evidence) == 1


# ------------------------------------------------------------
# 3. SHA-256 Deduplication (Duplicate items do NOT inflate trust)
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_evidence_trust_agent_sha256_deduplication():
    agent = EvidenceTrustAgent()
    run_id = uuid4()
    company_id = uuid4()

    # Create two duplicate evidence items with exact same content hash
    dup_hash = "f" * 64
    ev1 = NormalizedEvidence(
        claim="Identical claim",
        evidence_text="Identical text",
        source_url="https://dup.com",
        source_type=SourceType.OFFICIAL_COMPANY,
        observed_at=utc_now(),
        reliability_score=0.90,
        confidence_score=0.90,
        verification_status=VerificationStatus.VERIFIED,
        agent_name="company_research",
        content_hash=dup_hash,
    )

    ev2 = NormalizedEvidence(
        claim="Identical claim",
        evidence_text="Identical text",
        source_url="https://dup.com",
        source_type=SourceType.OFFICIAL_COMPANY,
        observed_at=utc_now(),
        reliability_score=0.90,
        confidence_score=0.90,
        verification_status=VerificationStatus.VERIFIED,
        agent_name="company_research",
        content_hash=dup_hash,
    )

    inp = AgentInput(
        research_run_id=run_id,
        company_id=company_id,
        company_name="DupCorp",
        company_url="https://dup.com",
        previous_evidence=[ev1, ev2],
    )

    result = await agent.execute(inp)

    # 2 raw items input, but 1 unique item after deduplication
    assert result.metadata["raw_evidence_count"] == 2
    assert result.metadata["total_evidence"] == 1
    assert len(result.evidence) == 1
    assert result.findings[0]["duplicates_removed"] == 1


# ------------------------------------------------------------
# 4. Empty Evidence Handling
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_evidence_trust_agent_empty_evidence():
    agent = EvidenceTrustAgent()
    run_id = uuid4()
    company_id = uuid4()

    inp = AgentInput(
        research_run_id=run_id,
        company_id=company_id,
        company_name="EmptyCorp",
        company_url="https://empty.test",
        previous_evidence=[],
    )

    result = await agent.execute(inp)

    assert result.status == "partial"
    assert result.metadata["total_evidence"] == 0
    assert result.metadata["preliminary_trust_score"] == 50.0
    assert len(result.evidence) == 0
    assert any("No evidence items were provided" in w for w in result.warnings)


# ------------------------------------------------------------
# 5. Evidence Provenance Retention
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_evidence_trust_agent_provenance_retention():
    agent = EvidenceTrustAgent()
    run_id = uuid4()

    ev = NormalizedEvidence(
        claim="Provenance claim test",
        evidence_text="Detailed text",
        source_url="https://provenance.com",
        source_title="Provenance Title",
        source_type=SourceType.OFFICIAL_COMPANY,
        published_at=utc_now(),
        observed_at=utc_now(),
        reliability_score=0.90,
        confidence_score=0.95,
        verification_status=VerificationStatus.VERIFIED,
        agent_name="verification",
        content_hash="d" * 64,
    )

    inp = AgentInput(
        research_run_id=run_id,
        company_id=uuid4(),
        company_name="ProvCorp",
        previous_evidence=[ev],
    )

    result = await agent.execute(inp)
    out_ev = result.evidence[0]

    assert out_ev.claim == "Provenance claim test"
    assert out_ev.source_url == "https://provenance.com"
    assert out_ev.source_title == "Provenance Title"
    assert out_ev.source_type == SourceType.OFFICIAL_COMPANY
    assert out_ev.reliability_score == 0.90
    assert out_ev.confidence_score == 0.95
    assert out_ev.verification_status == VerificationStatus.VERIFIED
    assert out_ev.agent_name == "verification"
    assert out_ev.content_hash == "d" * 64


# ------------------------------------------------------------
# 6. Error Boundary Handling
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_evidence_trust_agent_error_boundary():
    agent = EvidenceTrustAgent()
    invalid_dict = {"company_name": "TestCorp"}

    result = await agent.run(invalid_dict)
    assert result.status == "failed"
    assert result.agent_name == "evidence_trust"
    assert len(result.errors) > 0

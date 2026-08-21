from datetime import datetime, timezone
from uuid import uuid4
import pytest
from app.research.agents.base import AgentInput, AgentResponse, AgentResult
from app.research.agents.risk_analysis_agent import RiskAnalysisAgent
from app.research.models import NormalizedEvidence
from app.schemas.evidence import SourceType, VerificationStatus


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


# ------------------------------------------------------------
# 1. Standard Execution via AgentInput (Low Risk Case)
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_risk_analysis_agent_standard_execution():
    agent = RiskAnalysisAgent()
    run_id = uuid4()
    company_id = uuid4()

    inp = AgentInput(
        research_run_id=run_id,
        company_id=company_id,
        company_name="Google LLC",
        company_url="https://google.com",
    )

    result = await agent.run(inp)

    assert isinstance(result, AgentResult)
    assert isinstance(result, AgentResponse)
    assert result.agent_name == "risk_analysis"
    assert result.status == "completed"
    assert result.research_run_id == run_id
    assert result.execution_time_ms > 0.0

    # Risk metadata checks
    assert result.metadata["overall_risk_level"] == "low"
    assert result.metadata["risk_score"] == 15
    assert result.metadata["overall_confidence"] == 0.90
    assert len(result.metadata["indicators"]) >= 2
    assert len(result.findings) >= 2


# ------------------------------------------------------------
# 2. Legacy Signature Compatibility
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_risk_analysis_agent_legacy_signature():
    agent = RiskAnalysisAgent()
    run_id = uuid4()
    company_id = uuid4()

    result = await agent.execute(
        research_run_id=run_id,
        company_id=company_id,
        company_name="Microsoft",
        domain="microsoft.com",
    )

    assert isinstance(result, AgentResult)
    assert result.agent_name == "risk_analysis"
    assert result.status == "completed"
    assert result.metadata["overall_risk_level"] == "low"


# ------------------------------------------------------------
# 3. Missing Evidence / Missing Domain != Fraud (Medium Risk, Low Confidence)
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_risk_analysis_agent_missing_domain_low_confidence():
    agent = RiskAnalysisAgent()
    run_id = uuid4()
    company_id = uuid4()

    inp = AgentInput(
        research_run_id=run_id,
        company_id=company_id,
        company_name="Unlisted Stealther LLC",
        company_url=None,
    )

    result = await agent.execute(inp)

    # Missing domain MUST NOT automatically be flagged as high risk or critical fraud!
    assert result.metadata["overall_risk_level"] == "medium"
    assert result.metadata["risk_score"] == 45
    assert result.metadata["overall_confidence"] == 0.40  # Low confidence
    assert any("unverified" in f["status"].lower() or "missing" in f["reason"].lower() or "insufficient" in f["reason"].lower() for f in result.findings)
    assert any("Company lacks verified official domain" in w for w in result.warnings)


# ------------------------------------------------------------
# 4. Conflicting Evidence Signals -> High Risk Signal
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_risk_analysis_agent_conflicting_evidence_signals():
    agent = RiskAnalysisAgent()
    run_id = uuid4()
    company_id = uuid4()

    # Pass previous evidence containing a CONFLICTING verification status
    conflicting_ev = NormalizedEvidence(
        claim="Disputed domain ownership",
        evidence_text="Two separate entities claim domain control.",
        source_url="https://disputed-domain.com",
        source_type=SourceType.OTHER,
        observed_at=utc_now(),
        reliability_score=0.60,
        confidence_score=0.35,
        verification_status=VerificationStatus.CONFLICTING,
        agent_name="verification",
        content_hash="b" * 64,
    )

    inp = AgentInput(
        research_run_id=run_id,
        company_id=company_id,
        company_name="DisputedCorp",
        company_url="https://disputed-domain.com",
        previous_evidence=[conflicting_ev],
    )

    result = await agent.execute(inp)

    assert result.metadata["overall_risk_level"] == "high"
    assert result.metadata["risk_score"] == 75
    assert result.metadata["overall_confidence"] == 0.35
    assert any(f["status"] == "conflicting_signal" for f in result.findings)


# ------------------------------------------------------------
# 5. Evidence Traceability in Risk Indicators
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_risk_analysis_agent_evidence_traceability():
    agent = RiskAnalysisAgent()
    run_id = uuid4()
    company_id = uuid4()

    prev_ev = NormalizedEvidence(
        claim="Google operates official search service",
        evidence_text="Verified enterprise search portal.",
        source_url="https://google.com",
        source_type=SourceType.OFFICIAL_COMPANY,
        observed_at=utc_now(),
        reliability_score=0.90,
        confidence_score=0.95,
        verification_status=VerificationStatus.VERIFIED,
        agent_name="company_research",
        content_hash="c" * 64,
    )

    inp = AgentInput(
        research_run_id=run_id,
        company_id=company_id,
        company_name="Google",
        company_url="https://google.com",
        previous_evidence=[prev_ev],
    )

    result = await agent.execute(inp)
    evidence_sufficiency_finding = next(f for f in result.findings if f["risk_type"] == "evidence_sufficiency")

    assert evidence_sufficiency_finding["status"] == "passed"
    assert "c" * 64 in evidence_sufficiency_finding["evidence_references"]


# ------------------------------------------------------------
# 6. Error Boundary Handling
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_risk_analysis_agent_error_boundary():
    agent = RiskAnalysisAgent()
    invalid_dict = {"company_name": "TestCorp"}

    result = await agent.run(invalid_dict)
    assert result.status == "failed"
    assert result.agent_name == "risk_analysis"
    assert len(result.errors) > 0

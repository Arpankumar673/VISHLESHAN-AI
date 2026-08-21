from datetime import datetime, timezone
from uuid import uuid4
import pytest
from app.research.agents.base import AgentInput, AgentResponse, AgentResult
from app.research.agents.report_agent import ReportAgent
from app.research.models import IdentityResult, NormalizedEvidence
from app.schemas.evidence import SourceType, VerificationStatus


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


# ------------------------------------------------------------
# 1. Standard Execution via AgentInput
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_report_agent_standard_execution():
    agent = ReportAgent()
    run_id = uuid4()
    company_id = uuid4()

    ev1 = NormalizedEvidence(
        claim="Official Google Domain Verified",
        evidence_text="Enterprise search portal.",
        source_url="https://google.com",
        source_type=SourceType.OFFICIAL_COMPANY,
        observed_at=utc_now(),
        reliability_score=0.90,
        confidence_score=0.95,
        verification_status=VerificationStatus.VERIFIED,
        agent_name="verification",
        content_hash="1" * 64,
    )

    inp = AgentInput(
        research_run_id=run_id,
        company_id=company_id,
        company_name="Google LLC",
        company_url="https://google.com",
        previous_evidence=[ev1],
    )

    result = await agent.run(inp)

    assert isinstance(result, AgentResult)
    assert isinstance(result, AgentResponse)
    assert result.agent_name == "report_agent"
    assert result.status == "completed"
    assert result.research_run_id == run_id
    assert result.execution_time_ms > 0.0

    # Metadata & Report Content verification
    content = result.metadata["report_content"]
    assert isinstance(content, dict)
    assert content["overview"]["name"] == "Google LLC"
    assert content["overview"]["official_domain"] == "google.com"
    assert len(content["evidence"]) == 1
    assert len(content["references"]) == 1
    assert content["evidence"][0]["content_hash"] == "1" * 64


# ------------------------------------------------------------
# 2. Legacy Signature Compatibility
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_report_agent_legacy_signature():
    agent = ReportAgent()
    run_id = uuid4()
    company_id = uuid4()

    identity = IdentityResult(
        canonical_name="Microsoft Corp",
        official_domain="microsoft.com",
        official_website="https://microsoft.com",
        description="Software technology corporation.",
        headquarters="Redmond, WA, USA",
        confidence=0.95,
    )

    ev1 = NormalizedEvidence(
        claim="Microsoft operates Azure portal",
        evidence_text="Cloud infrastructure provider.",
        source_url="https://microsoft.com",
        source_type=SourceType.OFFICIAL_COMPANY,
        observed_at=utc_now(),
        reliability_score=0.90,
        confidence_score=0.95,
        verification_status=VerificationStatus.VERIFIED,
        agent_name="company_research",
        content_hash="2" * 64,
    )

    result = await agent.execute(
        research_run_id=run_id,
        company_id=company_id,
        company_name="Microsoft Corp",
        domain="microsoft.com",
        context={"evidence": [ev1], "identity": identity},
    )

    assert isinstance(result, AgentResult)
    assert result.agent_name == "report_agent"
    assert result.status == "completed"
    assert result.metadata["canonical_name"] == "Microsoft Corp"
    assert result.metadata["official_domain"] == "microsoft.com"


# ------------------------------------------------------------
# 3. Complete 13-Section Report Structure Verification
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_report_agent_sections_structure():
    agent = ReportAgent()
    run_id = uuid4()
    company_id = uuid4()

    inp = AgentInput(
        research_run_id=run_id,
        company_id=company_id,
        company_name="Apple Inc.",
        company_url="https://apple.com",
    )

    result = await agent.execute(inp)
    content = result.metadata["report_content"]

    required_sections = [
        "overview",
        "official_resources",
        "identity_verification",
        "registration_findings",
        "certification_findings",
        "news_hiring",
        "technology_reputation",
        "trust_score",
        "confidence",
        "risk_analysis",
        "important_conclusions",
        "evidence",
        "references",
    ]

    for section in required_sections:
        assert section in content, f"Missing report section: {section}"


# ------------------------------------------------------------
# 4. Empty Evidence Handling
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_report_agent_empty_evidence():
    agent = ReportAgent()
    run_id = uuid4()
    company_id = uuid4()

    inp = AgentInput(
        research_run_id=run_id,
        company_id=company_id,
        company_name="Stealth Startup",
        company_url=None,
        previous_evidence=[],
    )

    result = await agent.execute(inp)
    content = result.metadata["report_content"]

    assert result.status == "completed"
    assert content["identity_verification"]["verified_claims_count"] == 0
    assert len(content["evidence"]) == 0
    assert len(content["references"]) == 0


# ------------------------------------------------------------
# 5. Error Boundary Handling
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_report_agent_error_boundary():
    agent = ReportAgent()
    invalid_dict = {"company_name": "TestCorp"}

    result = await agent.run(invalid_dict)
    assert result.status == "failed"
    assert result.agent_name == "report_agent"
    assert len(result.errors) > 0

from uuid import uuid4
import pytest
from app.research.agents.base import AgentInput, AgentResponse, AgentResult
from app.research.agents.verification_agent import VerificationAgent
from app.research.models import NormalizedEvidence
from app.schemas.evidence import SourceType, VerificationStatus


# ------------------------------------------------------------
# 1. Standard Execution via AgentInput (Verified Case)
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_verification_agent_verified_case():
    agent = VerificationAgent()
    run_id = uuid4()
    company_id = uuid4()

    inp = AgentInput(
        research_run_id=run_id,
        company_id=company_id,
        company_name="Microsoft Corporation",
        company_url="https://microsoft.com",
    )

    result = await agent.run(inp)

    assert isinstance(result, AgentResult)
    assert isinstance(result, AgentResponse)
    assert result.agent_name == "verification"
    assert result.status == "completed"
    assert result.research_run_id == run_id
    assert result.execution_time_ms > 0.0

    # Metadata checks
    assert result.metadata["domain_verified"] is True
    assert result.metadata["verification_state"] == "verified"
    assert result.metadata["verification_confidence"] >= 0.90

    # Findings checks
    assert len(result.findings) > 0
    assert result.findings[0]["verification_status"] == VerificationStatus.VERIFIED.value
    assert result.findings[0]["identity_status"] == "verified"
    assert len(result.findings[0]["reasons"]) > 0

    # Evidence checks
    assert len(result.evidence) == 2
    assert all(e.verification_status == VerificationStatus.VERIFIED for e in result.evidence)
    assert all(len(e.content_hash) == 64 for e in result.evidence)


# ------------------------------------------------------------
# 2. Legacy Signature Compatibility
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_verification_agent_legacy_signature():
    agent = VerificationAgent()
    run_id = uuid4()
    company_id = uuid4()

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
# 3. Missing URL -> Unable to Verify (No Domain Guessing)
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_verification_agent_missing_url_unable_to_verify():
    agent = VerificationAgent()
    run_id = uuid4()
    company_id = uuid4()

    inp = AgentInput(
        research_run_id=run_id,
        company_id=company_id,
        company_name="Anonymous Unlisted LLC",
        company_url=None,
    )

    result = await agent.execute(inp)

    assert result.status == "completed"
    assert result.metadata["domain_verified"] is False
    assert result.metadata["verification_state"] == "unable_to_verify"
    assert result.metadata["verification_confidence"] <= 0.50

    # Must contain exactly the UNABLE_TO_VERIFY evidence record
    assert len(result.evidence) == 1
    assert result.evidence[0].verification_status == VerificationStatus.UNABLE_TO_VERIFY

    # Findings verification
    assert result.findings[0]["verification_status"] == VerificationStatus.UNABLE_TO_VERIFY.value
    assert result.findings[0]["identity_status"] == "unverified"
    assert any("Official domain could not be verified" in w for w in result.warnings)


# ------------------------------------------------------------
# 4. Conflicting Domain Signals
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_verification_agent_conflicting_signals():
    agent = VerificationAgent()
    run_id = uuid4()
    company_id = uuid4()

    inp = AgentInput(
        research_run_id=run_id,
        company_id=company_id,
        company_name="Acme Inc",
        company_url="https://acme-pharma.com",
        context={"conflicting_domain": "acme-industrial.com operated by separate entity"},
    )

    result = await agent.execute(inp)

    assert result.status == "completed"
    assert result.metadata["domain_verified"] is False
    assert result.metadata["verification_state"] == "conflicting"
    assert result.metadata["verification_confidence"] < 0.50

    # Check evidence item status
    assert len(result.evidence) == 1
    assert result.evidence[0].verification_status == VerificationStatus.CONFLICTING
    assert result.findings[0]["verification_status"] == VerificationStatus.CONFLICTING.value
    assert result.findings[0]["identity_status"] == "conflicting"
    assert any("Identity conflict noted" in w for w in result.warnings)


# ------------------------------------------------------------
# 5. Error Boundary and Lifecycle
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_verification_agent_validation_error_boundary():
    agent = VerificationAgent()

    # Pass invalid dictionary input missing required fields
    invalid_dict = {"company_name": "TestCorp"}
    result = await agent.run(invalid_dict)

    assert result.status == "failed"
    assert result.agent_name == "verification"
    assert len(result.errors) > 0

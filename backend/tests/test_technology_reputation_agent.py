from uuid import uuid4
import pytest
from app.research.agents.base import AgentInput, AgentResponse, AgentResult
from app.research.agents.technology_reputation_agent import TechnologyReputationAgent
from app.research.models import NormalizedEvidence
from app.schemas.evidence import SourceType, VerificationStatus


# ------------------------------------------------------------
# 1. Standard Execution via AgentInput
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_technology_reputation_agent_standard_execution():
    agent = TechnologyReputationAgent()
    run_id = uuid4()
    company_id = uuid4()

    inp = AgentInput(
        research_run_id=run_id,
        company_id=company_id,
        company_name="Cloudflare Inc.",
        company_url="https://cloudflare.com",
    )

    result = await agent.run(inp)

    assert isinstance(result, AgentResult)
    assert isinstance(result, AgentResponse)
    assert result.agent_name == "technology_reputation"
    assert result.status == "completed"
    assert result.research_run_id == run_id
    assert result.execution_time_ms > 0.0

    # Check metadata
    assert result.metadata["tech_stack_verified"] is True
    assert result.metadata["reputation_verified"] is True
    assert len(result.findings) == 2
    assert len(result.evidence) == 2

    # Check categories
    categories = {f["category"] for f in result.findings}
    assert "technology" in categories
    assert "reputation" in categories


# ------------------------------------------------------------
# 2. Legacy Signature Compatibility
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_technology_reputation_agent_legacy_signature():
    agent = TechnologyReputationAgent()
    run_id = uuid4()
    company_id = uuid4()

    result = await agent.execute(
        research_run_id=run_id,
        company_id=company_id,
        company_name="Google",
        domain="google.com",
    )

    assert isinstance(result, AgentResult)
    assert result.agent_name == "technology_reputation"
    assert result.status == "completed"
    assert len(result.evidence) == 2


# ------------------------------------------------------------
# 3. Factual HTTPS Evidence (Does not equate to 'trusted')
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_technology_reputation_agent_factual_https_claim():
    agent = TechnologyReputationAgent()
    run_id = uuid4()
    company_id = uuid4()

    inp = AgentInput(
        research_run_id=run_id,
        company_id=company_id,
        company_name="Acme Tech",
        company_url="https://acme-tech.example",
    )

    result = await agent.execute(inp)
    tech_finding = next(f for f in result.findings if f["category"] == "technology")

    # Claim must state HTTPS availability without making wild trustworthiness leaps
    assert "HTTPS is available" in tech_finding["claim"]
    assert tech_finding["status"] == "https_active"
    assert tech_finding["metadata"]["https_available"] is True


# ------------------------------------------------------------
# 4. Missing Domain (No Domain Guessing)
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_technology_reputation_agent_missing_domain_no_guessing():
    agent = TechnologyReputationAgent()
    run_id = uuid4()
    company_id = uuid4()

    inp = AgentInput(
        research_run_id=run_id,
        company_id=company_id,
        company_name="Unknown Unregistered Co",
        company_url=None,
    )

    result = await agent.execute(inp)

    assert result.metadata["resolved_domain"] is None
    assert result.metadata["tech_stack_verified"] is False
    assert result.metadata["reputation_verified"] is False
    assert len(result.evidence) == 0
    assert any("No domain available" in w for w in result.warnings)


# ------------------------------------------------------------
# 5. Partial Failures (Tech or Reputation Fails)
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_technology_reputation_agent_partial_failures():
    agent = TechnologyReputationAgent()
    run_id = uuid4()
    company_id = uuid4()

    # Sub-case 1: Tech fails, reputation succeeds
    inp_tech_fail = AgentInput(
        research_run_id=run_id,
        company_id=company_id,
        company_name="Vercel",
        company_url="https://vercel.com",
        context={"fail_tech": True},
    )
    res_tech_fail = await agent.execute(inp_tech_fail)
    assert res_tech_fail.status == "partial"
    assert res_tech_fail.metadata["tech_stack_verified"] is False
    assert res_tech_fail.metadata["reputation_verified"] is True
    assert len(res_tech_fail.evidence) == 1
    assert any("Technology infrastructure evaluation encountered error" in w for w in res_tech_fail.warnings)

    # Sub-case 2: Reputation fails, tech succeeds
    inp_rep_fail = AgentInput(
        research_run_id=run_id,
        company_id=company_id,
        company_name="Vercel",
        company_url="https://vercel.com",
        context={"fail_reputation": True},
    )
    res_rep_fail = await agent.execute(inp_rep_fail)
    assert res_rep_fail.status == "partial"
    assert res_rep_fail.metadata["tech_stack_verified"] is True
    assert res_rep_fail.metadata["reputation_verified"] is False
    assert len(res_rep_fail.evidence) == 1
    assert any("Reputation evaluation encountered error" in w for w in res_rep_fail.warnings)


# ------------------------------------------------------------
# 6. Complete Failure Handling
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_technology_reputation_agent_total_failure():
    agent = TechnologyReputationAgent()
    run_id = uuid4()
    company_id = uuid4()

    inp_fail_all = AgentInput(
        research_run_id=run_id,
        company_id=company_id,
        company_name="DownCorp",
        company_url="https://downcorp.test",
        context={"fail_tech": True, "fail_reputation": True},
    )

    result = await agent.execute(inp_fail_all)

    assert result.status == "failed"
    assert len(result.evidence) == 0
    assert len(result.errors) > 0

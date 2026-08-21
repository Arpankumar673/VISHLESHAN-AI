from datetime import datetime, timezone
from uuid import uuid4
import pytest
from app.research.agents.base import AgentInput, AgentResponse, AgentResult
from app.research.agents.news_hiring_agent import NewsHiringAgent
from app.research.models import NormalizedEvidence
from app.schemas.evidence import SourceType, VerificationStatus


# ------------------------------------------------------------
# 1. Standard Execution via AgentInput
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_news_hiring_agent_standard_execution():
    agent = NewsHiringAgent()
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
    assert result.agent_name == "news_hiring"
    assert result.status == "completed"
    assert result.research_run_id == run_id
    assert result.execution_time_ms > 0.0

    # Verify both news and hiring channels were discovered
    assert result.metadata["hiring_channel_found"] is True
    assert result.metadata["news_channel_found"] is True
    assert len(result.findings) == 2
    assert len(result.evidence) == 2

    # Verify findings categorization
    categories = {f["category"] for f in result.findings}
    assert "hiring" in categories
    assert "news" in categories


# ------------------------------------------------------------
# 2. Legacy Signature Compatibility
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_news_hiring_agent_legacy_signature():
    agent = NewsHiringAgent()
    run_id = uuid4()
    company_id = uuid4()

    result = await agent.execute(
        research_run_id=run_id,
        company_id=company_id,
        company_name="Microsoft",
        domain="microsoft.com",
    )

    assert isinstance(result, AgentResult)
    assert result.agent_name == "news_hiring"
    assert result.status == "completed"
    assert len(result.evidence) == 2


# ------------------------------------------------------------
# 3. Publication Date Integrity (No Date Fabrication)
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_news_hiring_agent_publication_date_integrity():
    agent = NewsHiringAgent()
    run_id = uuid4()
    company_id = uuid4()

    # Case A: Date is NOT provided -> published_at MUST be None (no fabrication)
    inp_no_date = AgentInput(
        research_run_id=run_id,
        company_id=company_id,
        company_name="Stripe",
        company_url="https://stripe.com",
    )
    res_no_date = await agent.execute(inp_no_date)
    news_ev = next(e for e in res_no_date.evidence if e.source_type == SourceType.OFFICIAL_ANNOUNCEMENT)
    assert news_ev.published_at is None

    # Case B: Date IS provided in context -> published_at is parsed correctly
    inp_with_date = AgentInput(
        research_run_id=run_id,
        company_id=company_id,
        company_name="Stripe",
        company_url="https://stripe.com",
        context={"news_published_at": "2026-05-15T10:00:00Z"},
    )
    res_with_date = await agent.execute(inp_with_date)
    news_ev2 = next(e for e in res_with_date.evidence if e.source_type == SourceType.OFFICIAL_ANNOUNCEMENT)
    assert news_ev2.published_at is not None
    assert news_ev2.published_at.year == 2026


# ------------------------------------------------------------
# 4. Missing Domain (No Domain Guessing)
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_news_hiring_agent_missing_domain_no_guessing():
    agent = NewsHiringAgent()
    run_id = uuid4()
    company_id = uuid4()

    inp = AgentInput(
        research_run_id=run_id,
        company_id=company_id,
        company_name="Unlisted Stealther Inc",
        company_url=None,
    )

    result = await agent.execute(inp)

    assert result.metadata["resolved_domain"] is None
    assert result.metadata["hiring_channel_found"] is False
    assert result.metadata["news_channel_found"] is False
    assert len(result.evidence) == 0
    assert any("No official domain available" in w for w in result.warnings)


# ------------------------------------------------------------
# 5. Partial Failure Handling (Careers or News Fails)
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_news_hiring_agent_partial_failures():
    agent = NewsHiringAgent()
    run_id = uuid4()
    company_id = uuid4()

    # Sub-case 1: Careers fails, news succeeds
    inp_fail_careers = AgentInput(
        research_run_id=run_id,
        company_id=company_id,
        company_name="Amazon",
        company_url="https://amazon.com",
        context={"fail_careers": True},
    )
    res_careers_fail = await agent.execute(inp_fail_careers)
    assert res_careers_fail.status == "partial"
    assert res_careers_fail.metadata["hiring_channel_found"] is False
    assert res_careers_fail.metadata["news_channel_found"] is True
    assert len(res_careers_fail.evidence) == 1
    assert any("Careers channel collection encountered error" in w for w in res_careers_fail.warnings)

    # Sub-case 2: News fails, careers succeeds
    inp_fail_news = AgentInput(
        research_run_id=run_id,
        company_id=company_id,
        company_name="Amazon",
        company_url="https://amazon.com",
        context={"fail_news": True},
    )
    res_news_fail = await agent.execute(inp_fail_news)
    assert res_news_fail.status == "partial"
    assert res_news_fail.metadata["hiring_channel_found"] is True
    assert res_news_fail.metadata["news_channel_found"] is False
    assert len(res_news_fail.evidence) == 1
    assert any("News channel collection encountered error" in w for w in res_news_fail.warnings)


# ------------------------------------------------------------
# 6. Complete Failure Handling
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_news_hiring_agent_total_failure():
    agent = NewsHiringAgent()
    run_id = uuid4()
    company_id = uuid4()

    inp_fail_all = AgentInput(
        research_run_id=run_id,
        company_id=company_id,
        company_name="Offline Corp",
        company_url="https://offline.test",
        context={"fail_careers": True, "fail_news": True},
    )

    result = await agent.execute(inp_fail_all)

    assert result.status == "failed"
    assert len(result.evidence) == 0
    assert len(result.errors) > 0

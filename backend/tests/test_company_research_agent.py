from unittest.mock import AsyncMock, patch
from uuid import uuid4
import pytest
from app.research.agents.base import AgentInput, AgentResponse, AgentResult
from app.research.agents.company_research_agent import CompanyResearchAgent
from app.research.models import NormalizedEvidence, SourceFinding
from app.schemas.evidence import SourceType, VerificationStatus


# ------------------------------------------------------------
# 1. Standard Execution via AgentInput
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_company_research_agent_with_agent_input():
    agent = CompanyResearchAgent()
    run_id = uuid4()
    company_id = uuid4()

    inp = AgentInput(
        research_run_id=run_id,
        company_id=company_id,
        company_name="Microsoft Corporation",
        company_url="https://www.microsoft.com",
    )

    result = await agent.run(inp)

    assert isinstance(result, AgentResult)
    assert isinstance(result, AgentResponse)  # Backward-compatible check
    assert result.agent_name == "company_research"
    assert result.status in ("completed", "partial")
    assert result.research_run_id == run_id
    assert result.execution_time_ms > 0.0
    assert result.metadata["company_name"] == "Microsoft Corporation"
    assert result.metadata["resolved_domain"] == "microsoft.com"
    assert len(result.evidence) > 0
    assert all(isinstance(e, NormalizedEvidence) for e in result.evidence)
    assert all(len(e.content_hash) == 64 for e in result.evidence)


# ------------------------------------------------------------
# 2. Backward Compatibility with Legacy Positional / Keyword Arguments
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_company_research_agent_legacy_signature():
    agent = CompanyResearchAgent()
    run_id = uuid4()
    company_id = uuid4()

    result = await agent.execute(
        research_run_id=run_id,
        company_id=company_id,
        company_name="Apple Inc.",
        domain="apple.com",
    )

    assert isinstance(result, AgentResult)
    assert result.agent_name == "company_research"
    assert result.status in ("completed", "partial")
    assert result.research_run_id == run_id
    assert len(result.evidence) > 0


# ------------------------------------------------------------
# 3. Missing Domain & No Domain Guessing
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_company_research_agent_missing_url_no_guessing():
    agent = CompanyResearchAgent()
    run_id = uuid4()
    company_id = uuid4()

    # URL is completely omitted
    inp = AgentInput(
        research_run_id=run_id,
        company_id=company_id,
        company_name="Random Unlisted Entity",
        company_url=None,
    )

    result = await agent.execute(inp)

    # Domain MUST remain None — never guessed as randomunlistedentity.com
    assert result.metadata["resolved_domain"] is None
    assert any("Official corporate domain for 'Random Unlisted Entity' was not provided" in w for w in result.warnings)


# ------------------------------------------------------------
# 4. Mocked Adapters & Evidence Structuring
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_company_research_agent_structured_findings_and_evidence():
    mock_search = AsyncMock()
    mock_search.collect.return_value = [
        SourceFinding(
            claim="OpenAI specializes in artificial intelligence systems",
            evidence_text="OpenAI research lab developing frontier AI models.",
            source_url="https://en.wikipedia.org/wiki/OpenAI",
            source_title="OpenAI — Wikipedia",
            source_type=SourceType.NEWS,
        )
    ]

    mock_official = AsyncMock()
    mock_official.collect.return_value = [
        SourceFinding(
            claim="OpenAI operates official domain openai.com",
            evidence_text="Official homepage describing safety research and enterprise APIs.",
            source_url="https://openai.com",
            source_title="OpenAI Homepage",
            source_type=SourceType.OFFICIAL_COMPANY,
        )
    ]

    agent = CompanyResearchAgent(
        search_adapter=mock_search,
        official_adapter=mock_official,
    )

    run_id = uuid4()
    inp = AgentInput(
        research_run_id=run_id,
        company_id=uuid4(),
        company_name="OpenAI",
        company_url="https://openai.com",
    )

    result = await agent.execute(inp)

    assert result.status == "completed"
    assert len(result.evidence) == 2
    assert len(result.findings) == 2

    # Verify findings contain source provenance
    assert result.findings[0]["source"] == "public_search"
    assert result.findings[1]["source"] == "official_website"

    # Verify reliability tiers
    ev_types = {e.source_type: e.reliability_score for e in result.evidence}
    assert ev_types[SourceType.NEWS] == 0.80
    assert ev_types[SourceType.OFFICIAL_COMPANY] == 0.90


# ------------------------------------------------------------
# 5. Resilience: Partial Failure when Public Search Fails
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_company_research_agent_partial_failure_resilience():
    mock_search = AsyncMock()
    mock_search.collect.side_effect = ConnectionError("Public API unreachable")

    mock_official = AsyncMock()
    mock_official.collect.return_value = [
        SourceFinding(
            claim="GitHub operates official web portal",
            evidence_text="Code hosting platform.",
            source_url="https://github.com",
            source_title="GitHub",
            source_type=SourceType.OFFICIAL_COMPANY,
        )
    ]

    agent = CompanyResearchAgent(
        search_adapter=mock_search,
        official_adapter=mock_official,
    )

    inp = AgentInput(
        research_run_id=uuid4(),
        company_id=uuid4(),
        company_name="GitHub",
        company_url="https://github.com",
    )

    result = await agent.execute(inp)

    # Should succeed partially with OfficialWebsite evidence without crashing
    assert result.status == "partial"
    assert len(result.evidence) == 1
    assert any("Public search query encountered error" in w for w in result.warnings)


# ------------------------------------------------------------
# 6. Total Source Failure Handled Structurally
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_company_research_agent_total_failure_handling():
    mock_search = AsyncMock()
    mock_search.collect.side_effect = ConnectionError("DNS failure")

    mock_official = AsyncMock()
    mock_official.collect.side_effect = TimeoutError("HTTP timeout")

    agent = CompanyResearchAgent(
        search_adapter=mock_search,
        official_adapter=mock_official,
    )

    inp = AgentInput(
        research_run_id=uuid4(),
        company_id=uuid4(),
        company_name="NonExistentCorp",
        company_url="https://nonexistent.test",
    )

    result = await agent.execute(inp)

    assert result.status == "failed"
    assert len(result.evidence) == 0
    assert len(result.errors) > 0

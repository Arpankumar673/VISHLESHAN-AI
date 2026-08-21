import asyncio
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from uuid import uuid4
import pytest
from app.research.agents.base import AgentInput, AgentResult
from app.research.agents.orchestrator import MultiAgentOrchestrator
from app.research.graph.nodes import (
    node_company_research,
    node_evidence_trust,
    node_news_hiring,
    node_persist_results,
    node_report_agent,
    node_resolve_identity,
    node_risk_analysis,
    node_technology_reputation,
    node_verification,
)
from app.research.graph.state import (
    ResearchGraphState,
    add_evidence,
    add_findings,
    add_strings,
    update_agent_results,
)
from app.research.graph.workflow import research_graph
from app.research.models import IdentityResult, NormalizedEvidence, ResearchEngineResult
from app.schemas.evidence import SourceType, VerificationStatus


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


# ------------------------------------------------------------
# 1. State Reducers Unit Verification
# ------------------------------------------------------------
def test_langgraph_state_reducers():
    # Test add_strings
    assert add_strings(["w1"], ["w2"]) == ["w1", "w2"]
    assert add_strings(None, ["w2"]) == ["w2"]
    assert add_strings(["w1"], None) == ["w1"]

    # Test update_agent_results
    r1 = update_agent_results({"a": 1}, {"b": 2})
    assert r1 == {"a": 1, "b": 2}

    # Test add_evidence
    ev1 = NormalizedEvidence(
        claim="Claim 1",
        evidence_text="Text 1",
        source_url="https://test.com",
        source_type=SourceType.OFFICIAL_COMPANY,
        observed_at=utc_now(),
        reliability_score=0.90,
        confidence_score=0.90,
        verification_status=VerificationStatus.VERIFIED,
        agent_name="company_research",
        content_hash="1" * 64,
    )
    assert len(add_evidence([ev1], [ev1])) == 2


# ------------------------------------------------------------
# 2. Identity Unresolved Fallback Safety (No Fake Domain)
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_langgraph_identity_unresolved_fallback_safety():
    run_id = uuid4()
    company_id = uuid4()

    state: ResearchGraphState = {
        "research_run_id": run_id,
        "company_id": company_id,
        "company_name": "Unlisted Stealther Inc",
        "company_url": None,
        "correlation_id": str(run_id),
        "identity": None,
        "identity_status": "unverified",
        "agent_results": {},
        "evidence": [],
        "findings": [],
        "trust_score": None,
        "risk_summary": None,
        "report_content": None,
        "report_id": None,
        "warnings": [],
        "errors": [],
        "status": "running",
    }

    # Mock resolver to raise exception simulating resolution failure
    with patch("app.research.graph.nodes.IdentityResolver.resolve", side_effect=Exception("API lookup timeout")):
        result_dict = await node_resolve_identity(state)

        assert result_dict["identity_status"] == "unresolved"
        assert result_dict["identity"].official_domain is None
        assert result_dict["identity"].canonical_name == "Unlisted Stealther Inc"
        assert any("Identity resolution could not verify an official corporate domain" in w for w in result_dict["warnings"])


# ------------------------------------------------------------
# 3. End-to-End LangGraph Workflow Execution
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_langgraph_workflow_end_to_end_success():
    run_id = uuid4()
    company_id = uuid4()

    initial_state = {
        "research_run_id": run_id,
        "company_id": company_id,
        "company_name": "Google LLC",
        "company_url": "https://google.com",
        "correlation_id": str(run_id),
        "identity": None,
        "identity_status": "unverified",
        "agent_results": {},
        "evidence": [],
        "findings": [],
        "trust_score": None,
        "risk_summary": None,
        "report_content": None,
        "report_id": None,
        "warnings": [],
        "errors": [],
        "status": "running",
    }

    # Mock Supabase database persistence node to avoid external network calls during pytest
    with patch("app.research.graph.nodes.get_supabase_client") as mock_supa:
        mock_table = MagicMock()
        mock_table.update.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
        mock_table.insert.return_value.execute.return_value = MagicMock(data=[{"id": str(uuid4())}])
        mock_table.upsert.return_value.execute.return_value = MagicMock(data=[])
        mock_supa.return_value.table.return_value = mock_table

        final_state = await research_graph.ainvoke(initial_state)

        assert final_state["status"] in ("completed", "partial")
        assert final_state["identity"] is not None
        assert len(final_state["evidence"]) > 0
        assert final_state["report_content"] is not None
        assert "overview" in final_state["report_content"]


# ------------------------------------------------------------
# 4. MultiAgentOrchestrator.execute_langgraph_run Interface
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_orchestrator_execute_langgraph_run():
    orchestrator = MultiAgentOrchestrator()
    run_id = uuid4()
    company_id = uuid4()

    with patch("app.research.agents.orchestrator.get_supabase_client") as mock_supa, \
         patch("app.research.graph.nodes.get_supabase_client") as mock_node_supa:

        mock_table = MagicMock()
        mock_table.update.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
        mock_table.insert.return_value.execute.return_value = MagicMock(data=[{"id": str(uuid4())}])
        mock_table.upsert.return_value.execute.return_value = MagicMock(data=[])

        mock_supa.return_value.table.return_value = mock_table
        mock_node_supa.return_value.table.return_value = mock_table

        result = await orchestrator.execute_langgraph_run(
            research_run_id=run_id,
            company_id=company_id,
            company_name="Microsoft",
            company_url="https://microsoft.com",
        )

        assert isinstance(result, ResearchEngineResult)
        assert result.research_run_id == run_id
        assert result.company_id == company_id
        assert result.status in ("completed", "partial")
        assert len(result.evidence_items) > 0


# ------------------------------------------------------------
# 5. Branch Failure Isolation & Partial Status
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_langgraph_branch_failure_isolation():
    run_id = uuid4()
    company_id = uuid4()

    state: ResearchGraphState = {
        "research_run_id": run_id,
        "company_id": company_id,
        "company_name": "TestCorp",
        "company_url": "https://test.com",
        "correlation_id": str(run_id),
        "identity": IdentityResult(canonical_name="TestCorp", official_domain="test.com"),
        "identity_status": "verified",
        "agent_results": {},
        "evidence": [],
        "findings": [],
        "trust_score": None,
        "risk_summary": None,
        "report_content": None,
        "report_id": None,
        "warnings": [],
        "errors": [],
        "status": "running",
    }

    # Simulate failure in CompanyResearchAgent node
    with patch("app.research.graph.nodes.CompanyResearchAgent.run", side_effect=Exception("Network connection reset")):
        result_dict = await node_company_research(state)

        assert "errors" in result_dict
        assert len(result_dict["errors"]) > 0
        assert "CompanyResearchAgent failed" in result_dict["errors"][0]
        assert result_dict["agent_results"]["company_research"].status == "failed"


# ------------------------------------------------------------
# 6. Orchestrator Mode Dispatch Verification (langgraph, local)
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_orchestrator_mode_dispatch():
    from app.core.config import settings
    from app.services.research_service import ResearchService

    # 1. Verify default mode is langgraph
    assert settings.RESEARCH_ORCHESTRATOR_MODE == "langgraph"

    mock_orchestrator = MagicMock()
    mock_orchestrator.execute_langgraph_run = MagicMock(return_value=asyncio.Future())
    mock_orchestrator.execute_langgraph_run.return_value.set_result(None)
    mock_orchestrator.execute_run = MagicMock(return_value=asyncio.Future())
    mock_orchestrator.execute_run.return_value.set_result(None)

    service = ResearchService(
        multi_agent_orchestrator=mock_orchestrator,
    )

    run_id = uuid4()
    company_id = uuid4()

    # Test explicit langgraph mode
    with patch.object(settings, "RESEARCH_ORCHESTRATOR_MODE", "langgraph"):
        await service._dispatch_research_run(run_id, company_id, "Google LLC", "https://google.com")
        mock_orchestrator.execute_langgraph_run.assert_called_once()

    mock_orchestrator.reset_mock()

    # Test explicit local mode
    with patch.object(settings, "RESEARCH_ORCHESTRATOR_MODE", "local"):
        await service._dispatch_research_run(run_id, company_id, "Google LLC", "https://google.com")
        mock_orchestrator.execute_run.assert_called_once()
        mock_orchestrator.execute_langgraph_run.assert_not_called()



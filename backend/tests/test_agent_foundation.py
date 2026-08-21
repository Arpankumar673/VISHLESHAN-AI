import asyncio
from datetime import datetime, timezone
from uuid import UUID, uuid4
import pytest
from pydantic import ValidationError
from app.research.agents.base import (
    AgentInput,
    AgentResponse,
    AgentResult,
    AgentStatus,
    BaseAgent,
    BaseTool,
)
from app.research.agents.errors import (
    AgentException,
    AgentSourceError,
    AgentTimeoutError,
    AgentValidationError,
)
from app.research.models import NormalizedEvidence
from app.schemas.evidence import SourceType, VerificationStatus


# ------------------------------------------------------------
# 1. AgentInput Validation & Domain Parsing
# ------------------------------------------------------------
def test_valid_agent_input():
    run_id = uuid4()
    company_id = uuid4()
    inp = AgentInput(
        research_run_id=run_id,
        company_id=company_id,
        company_name="Tata Consultancy Services",
        company_url="https://www.tcs.com/careers",
        context={"depth": "full"},
        correlation_id="req-12345",
    )

    assert inp.research_run_id == run_id
    assert inp.company_id == company_id
    assert inp.company_name == "Tata Consultancy Services"
    assert inp.company_url == "https://www.tcs.com/careers"
    assert inp.domain == "tcs.com"
    assert inp.context["depth"] == "full"
    assert inp.correlation_id == "req-12345"
    assert isinstance(inp.previous_findings, list)
    assert isinstance(inp.previous_evidence, list)


def test_agent_input_domain_property_variations():
    run_id = uuid4()
    comp_id = uuid4()

    # Case 1: Standard HTTPS URL
    inp1 = AgentInput(research_run_id=run_id, company_id=comp_id, company_name="OpenAI", company_url="https://openai.com")
    assert inp1.domain == "openai.com"

    # Case 2: URL with www and subpath
    inp2 = AgentInput(research_run_id=run_id, company_id=comp_id, company_name="Google", company_url="https://www.google.com/about")
    assert inp2.domain == "google.com"

    # Case 3: Raw domain string without scheme
    inp3 = AgentInput(research_run_id=run_id, company_id=comp_id, company_name="Microsoft", company_url="microsoft.com")
    assert inp3.domain == "microsoft.com"

    # Case 4: None company_url -> domain MUST be None (DO NOT guess or invent .com)
    inp4 = AgentInput(research_run_id=run_id, company_id=comp_id, company_name="Acme Corp", company_url=None)
    assert inp4.domain is None

    # Case 5: Empty string company_url -> domain MUST be None
    inp5 = AgentInput(research_run_id=run_id, company_id=comp_id, company_name="Acme Corp", company_url="")
    assert inp5.domain is None


def test_agent_input_validation_failures():
    run_id = uuid4()
    comp_id = uuid4()

    # Missing company_name
    with pytest.raises(ValidationError):
        AgentInput(research_run_id=run_id, company_id=comp_id, company_name="")

    # Missing research_run_id
    with pytest.raises(ValidationError):
        AgentInput(company_id=comp_id, company_name="Infosys")  # type: ignore

    # Missing company_id
    with pytest.raises(ValidationError):
        AgentInput(research_run_id=run_id, company_name="Infosys")  # type: ignore


# ------------------------------------------------------------
# 2. EvidenceItem & NormalizedEvidence Compatibility
# ------------------------------------------------------------
def test_evidence_item_compatibility():
    now = datetime.now(timezone.utc)
    ev = NormalizedEvidence(
        claim="TCS maintains official research laboratory",
        evidence_text="Verified enterprise research unit active in Pune.",
        source_url="https://tcs.com/research",
        source_title="TCS Research",
        source_type=SourceType.OFFICIAL_COMPANY,
        published_at=None,
        observed_at=now,
        reliability_score=0.90,
        confidence_score=0.95,
        verification_status=VerificationStatus.VERIFIED,
        agent_name="company_research",
        content_hash="a" * 64,
    )

    result = AgentResult(
        agent_name="company_research",
        status=AgentStatus.COMPLETED.value,
        research_run_id=uuid4(),
        evidence=[ev],
    )

    assert len(result.evidence) == 1
    assert result.evidence[0].claim == "TCS maintains official research laboratory"
    assert result.evidence[0].reliability_score == 0.90


# ------------------------------------------------------------
# 3. AgentResult Serialization & Backward Compatibility
# ------------------------------------------------------------
def test_agent_result_states_and_serialization():
    run_id = uuid4()

    # Success State
    res_success = AgentResult(
        agent_name="verification",
        agent_version="1.0",
        status=AgentStatus.COMPLETED.value,
        research_run_id=run_id,
        findings=[{"key": "verified_domain"}],
        metadata={"step": 1},
    )
    dumped = res_success.model_dump()
    assert dumped["status"] == "completed"
    assert dumped["agent_name"] == "verification"
    assert dumped["research_run_id"] == run_id

    # Partial State
    res_partial = AgentResult(
        agent_name="verification",
        status=AgentStatus.PARTIAL.value,
        research_run_id=run_id,
        warnings=["Some records unverified"],
    )
    assert res_partial.status == "partial"
    assert len(res_partial.warnings) == 1

    # Failed State
    res_failed = AgentResult(
        agent_name="verification",
        status=AgentStatus.FAILED.value,
        research_run_id=run_id,
        errors=["DNS timeout"],
    )
    assert res_failed.status == "failed"
    assert len(res_failed.errors) == 1

    # Verify AgentResponse is an exact alias/subclass of AgentResult
    assert AgentResponse is AgentResult


# ------------------------------------------------------------
# 4. BaseAgent Lifecycle, Timing & Error Boundary
# ------------------------------------------------------------
class SampleWorkingAgent(BaseAgent):
    def __init__(self):
        super().__init__(agent_name="sample_working", agent_description="Testing working flow")

    async def execute(self, input_data: AgentInput) -> AgentResult:
        await asyncio.sleep(0.01)  # Simulate brief async task
        return AgentResult(
            agent_name=self.agent_name,
            status=AgentStatus.COMPLETED.value,
            research_run_id=input_data.research_run_id,
            findings=[{"item": "found"}],
        )


class SampleTimeoutAgent(BaseAgent):
    def __init__(self):
        super().__init__(agent_name="sample_timeout", agent_description="Testing timeout error")

    async def execute(self, input_data: AgentInput) -> AgentResult:
        raise AgentTimeoutError(f"HTTP request timed out after 5.0s for {input_data.company_name}")


class SampleFailingAgent(BaseAgent):
    def __init__(self):
        super().__init__(agent_name="sample_failing", agent_description="Testing unexpected exception")

    async def execute(self, input_data: AgentInput) -> AgentResult:
        raise ValueError("Unexpected downstream parsing error")


@pytest.mark.asyncio
async def test_base_agent_successful_run():
    agent = SampleWorkingAgent()
    inp = AgentInput(
        research_run_id=uuid4(),
        company_id=uuid4(),
        company_name="Infosys",
        company_url="https://infosys.com",
    )

    result = await agent.run(inp)

    assert result.status == "completed"
    assert result.agent_name == "sample_working"
    assert result.execution_time_ms > 0.0
    assert result.completed_at is not None
    assert len(result.findings) == 1


@pytest.mark.asyncio
async def test_base_agent_timeout_error_boundary():
    agent = SampleTimeoutAgent()
    inp = AgentInput(
        research_run_id=uuid4(),
        company_id=uuid4(),
        company_name="Wipro",
    )

    # Should NOT raise unhandled exception, but return structured failed AgentResult
    result = await agent.run(inp)

    assert result.status == "failed"
    assert result.agent_name == "sample_timeout"
    assert len(result.errors) == 1
    assert "timed out" in result.errors[0]
    assert result.execution_time_ms > 0.0


@pytest.mark.asyncio
async def test_base_agent_unexpected_error_boundary():
    agent = SampleFailingAgent()
    inp = AgentInput(
        research_run_id=uuid4(),
        company_id=uuid4(),
        company_name="HCL Tech",
    )

    # Should safely catch unexpected ValueError and return status="failed"
    result = await agent.run(inp)

    assert result.status == "failed"
    assert result.agent_name == "sample_failing"
    assert len(result.errors) == 1
    assert "Unexpected downstream parsing error" in result.errors[0]


@pytest.mark.asyncio
async def test_base_agent_dict_input_and_validation_error():
    agent = SampleWorkingAgent()
    run_id = uuid4()
    comp_id = uuid4()

    # Valid dict input
    dict_input = {
        "research_run_id": run_id,
        "company_id": comp_id,
        "company_name": "Cognizant",
    }
    res = await agent.run(dict_input)
    assert res.status == "completed"
    assert res.research_run_id == run_id

    # Invalid dict input (missing company_name)
    invalid_dict = {
        "research_run_id": run_id,
        "company_id": comp_id,
    }
    res_err = await agent.run(invalid_dict)
    assert res_err.status == "failed"
    assert len(res_err.errors) > 0


# ------------------------------------------------------------
# 5. BaseTool Interface
# ------------------------------------------------------------
class SampleSearchTool(BaseTool):
    def __init__(self):
        super().__init__(name="sample_search", description="Search tool for testing")

    async def execute(self, query: str) -> dict:
        return {"query": query, "status": "ok"}


@pytest.mark.asyncio
async def test_base_tool_execution():
    tool = SampleSearchTool()
    assert tool.name == "sample_search"
    out = await tool.run(query="Google")
    assert out == {"query": "Google", "status": "ok"}


# ------------------------------------------------------------
# 6. Error Taxonomy
# ------------------------------------------------------------
def test_agent_error_taxonomy():
    exc = AgentSourceError("API endpoint unavailable", details={"url": "https://api.test"})
    assert isinstance(exc, AgentException)
    assert exc.code == "AGENT_SOURCE_ERROR"
    assert exc.status_code == 502
    assert exc.details == {"url": "https://api.test"}


# ------------------------------------------------------------
# 7. LangGraph State Round-Trip Compatibility
# ------------------------------------------------------------
def test_langgraph_state_roundtrip():
    run_id = uuid4()
    comp_id = uuid4()

    # Create input and serialize to LangGraph state dict
    state_input = AgentInput(
        research_run_id=run_id,
        company_id=comp_id,
        company_name="NVIDIA",
        company_url="https://nvidia.com",
        context={"pipeline": "langgraph"},
    )
    state_dict = state_input.model_dump()

    # Reconstitute from state dict
    reconstituted = AgentInput.model_validate(state_dict)
    assert reconstituted.research_run_id == run_id
    assert reconstituted.company_name == "NVIDIA"
    assert reconstituted.domain == "nvidia.com"
    assert reconstituted.context["pipeline"] == "langgraph"

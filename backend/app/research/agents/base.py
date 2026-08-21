import time
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field
from app.core.logging import logger
from app.research.agents.errors import (
    AgentException,
    AgentSourceError,
    AgentTimeoutError,
    AgentValidationError,
)
from app.research.models import NormalizedEvidence, SourceFinding


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class AgentStatus(str, Enum):
    """Execution status for agent outcomes."""
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"


class AgentInput(BaseModel):
    """
    Structured input contract for all specialized agents in Vishleshan AI.
    Compatible with LangGraph state channels and parallel async execution.
    """
    research_run_id: UUID = Field(..., description="Unique research execution run identifier")
    company_id: UUID = Field(..., description="Target corporate entity ID in Supabase")
    company_name: str = Field(..., min_length=1, description="Official or trading name of target organization")
    company_url: Optional[str] = Field(default=None, description="Optional corporate domain or website URL")
    context: Dict[str, Any] = Field(default_factory=dict, description="Execution context passed from prior nodes")
    previous_findings: List[Dict[str, Any]] = Field(default_factory=list, description="Raw findings accumulated by prior agents")
    previous_evidence: List[NormalizedEvidence] = Field(default_factory=list, description="Corroborated evidence items accumulated so far")
    correlation_id: Optional[str] = Field(default=None, description="Traceability / request correlation ID")

    @property
    def domain(self) -> Optional[str]:
        """
        Safely extracts and normalizes the hostname from company_url if present.
        Returns None if company_url is missing or empty.
        Does NOT invent, guess, or assume a domain from the company name.
        """
        if not self.company_url:
            return None

        raw = self.company_url.strip().lower()
        if not raw:
            return None

        # Ensure scheme for urlparse if not provided
        if not raw.startswith("http://") and not raw.startswith("https://"):
            raw = f"https://{raw}"

        try:
            parsed = urlparse(raw)
            hostname = parsed.hostname or parsed.netloc or parsed.path.split("/")[0]
            if not hostname:
                return None
            hostname = hostname.strip().lower()
            if hostname.startswith("www."):
                hostname = hostname[4:]
            hostname = hostname.rstrip("/.")
            return hostname if hostname else None
        except Exception:
            return None

    model_config = ConfigDict(extra="allow", arbitrary_types_allowed=True)


class AgentResult(BaseModel):
    """
    Standardized, serializable execution envelope returned by all agents.
    Full backward-compatibility superset of legacy AgentResponse.
    """
    agent_name: str = Field(..., description="Registered identifier of the executing agent")
    agent_version: str = Field(default="1.0", description="Semver version of agent implementation")
    status: str = Field(..., description="'completed', 'partial', or 'failed'")
    research_run_id: UUID = Field(..., description="Associated research execution run ID")
    findings: List[Dict[str, Any]] = Field(default_factory=list, description="Raw structured findings collected")
    evidence: List[NormalizedEvidence] = Field(default_factory=list, description="Normalized and hashed evidence items")
    warnings: List[str] = Field(default_factory=list, description="Non-fatal warnings encountered")
    errors: List[str] = Field(default_factory=list, description="Error messages encountered during run")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Agent-specific execution metadata")
    executed_at: datetime = Field(default_factory=utc_now, description="Timestamp when execution completed")
    started_at: datetime = Field(default_factory=utc_now, description="Timestamp when execution began")
    completed_at: Optional[datetime] = Field(default=None, description="Completion timestamp")
    execution_time_ms: float = Field(default=0.0, description="Elapsed execution wall-clock time in milliseconds")

    model_config = ConfigDict(extra="allow", arbitrary_types_allowed=True)


# Backward-compatible alias for existing codebase imports
AgentResponse = AgentResult


class BaseTool(ABC):
    """
    Abstract base class for reusable tools and data retrieval utilities.
    """

    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description

    @abstractmethod
    async def execute(self, **kwargs: Any) -> Any:
        """Execute tool logic asynchronously."""
        pass

    async def run(self, **kwargs: Any) -> Any:
        """Resilient tool execution wrapper."""
        return await self.execute(**kwargs)


class BaseAgent(ABC):
    """
    Abstract base class defining the standard interface, execution lifecycle,
    and non-fatal error boundary for all specialized agents in Vishleshan AI.
    """

    def __init__(
        self,
        agent_name: str,
        agent_description: str = "",
        agent_version: str = "1.0",
    ):
        self.agent_name = agent_name
        self.agent_description = agent_description
        self.agent_version = agent_version

    @abstractmethod
    async def execute(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> AgentResult:
        """
        Subclasses implement their specialized research logic here.
        Supports both modern `execute(input: AgentInput)` and legacy positional signatures.
        """
        pass

    async def run(
        self,
        input_data: Union[AgentInput, Dict[str, Any]],
    ) -> AgentResult:
        """
        Safe execution lifecycle wrapper:
        - Validates input into AgentInput
        - Measures wall-clock execution time
        - Captures timeouts, source errors, and unexpected exceptions
        - Returns structured AgentResult with status='failed' instead of crashing pipeline
        """
        start_time = time.perf_counter()
        started_at = utc_now()

        # Validate input
        if isinstance(input_data, dict):
            try:
                agent_input = AgentInput.model_validate(input_data)
            except Exception as val_exc:
                exec_time = (time.perf_counter() - start_time) * 1000
                logger.error(f"[{self.agent_name}] Input validation error: {val_exc}")
                return AgentResult(
                    agent_name=self.agent_name,
                    agent_version=self.agent_version,
                    status=AgentStatus.FAILED.value,
                    research_run_id=input_data.get("research_run_id") or UUID(int=0),
                    errors=[f"Validation error: {val_exc}"],
                    started_at=started_at,
                    completed_at=utc_now(),
                    execution_time_ms=round(exec_time, 2),
                )
        else:
            agent_input = input_data

        run_id = agent_input.research_run_id

        try:
            # Delegate to specialized execute implementation
            result = await self.execute(agent_input)

            exec_time = (time.perf_counter() - start_time) * 1000
            result.started_at = started_at
            result.completed_at = utc_now()
            result.execution_time_ms = round(exec_time, 2)
            return result

        except AgentTimeoutError as timeout_exc:
            exec_time = (time.perf_counter() - start_time) * 1000
            logger.warning(f"[{self.agent_name}] Timeout for run {run_id}: {timeout_exc}")
            return AgentResult(
                agent_name=self.agent_name,
                agent_version=self.agent_version,
                status=AgentStatus.FAILED.value,
                research_run_id=run_id,
                errors=[str(timeout_exc)],
                started_at=started_at,
                completed_at=utc_now(),
                execution_time_ms=round(exec_time, 2),
            )

        except (AgentSourceError, AgentValidationError, AgentException) as agent_exc:
            exec_time = (time.perf_counter() - start_time) * 1000
            logger.warning(f"[{self.agent_name}] Agent error for run {run_id}: {agent_exc}")
            return AgentResult(
                agent_name=self.agent_name,
                agent_version=self.agent_version,
                status=AgentStatus.FAILED.value,
                research_run_id=run_id,
                errors=[str(agent_exc)],
                started_at=started_at,
                completed_at=utc_now(),
                execution_time_ms=round(exec_time, 2),
            )

        except Exception as exc:
            exec_time = (time.perf_counter() - start_time) * 1000
            logger.exception(f"[{self.agent_name}] Unhandled exception in run {run_id}: {exc}")
            return AgentResult(
                agent_name=self.agent_name,
                agent_version=self.agent_version,
                status=AgentStatus.FAILED.value,
                research_run_id=run_id,
                errors=[f"Unhandled exception: {exc}"],
                started_at=started_at,
                completed_at=utc_now(),
                execution_time_ms=round(exec_time, 2),
            )

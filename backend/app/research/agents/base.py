from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, Field
from app.research.models import NormalizedEvidence, SourceFinding


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class AgentResponse(BaseModel):
    """Standard envelope returned by all specialized research agents."""
    agent_name: str
    agent_version: str = "1.0"
    status: str = Field(..., description="'completed', 'partial', or 'failed'")
    research_run_id: UUID
    findings: List[Dict[str, Any]] = Field(default_factory=list)
    evidence: List[NormalizedEvidence] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    executed_at: datetime = Field(default_factory=utc_now)


class BaseAgent(ABC):
    """Abstract base class defining the standard interface for all specialized agents."""

    def __init__(self, agent_name: str, agent_version: str = "1.0"):
        self.agent_name = agent_name
        self.agent_version = agent_version

    @abstractmethod
    async def execute(
        self,
        research_run_id: UUID,
        company_id: UUID,
        company_name: str,
        domain: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> AgentResponse:
        """Execute agent research logic with bounded error handling."""
        pass

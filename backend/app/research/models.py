from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, Field
from app.schemas.evidence import SourceType, VerificationStatus


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class SourceFinding(BaseModel):
    """Raw finding extracted from an external public source."""
    claim: str
    evidence_text: str
    source_url: Optional[str] = None
    source_title: Optional[str] = None
    source_type: SourceType
    published_at: Optional[datetime] = None
    observed_at: datetime = Field(default_factory=utc_now)
    raw_metadata: Dict[str, Any] = Field(default_factory=dict)


class IdentityResult(BaseModel):
    """Resolved company identity metadata."""
    canonical_name: str
    official_domain: Optional[str] = None
    official_website: Optional[str] = None
    description: Optional[str] = None
    industry: Optional[str] = None
    headquarters: Optional[str] = None
    identifiers: List[Dict[str, Any]] = Field(default_factory=list)


class NormalizedEvidence(BaseModel):
    """Fully normalized and hashed evidence entity ready for persistence."""
    claim: str
    evidence_text: str
    source_url: Optional[str] = ""
    source_title: Optional[str] = None
    source_type: SourceType
    published_at: Optional[datetime] = None
    observed_at: datetime
    reliability_score: float = Field(ge=0.0, le=1.0)
    confidence_score: float = Field(ge=0.0, le=1.0)
    verification_status: VerificationStatus
    agent_name: str = "company_research_v1"
    content_hash: str


class ResearchEngineResult(BaseModel):
    """Overall outcome of a completed or partial research run."""
    research_run_id: UUID
    company_id: UUID
    identity: IdentityResult
    evidence_items: List[NormalizedEvidence]
    report_id: Optional[UUID] = None
    status: str = "completed"
    error_message: Optional[str] = None

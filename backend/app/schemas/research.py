from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.company import CompanyResponse
from app.schemas.trust import TrustScoreResponse


class ResearchStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"


class StartResearchRequest(BaseModel):
    company_name: str = Field(..., min_length=1, max_length=255, description="Name of company to investigate")
    company_url: Optional[str] = Field(default=None, max_length=255, description="Optional corporate domain URL")


class StartResearchResponse(BaseModel):
    research_run_id: UUID
    company_id: UUID
    status: ResearchStatus = ResearchStatus.QUEUED


class ResearchRunResponse(BaseModel):
    research_run_id: UUID
    company_id: UUID
    user_id: Optional[UUID] = None
    status: ResearchStatus
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    company: Optional[CompanyResponse] = None
    trust_score: Optional[TrustScoreResponse] = None

    model_config = ConfigDict(from_attributes=True)

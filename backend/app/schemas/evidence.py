from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class VerificationStatus(str, Enum):
    VERIFIED = "verified"
    UNVERIFIED = "unverified"
    CONFLICTING = "conflicting"
    UNABLE_TO_VERIFY = "unable_to_verify"


class SourceType(str, Enum):
    GOVERNMENT = "government"
    REGULATOR = "regulator"
    CERTIFICATION_BODY = "certification_body"
    OFFICIAL_COMPANY = "official_company"
    OFFICIAL_CAREERS = "official_careers"
    OFFICIAL_ANNOUNCEMENT = "official_announcement"
    NEWS = "news"
    PROFESSIONAL_NETWORK = "professional_network"
    EMPLOYEE_REVIEW = "employee_review"
    FORUM = "forum"
    BLOG = "blog"
    OTHER = "other"


class EvidenceBase(BaseModel):
    claim: str = Field(..., min_length=1)
    evidence_text: str = Field(..., min_length=1)
    source_url: str = Field(..., min_length=1)
    source_title: Optional[str] = None
    source_type: SourceType
    published_at: Optional[datetime] = None
    observed_at: datetime = Field(default_factory=utc_now)
    reliability_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    confidence_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    verification_status: VerificationStatus = VerificationStatus.UNVERIFIED
    agent_name: Optional[str] = None
    content_hash: Optional[str] = None


class EvidenceCreate(EvidenceBase):
    company_id: UUID
    research_run_id: UUID


class EvidenceResponse(EvidenceBase):
    id: UUID
    company_id: UUID
    research_run_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

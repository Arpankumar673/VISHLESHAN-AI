from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class TrustScoreResponse(BaseModel):
    id: UUID
    company_id: UUID
    research_run_id: UUID
    score: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    risk_level: Optional[RiskLevel] = RiskLevel.UNKNOWN
    evidence_coverage: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    algorithm_version: str = "v1.0"
    explanation: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.company import CompanyResponse
from app.schemas.trust import TrustScoreResponse


class ReportResponse(BaseModel):
    id: UUID
    company_id: UUID
    research_run_id: UUID
    title: str
    content: Dict[str, Any] = Field(default_factory=dict)
    report_version: str = "1.0"
    created_at: datetime
    updated_at: datetime
    company: Optional[CompanyResponse] = None
    trust_score: Optional[TrustScoreResponse] = None

    model_config = ConfigDict(from_attributes=True)

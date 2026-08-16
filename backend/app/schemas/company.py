from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class CompanyIdentifierResponse(BaseModel):
    id: UUID
    company_id: UUID
    identifier_type: str
    identifier_value: str
    source_url: Optional[str] = None
    confidence: Optional[float] = Field(default=None, ge=0, le=1)
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CompanyBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Full registered or trade name")
    official_domain: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = None
    industry: Optional[str] = None
    headquarters: Optional[str] = None


class CompanyCreate(CompanyBase):
    pass


class CompanyResponse(CompanyBase):
    id: UUID
    normalized_name: str
    created_at: datetime
    updated_at: datetime
    identifiers: Optional[List[CompanyIdentifierResponse]] = None

    model_config = ConfigDict(from_attributes=True)

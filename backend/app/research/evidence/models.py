from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4
from pydantic import BaseModel, Field, field_validator
from app.research.models import NormalizedEvidence
from app.schemas.evidence import SourceType, VerificationStatus


class FusedClaimStatus(str, Enum):
    """Categorical status outcome of evidence fusion for a claim."""
    SUPPORTED = "supported"
    CONFLICTED = "conflicted"
    INSUFFICIENT = "insufficient"
    UNVERIFIED = "unverified"


class EvidenceGroup(BaseModel):
    """Group of normalized evidence items relating to a single logical claim."""
    group_id: str = Field(default_factory=lambda: str(uuid4()))
    canonical_claim: str = Field(..., min_length=1)
    evidence: List[NormalizedEvidence] = Field(default_factory=list)
    supporting_evidence: List[NormalizedEvidence] = Field(default_factory=list)
    contradicting_evidence: List[NormalizedEvidence] = Field(default_factory=list)


class FusedClaim(BaseModel):
    """Fused conclusion aggregating supporting and contradicting evidence for a claim."""
    claim_id: str = Field(default_factory=lambda: str(uuid4()))
    canonical_claim: str = Field(..., min_length=1)
    status: FusedClaimStatus = FusedClaimStatus.UNVERIFIED
    supporting_evidence: List[NormalizedEvidence] = Field(default_factory=list)
    contradicting_evidence: List[NormalizedEvidence] = Field(default_factory=list)
    source_count: int = Field(default=0, ge=0)
    independent_source_count: int = Field(default=0, ge=0)
    agreement_score: float = Field(default=0.0, ge=0.0, le=1.0)
    contradiction_score: float = Field(default=0.0, ge=0.0, le=1.0)
    freshness_score: float = Field(default=0.0, ge=0.0, le=1.0)
    source_quality_score: float = Field(default=0.0, ge=0.0, le=1.0)
    evidence_strength: float = Field(default=0.0, ge=0.0, le=1.0)
    fused_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    explanation: Optional[str] = None

    @field_validator("status", mode="before")
    @classmethod
    def normalize_status(cls, v: Any) -> Any:
        if isinstance(v, str):
            v_str = v.lower()
            for item in FusedClaimStatus:
                if item.value == v_str or item.name.lower() == v_str:
                    return item
        return v


class FusionResult(BaseModel):
    """Aggregate result container holding all fused claims from a research run."""
    fused_claims: List[FusedClaim] = Field(default_factory=list)
    total_input_evidence: int = Field(default=0, ge=0)
    total_unique_evidence: int = Field(default=0, ge=0)
    total_claim_groups: int = Field(default=0, ge=0)
    conflicted_claims: int = Field(default=0, ge=0)
    warnings: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

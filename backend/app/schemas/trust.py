from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field



class TrustVerificationStatus(str, Enum):
    VERIFIED = "verified"
    PARTIALLY_VERIFIED = "partially_verified"
    UNABLE_TO_VERIFY = "unable_to_verify"
    CONFLICTING = "conflicting"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    UNKNOWN = "unknown"



class ConflictLevel(str, Enum):
    NO_CONFLICT = "no_conflict"
    MINOR_CONFLICT = "minor_conflict"
    MAJOR_CONFLICT = "major_conflict"


class DimensionScore(BaseModel):
    name: str = Field(..., description="Name of the evaluation dimension")
    score: float = Field(..., ge=0.0, le=100.0, description="Dimension score out of 100")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in dimension score")
    weight: float = Field(..., ge=0.0, le=1.0, description="Dimension weight in overall model")
    weighted_score: float = Field(..., ge=0.0, le=100.0, description="Score multiplied by weight")
    verification_status: TrustVerificationStatus = Field(
        default=TrustVerificationStatus.UNABLE_TO_VERIFY,
        description="Verification state for this dimension",
    )
    evidence_count: int = Field(default=0, description="Number of supporting evidence items used")
    evidence_ids: List[str] = Field(default_factory=list, description="IDs of supporting evidence items")
    details: Dict[str, Any] = Field(default_factory=dict, description="Detailed breakdown of dimension evaluation")


class RiskAdjustment(BaseModel):
    """
    Evaluates corporate risk signals and recruitment scam risk.
    Note: Recruitment risk uses deterministic rules (ML classifier not yet active).
    A risk dimension score of 100 indicates no configured penalties were triggered by deterministic rules.
    """
    company_legitimacy_penalty: float = Field(
        default=0.0, ge=0.0, le=50.0, description="Direct penalty to company legitimacy score"
    )
    recruitment_scam_risk: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Independent recruitment/job scam risk score (deterministic rule-based assessment; ML classifier not yet active)"
    )
    recruitment_risk_level: str = Field(
        default="low", description="Recruitment risk level (low, medium, high, critical)"
    )
    risk_factors: List[str] = Field(default_factory=list, description="List of identified risk flags")
    evidence_ids: List[str] = Field(default_factory=list, description="Evidence IDs triggering risk penalties")
    explanation: str = Field(
        default="No elevated corporate risk signals detected. Deterministic rule-based assessment; ML classifier not yet active. Risk score 100 indicates no configured penalties triggered.",
        description="Risk evaluation summary"
    )


class ConflictSummary(BaseModel):
    conflict_level: ConflictLevel = Field(
        default=ConflictLevel.NO_CONFLICT, description="Overall conflict severity level"
    )
    conflict_count: int = Field(default=0, description="Total number of conflicting claim pairs detected")
    confidence_penalty: float = Field(
        default=0.0, ge=0.0, le=0.5, description="Reduction in overall confidence due to conflicts"
    )
    conflict_details: List[Dict[str, Any]] = Field(
        default_factory=list, description="Structured description of detected conflicts"
    )


class TrustIndexResult(BaseModel):
    """
    Vishleshan AI v2 Trust Index result object.
    Score Limitations & Disclaimers:
    - Model weights are research hypotheses, not verified market truths.
    - Score is deterministic and reproducible.
    - Score is NOT a legal guarantee or audit certificate.
    - Missing data yields UNABLE_TO_VERIFY rather than zero or penalty.
    """
    trust_index: float = Field(..., ge=0.0, le=100.0, description="Overall deterministic Trust Index (0-100)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Overall confidence in Trust Index (0.0-1.0)")
    verification_status: TrustVerificationStatus = Field(
        ..., description="Overall organizational verification status"
    )
    risk_level: str = Field(..., description="Overall corporate risk level (low, medium, high, critical)")
    model_version: str = Field(default="v1", description="Trust model algorithm version identifier")
    calculated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="Timestamp of trust index computation",
    )
    computed_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO timestamp of score calculation",
    )
    updated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO timestamp of last score update",
    )
    dimension_scores: Dict[str, DimensionScore] = Field(
        ..., description="Breakdown across all 5 evaluation dimensions"
    )
    risk_adjustment: RiskAdjustment = Field(..., description="Risk adjustment penalty and recruitment scam metrics")
    conflict_summary: ConflictSummary = Field(..., description="Conflict evaluation summary")
    explanation: str = Field(..., description="Human-readable explanation grounded in evidence")
    evidence_references: List[Dict[str, Any]] = Field(
        default_factory=list, description="Traceable evidence references supporting score calculation"
    )

    @property
    def score(self) -> float:
        """Backward-compatibility accessor for legacy code expecting .score."""
        return self.trust_index


class TrustScoreResponse(BaseModel):
    id: Optional[UUID] = None
    company_id: Optional[UUID] = None
    research_run_id: Optional[UUID] = None
    score: Optional[float] = None
    trust_index: Optional[float] = None
    confidence: Optional[float] = None
    risk_level: Optional[str] = "low"
    verification_status: Optional[str] = "unable_to_verify"
    evidence_coverage: Optional[float] = None
    algorithm_version: str = "v1"
    explanation: Optional[str] = None
    created_at: Optional[datetime] = None
    computed_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    dimension_scores: Optional[Dict[str, Any]] = None
    risk_adjustment: Optional[Dict[str, Any]] = None
    conflict_summary: Optional[Dict[str, Any]] = None
    evidence_references: Optional[List[Dict[str, Any]]] = None

    model_config = ConfigDict(from_attributes=True)


TrustScoreResponse.model_rebuild()



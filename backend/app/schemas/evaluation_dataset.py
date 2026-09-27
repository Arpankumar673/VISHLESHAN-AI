from datetime import datetime, timezone
from enum import Enum
import re
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator


class EvaluationSourceType(str, Enum):
    FIRST_PARTY = "first_party"
    GOVERNMENT_REGULATORY = "government_regulatory"
    AUTHORITATIVE = "authoritative"
    REPUTABLE_SECONDARY = "reputable_secondary"
    OTHER = "other"


class EvaluationVerificationLabel(str, Enum):
    VERIFIED = "VERIFIED"
    PARTIALLY_VERIFIED = "PARTIALLY_VERIFIED"
    UNABLE_TO_VERIFY = "UNABLE_TO_VERIFY"
    CONFLICTING = "CONFLICTING"


class EvaluationNLILabel(str, Enum):
    ENTAILMENT = "ENTAILMENT"
    CONTRADICTION = "CONTRADICTION"
    NEUTRAL = "NEUTRAL"


class EvaluationDatasetMetadata(BaseModel):
    """
    Metadata specification for VISHLESHAN-EVAL-v1.
    """
    dataset_id: str = Field(default="VISHLESHAN-EVAL-v1", description="Unique dataset identifier")
    version: str = Field(default="v1.0.0", description="Semantic dataset version")
    creation_timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO timestamp of dataset creation",
    )
    description: str = Field(
        default="Vishleshan AI v2 Phase 6A Ground-Truth Evaluation Foundation Dataset Framework",
        description="Dataset description",
    )
    schema_version: str = Field(default="v1", description="Schema version identifier")
    provenance_policy: str = Field(
        default="Ground-truth claims must be traceable to explicit first-party, government, or authoritative source URLs.",
        description="Provenance enforcement policy description",
    )
    annotation_policy: str = Field(
        default="Annotated according to backend/data/evaluation/ANNOTATION_GUIDELINES.md. LLM predictions cannot serve as sole ground truth.",
        description="Annotation guidelines reference",
    )
    dataset_hash: str = Field(default="", description="Deterministic SHA-256 hash of dataset content")


class EvaluationCompanyRecord(BaseModel):
    """
    Evaluation target company record.
    """
    evaluation_company_id: str = Field(..., description="Unique UUID string for evaluation company")
    company_name: str = Field(..., min_length=1, description="Canonical target company name")
    official_domain: Optional[str] = Field(default=None, description="Official corporate web domain")
    source_references: List[Dict[str, Any]] = Field(default_factory=list, description="Associated source URLs/titles")
    evaluation_categories: List[str] = Field(default_factory=list, description="Associated evaluation categories")
    annotation_metadata: Dict[str, Any] = Field(default_factory=dict, description="Annotation metadata and dates")

    @field_validator("evaluation_company_id")
    @classmethod
    def validate_uuid_str(cls, v: str) -> str:
        try:
            UUID(v)
            return v
        except ValueError:
            raise ValueError(f"evaluation_company_id must be a valid UUID string. Got: '{v}'")


class GroundTruthClaim(BaseModel):
    """
    Structured ground-truth claim record for identity, evidence, and regulatory evaluation subsets.
    """
    claim_id: str = Field(..., description="Unique UUID string for claim record")
    evaluation_company_id: str = Field(..., description="Referenced evaluation_company_id")
    claim_text: str = Field(..., min_length=1, description="Statement or claim text")
    claim_type: str = Field(..., description="Category (e.g., identity, domain_ownership, registration, status)")
    expected_label: EvaluationVerificationLabel = Field(..., description="Ground-truth verification label")
    source_type: EvaluationSourceType = Field(..., description="Evaluation source category")
    source_url: Optional[str] = Field(default="", description="Source URL for provenance traceability")
    source_title: Optional[str] = Field(default="", description="Source document title")
    evidence_reference: str = Field(default="", description="Supporting evidence quote or record reference")
    annotation_method: str = Field(default="manual_curation", description="Annotation method (e.g. manual_curation)")
    annotator_id: str = Field(default="ANNOTATOR_001", description="Anonymized annotator identifier")
    annotation_timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO timestamp of annotation",
    )
    is_synthetic: bool = Field(default=False, description="Flag indicating whether record is synthetic/unit-test only")
    notes: Optional[str] = Field(default="", description="Contextual annotation notes")

    @field_validator("claim_id", "evaluation_company_id")
    @classmethod
    def validate_uuid_fields(cls, v: str) -> str:
        try:
            UUID(v)
            return v
        except ValueError:
            raise ValueError(f"ID field must be a valid UUID string. Got: '{v}'")

    @field_validator("source_url")
    @classmethod
    def validate_source_url(cls, v: Optional[str]) -> Optional[str]:
        if v and len(v.strip()) > 0:
            if not (v.startswith("http://") or v.startswith("https://")):
                raise ValueError(f"source_url must be a valid http or https URL. Got: '{v}'")
        return v


class ConflictEvalPair(BaseModel):
    """
    Ground-truth NLI evidence pair for conflict evaluation.
    """
    pair_id: str = Field(..., description="Unique UUID string for pair record")
    evaluation_company_id: str = Field(..., description="Referenced evaluation_company_id")
    premise_claim_id: str = Field(..., description="UUID of premise claim record")
    hypothesis_claim_id: str = Field(..., description="UUID of hypothesis claim record")
    premise_text: str = Field(..., min_length=1, description="Premise evidence text")
    hypothesis_text: str = Field(..., min_length=1, description="Hypothesis claim text")
    expected_nli_label: EvaluationNLILabel = Field(..., description="Ground-truth NLI relationship (ENTAILMENT, CONTRADICTION, NEUTRAL)")
    source_urls: List[str] = Field(default_factory=list, description="Source URLs of premise and hypothesis")
    annotation_method: str = Field(default="manual_curation", description="Annotation methodology")
    annotator_id: str = Field(default="ANNOTATOR_001", description="Anonymized annotator ID")
    is_synthetic: bool = Field(default=False, description="Flag indicating whether pair is synthetic/unit-test only")
    notes: Optional[str] = Field(default="", description="Annotation notes")

    @field_validator("pair_id", "evaluation_company_id", "premise_claim_id", "hypothesis_claim_id")
    @classmethod
    def validate_uuid_strings(cls, v: str) -> str:
        try:
            UUID(v)
            return v
        except ValueError:
            raise ValueError(f"ID must be a valid UUID string. Got: '{v}'")


class TrustBehaviorScenario(BaseModel):
    """
    Trust Engine behavioral evaluation scenario testing deterministic scoring rules and status assignments.
    """
    scenario_id: str = Field(..., description="Unique UUID string for behavioral scenario")
    evaluation_company_id: Optional[str] = Field(default="", description="Optional referenced evaluation_company_id")
    scenario_name: str = Field(..., min_length=1, description="Brief scenario title")
    evidence_state: Dict[str, Any] = Field(..., description="Simulated evidence state input payload")
    expected_dimension_behavior: Dict[str, Any] = Field(..., description="Expected 5-dimension scoring behaviors")
    expected_verification_state: EvaluationVerificationLabel = Field(..., description="Expected overall verification status")
    expected_conflict_state: str = Field(..., description="Expected conflict severity level (NO_CONFLICT, MINOR_CONFLICT, MAJOR_CONFLICT)")
    expected_confidence_behavior: str = Field(..., description="Expected confidence bounds or penalty behavior")
    expected_score_behavior: Dict[str, Any] = Field(default_factory=dict, description="Expected deterministic score bounds")
    provenance_references: List[str] = Field(default_factory=list, description="Supporting evidence source references")
    annotation_method: str = Field(default="deterministic_rule_specification", description="Specification method")
    annotator_id: str = Field(default="ANNOTATOR_001", description="Anonymized specifier ID")
    is_synthetic: bool = Field(default=False, description="Flag indicating synthetic/unit-test scenario")
    notes: Optional[str] = Field(default="", description="Scenario rationale")

    @field_validator("scenario_id")
    @classmethod
    def validate_scenario_uuid(cls, v: str) -> str:
        try:
            UUID(v)
            return v
        except ValueError:
            raise ValueError(f"scenario_id must be a valid UUID string. Got: '{v}'")


class RecruitmentEvalReference(BaseModel):
    """
    Reference manifest for frozen Phase 5A recruitment scam dataset and model evaluation.
    """
    reference_id: str = Field(default="PHASE_5A_RECRUITMENT_EVAL_MANIFEST", description="Reference manifest ID")
    dataset_id: str = Field(default="EMSCAD_REAL_DATASET_V1", description="Referenced dataset ID")
    dataset_sha256: str = Field(
        default="54e7f339cf0627b0b2e88102ad0db63c1935aa0f317eeae41ae645ee6e379dd8",
        description="SHA-256 of backend/data/fake_job_postings.csv",
    )
    source_file: str = Field(default="backend/data/fake_job_postings.csv", description="Relative file path")
    total_samples: int = Field(default=17880, description="Total EMSCAD sample count")
    fraudulent_count: int = Field(default=866, description="Fraudulent sample count")
    legitimate_count: int = Field(default=17014, description="Legitimate sample count")
    model_artifact_path: str = Field(
        default="backend/app/services/recruitment_scam_v1.joblib",
        description="Frozen model artifact location",
    )
    evaluation_protocol: str = Field(
        default="Phase 5A leakage-corrected group-split evaluation on company_profile",
        description="Protocol description",
    )
    is_synthetic: bool = Field(default=False, description="Real benchmark reference flag")
    notes: str = Field(
        default="Phase 5A recruitment classifier is frozen. Do not retrain or modify model artifact.",
        description="Freezing notice",
    )


class RAGEvalQuery(BaseModel):
    """
    Ground-truth query record for RAG evaluation.
    """
    question_id: str = Field(..., description="Unique UUID string for question record")
    evaluation_company_id: str = Field(..., description="Referenced evaluation_company_id")
    question: str = Field(..., min_length=1, description="User research question text")
    expected_answer: str = Field(..., min_length=1, description="Ground-truth expected answer or factual points")
    required_evidence_ids: List[str] = Field(default_factory=list, description="IDs of required evidence claims")
    acceptable_source_types: List[EvaluationSourceType] = Field(default_factory=list, description="Acceptable source tiers")
    annotation_method: str = Field(default="manual_curation", description="Annotation methodology")
    annotator_id: str = Field(default="ANNOTATOR_001", description="Anonymized annotator ID")
    is_synthetic: bool = Field(default=False, description="Synthetic query flag")
    notes: Optional[str] = Field(default="", description="Annotation notes")

    @field_validator("question_id", "evaluation_company_id")
    @classmethod
    def validate_rag_uuids(cls, v: str) -> str:
        try:
            UUID(v)
            return v
        except ValueError:
            raise ValueError(f"ID must be a valid UUID string. Got: '{v}'")


class EvaluationDataset(BaseModel):
    """
    Root container model holding metadata and records across all 6 evaluation subsets.
    """
    metadata: EvaluationDatasetMetadata
    companies: List[EvaluationCompanyRecord] = Field(default_factory=list)
    identity_eval: List[GroundTruthClaim] = Field(default_factory=list)
    evidence_eval: List[GroundTruthClaim] = Field(default_factory=list)
    conflict_eval: List[ConflictEvalPair] = Field(default_factory=list)
    trust_eval: List[TrustBehaviorScenario] = Field(default_factory=list)
    recruitment_eval: Optional[RecruitmentEvalReference] = Field(default_factory=RecruitmentEvalReference)
    rag_eval: List[RAGEvalQuery] = Field(default_factory=list)


class EvaluationDatasetStatistics(BaseModel):
    """
    Summary statistics breakdown for loaded evaluation dataset.
    """
    dataset_id: str
    version: str
    dataset_hash: str
    total_real_records: int
    total_synthetic_records: int
    company_count: int
    identity_eval_count: int
    evidence_eval_count: int
    conflict_eval_count: int
    trust_eval_count: int
    recruitment_sample_count: int
    rag_eval_count: int
    per_subset_real_counts: Dict[str, int]
    per_subset_synthetic_counts: Dict[str, int]

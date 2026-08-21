from app.research.evidence.conflict import (
    detect_conflicts,
    extract_employee_count,
    extract_founding_year,
    extract_official_domain_value,
)
from app.research.evidence.grouping import group_evidence, normalize_claim_text
from app.research.evidence.independence import (
    SourceIndependenceResult,
    assess_source_independence,
    normalize_url_for_independence,
)
from app.research.evidence.models import (
    EvidenceGroup,
    FusedClaim,
    FusedClaimStatus,
    FusionResult,
)
from app.research.evidence.scoring import (
    calculate_agreement_score,
    calculate_contradiction_score,
    calculate_evidence_strength,
    calculate_freshness_score,
    calculate_fused_confidence,
    calculate_independence_score,
    calculate_source_quality,
    calculate_verification_score,
    classify_claim_freshness_half_life,
    determine_fused_status,
    generate_explanation,
    score_evidence_group,
    score_fusion_result,
)

__all__ = [
    "EvidenceGroup",
    "FusedClaim",
    "FusedClaimStatus",
    "FusionResult",
    "normalize_claim_text",
    "group_evidence",
    "SourceIndependenceResult",
    "assess_source_independence",
    "normalize_url_for_independence",
    "detect_conflicts",
    "extract_founding_year",
    "extract_official_domain_value",
    "extract_employee_count",
    "classify_claim_freshness_half_life",
    "calculate_source_quality",
    "calculate_verification_score",
    "calculate_independence_score",
    "calculate_freshness_score",
    "calculate_agreement_score",
    "calculate_contradiction_score",
    "calculate_evidence_strength",
    "calculate_fused_confidence",
    "determine_fused_status",
    "generate_explanation",
    "score_evidence_group",
    "score_fusion_result",
]

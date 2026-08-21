from datetime import datetime, timezone
from math import exp, log
from typing import List, Optional, Tuple
from app.research.evidence.conflict import detect_conflicts
from app.research.evidence.independence import assess_source_independence
from app.research.evidence.models import (
    EvidenceGroup,
    FusedClaim,
    FusedClaimStatus,
    FusionResult,
)
from app.research.models import NormalizedEvidence
from app.schemas.evidence import VerificationStatus


VERIFICATION_WEIGHTS = {
    VerificationStatus.VERIFIED: 1.0,
    VerificationStatus.UNVERIFIED: 0.5,
    VerificationStatus.UNABLE_TO_VERIFY: 0.3,
    VerificationStatus.CONFLICTING: 0.2,
}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def classify_claim_freshness_half_life(claim: str) -> float:
    """Returns freshness half-life in days based on deterministic claim keyword categorization.
    
    Category Policies:
    - Hiring / Jobs / News / Announcements (rapid change): 90 days
    - Executive / Leadership / Domain / HQ (moderate stability): 180 days
    - Founding year / History (permanent facts): 3650 days (~10 years)
    - Default / Unclassified claims: 365 days (~1 year)
    """
    c = claim.lower()
    if any(k in c for k in ["hiring", "job", "career", "news", "announcement", "press"]):
        return 90.0
    elif any(k in c for k in ["ceo", "executive", "founder", "headquarters", "hq", "president", "domain", "website"]):
        return 180.0
    elif any(k in c for k in ["founded", "established", "incorporated", "started", "inception", "history"]):
        return 3650.0
    return 365.0


def calculate_source_quality(evidence: List[NormalizedEvidence]) -> float:
    """Calculates cluster-averaged source quality based on NormalizedEvidence.reliability_score.
    
    Uses independent source clusters so duplicate/dependent sources do not artificially inflate quality.
    """
    if not evidence:
        return 0.0

    indep_res = assess_source_independence(evidence)
    clusters = indep_res.source_clusters

    if not clusters:
        return 0.0

    cluster_max_qualities = []
    for cluster_urls in clusters:
        cluster_items = [e for e in evidence if e.source_url in cluster_urls]
        if cluster_items:
            max_rel = max(e.reliability_score for e in cluster_items)
            cluster_max_qualities.append(max_rel)

    if not cluster_max_qualities:
        return 0.0

    avg_quality = sum(cluster_max_qualities) / len(cluster_max_qualities)
    return max(0.0, min(1.0, float(avg_quality)))


def calculate_verification_score(evidence: List[NormalizedEvidence]) -> float:
    """Calculates cluster-averaged verification score using VerificationStatus weights."""
    if not evidence:
        return 0.0

    indep_res = assess_source_independence(evidence)
    clusters = indep_res.source_clusters

    if not clusters:
        return 0.0

    cluster_v_scores = []
    for cluster_urls in clusters:
        cluster_items = [e for e in evidence if e.source_url in cluster_urls]
        if cluster_items:
            max_v = max(VERIFICATION_WEIGHTS.get(e.verification_status, 0.5) for e in cluster_items)
            cluster_v_scores.append(max_v)

    if not cluster_v_scores:
        return 0.0

    avg_v = sum(cluster_v_scores) / len(cluster_v_scores)
    return max(0.0, min(1.0, float(avg_v)))


def calculate_independence_score(evidence: List[NormalizedEvidence]) -> float:
    """Calculates source independence score based on independent source cluster count."""
    if not evidence:
        return 0.0

    indep_res = assess_source_independence(evidence)
    k = indep_res.independent_sources

    if k <= 0:
        return 0.0
    elif k == 1:
        return 0.50
    else:
        # 2 clusters -> 0.75, 3+ clusters -> 1.00
        score = 0.50 + 0.25 * (k - 1)
        return max(0.0, min(1.0, float(score)))


def calculate_freshness_score(evidence: List[NormalizedEvidence], claim: str, now: Optional[datetime] = None) -> float:
    """Calculates freshness score using category-aware half-life exponential decay."""
    if not evidence:
        return 0.0

    ref_time = now or utc_now()
    half_life = classify_claim_freshness_half_life(claim)
    decay_constant = log(2) / half_life

    freshness_values = []
    for item in evidence:
        ts = item.published_at or item.observed_at
        if not ts:
            age_days = 365.0
        else:
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            if ref_time.tzinfo is None:
                ref_time = ref_time.replace(tzinfo=timezone.utc)

            delta = (ref_time - ts).total_seconds() / 86400.0
            age_days = max(0.0, delta)

        f_val = exp(-decay_constant * age_days)
        freshness_values.append(f_val)

    if not freshness_values:
        return 0.0

    avg_freshness = sum(freshness_values) / len(freshness_values)
    return max(0.0, min(1.0, float(avg_freshness)))


def calculate_agreement_score(supporting: List[NormalizedEvidence], contradicting: List[NormalizedEvidence]) -> float:
    """Calculates agreement score measuring independent supporting cluster ratio."""
    k_supp = assess_source_independence(supporting).independent_sources if supporting else 0
    k_contra = assess_source_independence(contradicting).independent_sources if contradicting else 0
    k_total = k_supp + k_contra

    if k_total == 0:
        return 0.0

    agreement = k_supp / k_total
    return max(0.0, min(1.0, float(agreement)))


def calculate_contradiction_score(supporting: List[NormalizedEvidence], contradicting: List[NormalizedEvidence]) -> float:
    """Calculates contradiction score measuring independent contradicting cluster ratio."""
    k_supp = assess_source_independence(supporting).independent_sources if supporting else 0
    k_contra = assess_source_independence(contradicting).independent_sources if contradicting else 0
    k_total = k_supp + k_contra

    if k_total == 0:
        return 0.0

    contradiction = k_contra / k_total
    return max(0.0, min(1.0, float(contradiction)))


def calculate_evidence_strength(
    source_quality: float,
    verification: float,
    independence: float,
    freshness: float,
    agreement: float,
    contradiction: float,
    has_supporting: bool,
) -> float:
    """Calculates composite evidence strength score bounded between 0.0 and 1.0.
    
    Formula:
    Base Strength = 0.30 * Quality + 0.25 * Verification + 0.25 * Independence + 0.20 * Freshness
    Evidence Strength = Base Strength * Agreement
    """
    if not has_supporting:
        return 0.0

    base_strength = (
        0.30 * source_quality +
        0.25 * verification +
        0.25 * independence +
        0.20 * freshness
    )

    strength = base_strength * agreement
    return max(0.0, min(1.0, float(strength)))


def calculate_fused_confidence(evidence_strength: float, contradiction_score: float, has_supporting: bool) -> float:
    """Calculates final fused confidence score bounded between 0.0 and 1.0.
    
    Formula:
    Fused Confidence = Evidence Strength * (1.0 - 0.5 * Contradiction Score)
    """
    if not has_supporting:
        return 0.0

    penalty = max(0.0, 1.0 - 0.5 * contradiction_score)
    confidence = evidence_strength * penalty
    return max(0.0, min(1.0, float(confidence)))


def determine_fused_status(
    k_supp: int,
    k_contra: int,
    fused_confidence: float,
    source_quality: float = 1.0,
    has_unverified_only: bool = False,
) -> FusedClaimStatus:
    """Determines categorical FusedClaimStatus based on deterministic rules:
    - UNVERIFIED: k_supp == 0
    - CONFLICTED: k_supp >= 1 AND k_contra >= 1
    - INSUFFICIENT: k_supp >= 1, k_contra == 0, and (unverified-only with confidence < 0.70 or source_quality < 0.60 or confidence < 0.50)
    - SUPPORTED: k_supp >= 1, k_contra == 0, fused_confidence >= 0.50, and source_quality >= 0.40
    """
    if k_supp == 0:
        return FusedClaimStatus.UNVERIFIED
    elif k_contra >= 1:
        return FusedClaimStatus.CONFLICTED
    elif has_unverified_only and (fused_confidence < 0.70 or source_quality < 0.60):
        return FusedClaimStatus.INSUFFICIENT
    elif fused_confidence >= 0.50 and source_quality >= 0.40:
        return FusedClaimStatus.SUPPORTED
    else:
        return FusedClaimStatus.INSUFFICIENT


def generate_explanation(
    status: FusedClaimStatus,
    fused_confidence: float,
    k_supp: int,
    k_contra: int,
    source_quality: float,
    verification: float,
    freshness: float,
) -> str:
    """Generates a template-driven, deterministic explanation string without LLMs."""
    if status == FusedClaimStatus.UNVERIFIED:
        return "Confidence 0.00 (Unverified): No supporting evidence items available for this claim."
    elif status == FusedClaimStatus.CONFLICTED:
        return f"Confidence {fused_confidence:.2f} (Conflicted): Material contradiction detected between {k_supp} independent supporting source(s) and {k_contra} independent contradicting source(s)."
    elif status == FusedClaimStatus.INSUFFICIENT:
        return f"Confidence {fused_confidence:.2f} (Insufficient): Evidence from {k_supp} independent source(s) is insufficient to establish high confidence (quality: {source_quality:.2f}, verification: {verification:.2f})."
    else:
        return f"Confidence {fused_confidence:.2f} (Supported): Based on {k_supp} independent supporting source(s) with high source quality ({source_quality:.2f}), verified status ({verification:.2f}), freshness ({freshness:.2f}), and zero unresolved contradictions."


def score_evidence_group(group: EvidenceGroup, now: Optional[datetime] = None) -> FusedClaim:
    """Transforms an EvidenceGroup into a fully scored and evaluated FusedClaim."""
    # 1. Perform deterministic conflict detection & partitioning if not pre-partitioned
    if group.supporting_evidence or group.contradicting_evidence:
        analyzed_group = group
    else:
        analyzed_group = detect_conflicts(group)

    supp_ev = analyzed_group.supporting_evidence
    contra_ev = analyzed_group.contradicting_evidence
    all_ev = analyzed_group.evidence

    # 2. Assess source independence
    supp_indep = assess_source_independence(supp_ev)
    contra_indep = assess_source_independence(contra_ev)
    all_indep = assess_source_independence(all_ev)

    k_supp = supp_indep.independent_sources
    k_contra = contra_indep.independent_sources
    has_supp = len(supp_ev) > 0

    # Check if all supporting evidence items are unverified/unable to verify
    has_unverified_only = has_supp and all(
        e.verification_status in (VerificationStatus.UNVERIFIED, VerificationStatus.UNABLE_TO_VERIFY)
        for e in supp_ev
    )

    # 3. Calculate component metrics
    source_quality = calculate_source_quality(supp_ev if has_supp else all_ev)
    verification = calculate_verification_score(supp_ev if has_supp else all_ev)
    independence = calculate_independence_score(supp_ev if has_supp else all_ev)
    freshness = calculate_freshness_score(supp_ev if has_supp else all_ev, group.canonical_claim, now=now)
    agreement = calculate_agreement_score(supp_ev, contra_ev)
    contradiction = calculate_contradiction_score(supp_ev, contra_ev)

    # 4. Calculate composite strength and fused confidence
    evidence_strength = calculate_evidence_strength(
        source_quality=source_quality,
        verification=verification,
        independence=independence,
        freshness=freshness,
        agreement=agreement,
        contradiction=contradiction,
        has_supporting=has_supp,
    )

    fused_confidence = calculate_fused_confidence(
        evidence_strength=evidence_strength,
        contradiction_score=contradiction,
        has_supporting=has_supp,
    )

    # 5. Determine status & generate explanation
    status = determine_fused_status(
        k_supp=k_supp,
        k_contra=k_contra,
        fused_confidence=fused_confidence,
        source_quality=source_quality,
        has_unverified_only=has_unverified_only,
    )

    explanation = generate_explanation(
        status=status,
        fused_confidence=fused_confidence,
        k_supp=k_supp,
        k_contra=k_contra,
        source_quality=source_quality,
        verification=verification,
        freshness=freshness,
    )

    # 6. Construct FusedClaim
    return FusedClaim(
        claim_id=group.group_id,
        canonical_claim=group.canonical_claim,
        status=status,
        supporting_evidence=supp_ev,
        contradicting_evidence=contra_ev,
        source_count=len(all_ev),
        independent_source_count=all_indep.independent_sources,
        agreement_score=agreement,
        contradiction_score=contradiction,
        freshness_score=freshness,
        source_quality_score=source_quality,
        evidence_strength=evidence_strength,
        fused_confidence=fused_confidence,
        explanation=explanation,
    )


def score_fusion_result(groups: List[EvidenceGroup], now: Optional[datetime] = None) -> FusionResult:
    """Transforms a list of EvidenceGroup objects into an aggregate FusionResult."""
    fused_claims: List[FusedClaim] = []
    total_input_evidence = 0
    conflicted_claims = 0
    all_evidence_items: List[NormalizedEvidence] = []

    for group in groups:
        fc = score_evidence_group(group, now=now)
        fused_claims.append(fc)
        total_input_evidence += fc.source_count
        all_evidence_items.extend(group.evidence)
        if fc.status == FusedClaimStatus.CONFLICTED:
            conflicted_claims += 1

    unique_evidence_hashes = {e.content_hash for e in all_evidence_items if e.content_hash}
    total_unique = len(unique_evidence_hashes) if unique_evidence_hashes else total_input_evidence

    warnings = []
    if conflicted_claims > 0:
        warnings.append(f"Detected {conflicted_claims} conflicted claim(s) requiring verification.")

    return FusionResult(
        fused_claims=fused_claims,
        total_input_evidence=total_input_evidence,
        total_unique_evidence=total_unique,
        total_claim_groups=len(groups),
        conflicted_claims=conflicted_claims,
        warnings=warnings,
        metadata={"fused_at": (now or utc_now()).isoformat()},
    )

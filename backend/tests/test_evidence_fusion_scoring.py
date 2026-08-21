from datetime import datetime, timedelta, timezone
import pytest
from app.research.evidence.models import EvidenceGroup, FusedClaimStatus
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
    score_evidence_group,
    score_fusion_result,
)
from app.research.models import NormalizedEvidence
from app.schemas.evidence import SourceType, VerificationStatus

FIXED_TEST_NOW = datetime(2026, 8, 20, 12, 0, 0, tzinfo=timezone.utc)


def make_ev(
    claim: str = "Google LLC operates search",
    url: str = "https://about.google",
    reliability: float = 0.90,
    verification: VerificationStatus = VerificationStatus.VERIFIED,
    published_at: datetime = None,
    observed_at: datetime = None,
    hash_val: str = None,
) -> NormalizedEvidence:
    pub = published_at if published_at is not None else (FIXED_TEST_NOW - timedelta(days=10))
    obs = observed_at if observed_at is not None else FIXED_TEST_NOW
    h = hash_val or f"hash_{url}_{claim}"
    return NormalizedEvidence(
        claim=claim,
        evidence_text=f"Text for {claim}",
        source_url=url,
        source_title="Title",
        source_type=SourceType.OFFICIAL_COMPANY,
        published_at=pub,
        observed_at=obs,
        reliability_score=reliability,
        confidence_score=0.95,
        verification_status=verification,
        agent_name="company_research_v1",
        content_hash=h,
    )


# ------------------------------------------------------------
# 1. All Scores Remain Within 0..1
# ------------------------------------------------------------
def test_all_scores_within_bounds():
    ev = make_ev()
    group = EvidenceGroup(canonical_claim="Bounds test", evidence=[ev])
    fc = score_evidence_group(group, now=FIXED_TEST_NOW)

    scores = [
        fc.agreement_score,
        fc.contradiction_score,
        fc.freshness_score,
        fc.source_quality_score,
        fc.evidence_strength,
        fc.fused_confidence,
    ]
    for s in scores:
        assert 0.0 <= s <= 1.0


# ------------------------------------------------------------
# 2. High-Quality vs Low-Quality Evidence
# ------------------------------------------------------------
def test_high_quality_scores_higher():
    high_ev = make_ev(reliability=0.95)
    low_ev = make_ev(reliability=0.20)

    q_high = calculate_source_quality([high_ev])
    q_low = calculate_source_quality([low_ev])

    assert q_high > q_low
    assert q_high == 0.95
    assert q_low == 0.20


# ------------------------------------------------------------
# 3. Verified vs Unverified Evidence
# ------------------------------------------------------------
def test_verified_scores_higher():
    v_ev = make_ev(verification=VerificationStatus.VERIFIED)
    u_ev = make_ev(verification=VerificationStatus.UNVERIFIED)

    s_verified = calculate_verification_score([v_ev])
    s_unverified = calculate_verification_score([u_ev])

    assert s_verified > s_unverified
    assert s_verified == 1.0
    assert s_unverified == 0.5


# ------------------------------------------------------------
# 4. Independent Sources Increase Agreement Appropriately
# ------------------------------------------------------------
def test_independent_sources_increase_agreement():
    supp1 = make_ev(claim="Acme was founded in 2018", url="https://source1.com")
    supp2 = make_ev(claim="Acme was founded in 2018", url="https://source2.com")
    contra = make_ev(claim="Acme was founded in 2020", url="https://source3.com")

    group = EvidenceGroup(canonical_claim="Acme was founded in 2018", evidence=[supp1, supp2, contra])
    fc = score_evidence_group(group, now=FIXED_TEST_NOW)

    assert fc.agreement_score > fc.contradiction_score
    assert fc.agreement_score == pytest.approx(2.0 / 3.0)
    assert fc.contradiction_score == pytest.approx(1.0 / 3.0)


# ------------------------------------------------------------
# 5. Duplicate Sources Do Not Inflate Agreement
# ------------------------------------------------------------
def test_duplicate_sources_do_not_inflate_agreement():
    supp1 = make_ev(claim="Acme was founded in 2018", url="https://source1.com", hash_val="hash_A")
    supp2_copy = make_ev(claim="Acme was founded in 2018", url="https://source1.com/copy", hash_val="hash_A")
    contra = make_ev(claim="Acme was founded in 2020", url="https://source3.com", hash_val="hash_B")

    group = EvidenceGroup(canonical_claim="Acme was founded in 2018", evidence=[supp1, supp2_copy, contra])
    fc = score_evidence_group(group, now=FIXED_TEST_NOW)

    # 1 independent supporting cluster vs 1 independent contradicting cluster
    assert fc.agreement_score == 0.50
    assert fc.contradiction_score == 0.50


# ------------------------------------------------------------
# 6. Contradictory Evidence Reduces Confidence
# ------------------------------------------------------------
def test_contradictory_evidence_reduces_confidence():
    supp = make_ev(claim="CEO is Alice", url="https://source1.com")
    contra = make_ev(claim="CEO is Bob", url="https://source2.com")

    group_clean = EvidenceGroup(canonical_claim="CEO is Alice", evidence=[supp])
    fc_clean = score_evidence_group(group_clean, now=FIXED_TEST_NOW)

    group_conflicted = EvidenceGroup(canonical_claim="CEO is Alice", evidence=[supp, contra])
    fc_conflicted = score_evidence_group(group_conflicted, now=FIXED_TEST_NOW)

    assert fc_conflicted.fused_confidence < fc_clean.fused_confidence
    assert fc_conflicted.status == FusedClaimStatus.CONFLICTED


# ------------------------------------------------------------
# 7. Copied Contradictory Evidence Does Not Inflate Contradiction
# ------------------------------------------------------------
def test_copied_contradictory_evidence_does_not_inflate_contradiction():
    supp = make_ev(claim="CEO is Alice", url="https://source1.com", hash_val="h_supp")
    contra1 = make_ev(claim="CEO is Bob", url="https://source2.com", hash_val="h_contra")
    contra2_copy = make_ev(claim="CEO is Bob", url="https://source2.com/mirror", hash_val="h_contra")

    group = EvidenceGroup(canonical_claim="CEO is Alice", evidence=[supp, contra1, contra2_copy])
    fc = score_evidence_group(group, now=FIXED_TEST_NOW)

    # 1 supp cluster vs 1 contra cluster
    assert fc.contradiction_score == 0.50


# ------------------------------------------------------------
# 8. Fresh vs Old Evidence for Time-Sensitive Claims
# ------------------------------------------------------------
def test_freshness_for_time_sensitive_claims():
    now = FIXED_TEST_NOW
    fresh_ev = make_ev(claim="Hiring software engineers", published_at=now - timedelta(days=5))
    old_ev = make_ev(claim="Hiring software engineers", published_at=now - timedelta(days=200))

    f_fresh = calculate_freshness_score([fresh_ev], claim="Hiring software engineers", now=now)
    f_old = calculate_freshness_score([old_ev], claim="Hiring software engineers", now=now)

    assert f_fresh > f_old
    assert f_fresh > 0.90
    assert f_old < 0.30


# ------------------------------------------------------------
# 9. Old Evidence Remains Useful for Stable Claims (Founding Year)
# ------------------------------------------------------------
def test_freshness_for_stable_historical_claims():
    now = FIXED_TEST_NOW
    old_founding_ev = make_ev(claim="Founded in 1998", published_at=now - timedelta(days=1000))

    f_score = calculate_freshness_score([old_founding_ev], claim="Founded in 1998", now=now)

    # Founding year half life is 3650 days (~10 years); 1000 days should retain high freshness (> 0.80)
    assert f_score > 0.80


# ------------------------------------------------------------
# 10. Ambiguous Freshness Uses Conservative Default
# ------------------------------------------------------------
def test_ambiguous_freshness_uses_default():
    hl = classify_claim_freshness_half_life("Generic corporate claim text")
    assert hl == 365.0


# ------------------------------------------------------------
# 11 & 12. Determinism of Evidence Strength and Fused Confidence
# ------------------------------------------------------------
def test_scoring_determinism():
    ev1 = make_ev(url="https://s1.com")
    ev2 = make_ev(url="https://s2.com")
    group = EvidenceGroup(canonical_claim="Deterministic scoring test", evidence=[ev1, ev2])

    fc1 = score_evidence_group(group, now=FIXED_TEST_NOW)
    fc2 = score_evidence_group(group, now=FIXED_TEST_NOW)

    assert fc1.evidence_strength == fc2.evidence_strength
    assert fc1.fused_confidence == fc2.fused_confidence
    assert fc1.explanation == fc2.explanation


# ------------------------------------------------------------
# 13 & 14. Confidence Boundaries
# ------------------------------------------------------------
def test_confidence_boundary_clamping():
    assert calculate_fused_confidence(1.5, 0.0, True) <= 1.0
    assert calculate_fused_confidence(-0.5, 1.0, True) >= 0.0


# ------------------------------------------------------------
# 15. Explanation Generation Determinism
# ------------------------------------------------------------
def test_explanation_generation_determinism():
    ev = make_ev()
    group = EvidenceGroup(canonical_claim="Explanation test", evidence=[ev])
    fc = score_evidence_group(group, now=FIXED_TEST_NOW)

    assert "Confidence" in fc.explanation
    assert "supported" in fc.explanation.lower() or "independent" in fc.explanation.lower()


# ------------------------------------------------------------
# 16. Status Assignment Determinism
# ------------------------------------------------------------
def test_status_assignment_determinism():
    ev = make_ev(verification=VerificationStatus.VERIFIED, reliability=0.90)
    group = EvidenceGroup(canonical_claim="Status test", evidence=[ev])
    fc = score_evidence_group(group, now=FIXED_TEST_NOW)

    assert fc.status == FusedClaimStatus.SUPPORTED


# ------------------------------------------------------------
# 17. Provenance Unchanged
# ------------------------------------------------------------
def test_provenance_unchanged():
    ev = make_ev(url="https://provenance.test.com", hash_val="hash_prov_99")
    group = EvidenceGroup(canonical_claim="Provenance test", evidence=[ev])
    fc = score_evidence_group(group, now=FIXED_TEST_NOW)

    assert fc.supporting_evidence[0].content_hash == "hash_prov_99"
    assert fc.supporting_evidence[0].source_url == "https://provenance.test.com"


# ============================================================
# EDGE CASES
# ============================================================

# 1. Empty Evidence
def test_edge_case_empty_evidence():
    group = EvidenceGroup(canonical_claim="Empty evidence group", evidence=[])
    fc = score_evidence_group(group, now=FIXED_TEST_NOW)

    assert fc.status == FusedClaimStatus.UNVERIFIED
    assert fc.source_count == 0
    assert fc.fused_confidence == 0.0
    assert fc.evidence_strength == 0.0


# 2. One Source
def test_edge_case_one_source():
    ev = make_ev(url="https://single.com")
    group = EvidenceGroup(canonical_claim="Single source group", evidence=[ev])
    fc = score_evidence_group(group, now=FIXED_TEST_NOW)

    assert fc.source_count == 1
    assert fc.independent_source_count == 1
    assert 0.0 <= fc.fused_confidence <= 1.0


# 3. Many Duplicate Sources
def test_edge_case_many_duplicate_sources():
    duplicates = [make_ev(url=f"https://dup{i}.com", hash_val="same_hash_all") for i in range(10)]
    group = EvidenceGroup(canonical_claim="Duplicates group", evidence=duplicates)
    fc = score_evidence_group(group, now=FIXED_TEST_NOW)

    assert fc.source_count == 10
    assert fc.independent_source_count == 1
    assert fc.agreement_score == 1.0


# 4. Only Contradictory Evidence
def test_edge_case_only_contradictory_evidence():
    contra = make_ev(claim="Founded in 2020", url="https://contra.com")
    group = EvidenceGroup(
        canonical_claim="Founded in 2018",
        evidence=[contra],
        supporting_evidence=[],
        contradicting_evidence=[contra],
    )
    fc = score_evidence_group(group, now=FIXED_TEST_NOW)

    assert fc.fused_confidence == 0.0
    assert fc.status == FusedClaimStatus.UNVERIFIED


# 5. Equal Supporting and Contradictory Evidence
def test_edge_case_equal_supporting_contradictory():
    supp = make_ev(claim="CEO is Alice", url="https://supp.com")
    contra = make_ev(claim="CEO is Bob", url="https://contra.com")
    group = EvidenceGroup(canonical_claim="CEO is Alice", evidence=[supp, contra])
    fc = score_evidence_group(group, now=FIXED_TEST_NOW)

    assert fc.status == FusedClaimStatus.CONFLICTED
    assert fc.agreement_score == 0.50
    assert fc.contradiction_score == 0.50


# 6. All Unverified Evidence
def test_edge_case_all_unverified():
    ev = make_ev(verification=VerificationStatus.UNVERIFIED, reliability=0.30)
    group = EvidenceGroup(canonical_claim="Unverified group", evidence=[ev])
    fc = score_evidence_group(group, now=FIXED_TEST_NOW)

    assert fc.status == FusedClaimStatus.INSUFFICIENT


# 7. All Verified Evidence
def test_edge_case_all_verified():
    ev = make_ev(verification=VerificationStatus.VERIFIED, reliability=0.95)
    group = EvidenceGroup(canonical_claim="Verified group", evidence=[ev])
    fc = score_evidence_group(group, now=FIXED_TEST_NOW)

    assert fc.status == FusedClaimStatus.SUPPORTED


# 8. Missing published_at
def test_edge_case_missing_published_at():
    ev = make_ev(published_at=None)
    group = EvidenceGroup(canonical_claim="Missing published_at", evidence=[ev])
    fc = score_evidence_group(group, now=FIXED_TEST_NOW)

    assert 0.0 <= fc.freshness_score <= 1.0


# 9. Missing observed_at (None fallback)
def test_edge_case_missing_timestamps():
    ev = make_ev(published_at=None)
    ev.observed_at = None
    group = EvidenceGroup(canonical_claim="Missing timestamps", evidence=[ev])
    fc = score_evidence_group(group, now=FIXED_TEST_NOW)

    assert 0.0 <= fc.freshness_score <= 1.0


# 10. Very Old Evidence
def test_edge_case_very_old_evidence():
    now = FIXED_TEST_NOW
    very_old = make_ev(published_at=now - timedelta(days=5000))
    group = EvidenceGroup(canonical_claim="Recent news update", evidence=[very_old])
    fc = score_evidence_group(group, now=now)

    assert fc.freshness_score < 0.10


# 11. Future Timestamps
def test_edge_case_future_timestamps():
    now = FIXED_TEST_NOW
    future_ev = make_ev(published_at=now + timedelta(days=100))
    group = EvidenceGroup(canonical_claim="Future event", evidence=[future_ev])
    fc = score_evidence_group(group, now=now)

    assert fc.freshness_score == 1.0


# 12. Zero Reliability
def test_edge_case_zero_reliability():
    ev = make_ev(reliability=0.0)
    group = EvidenceGroup(canonical_claim="Zero reliability", evidence=[ev])
    fc = score_evidence_group(group, now=FIXED_TEST_NOW)

    assert fc.source_quality_score == 0.0


# 13. Reliability = 1.0
def test_edge_case_max_reliability():
    ev = make_ev(reliability=1.0)
    group = EvidenceGroup(canonical_claim="Max reliability", evidence=[ev])
    fc = score_evidence_group(group, now=FIXED_TEST_NOW)

    assert fc.source_quality_score == 1.0


# 14. FusionResult Aggregate Test
def test_fusion_result_scoring_aggregate():
    ev1 = make_ev(claim="Claim A", url="https://s1.com")
    ev2 = make_ev(claim="CEO is Alice", url="https://s2.com")
    ev3 = make_ev(claim="CEO is Bob", url="https://s3.com")

    g1 = EvidenceGroup(canonical_claim="Claim A", evidence=[ev1])
    g2 = EvidenceGroup(canonical_claim="CEO of company", evidence=[ev2, ev3])

    res = score_fusion_result([g1, g2], now=FIXED_TEST_NOW)

    assert len(res.fused_claims) == 2
    assert res.total_input_evidence == 3
    assert res.conflicted_claims == 1
    assert len(res.warnings) == 1

from datetime import datetime, timezone
from uuid import uuid4
import pytest
from pydantic import ValidationError
from app.research.evidence.models import (
    EvidenceGroup,
    FusedClaim,
    FusedClaimStatus,
    FusionResult,
)
from app.research.models import NormalizedEvidence
from app.research.normalizer import EvidenceNormalizer
from app.schemas.evidence import SourceType, VerificationStatus


def make_sample_evidence(
    claim: str = "Google LLC operates search services",
    source_url: str = "https://about.google",
    reliability_score: float = 0.90,
    confidence_score: float = 0.95,
) -> NormalizedEvidence:
    text = "Official corporate overview page."
    return NormalizedEvidence(
        claim=claim,
        evidence_text=text,
        source_url=source_url,
        source_title="About Google",
        source_type=SourceType.OFFICIAL_COMPANY,
        observed_at=datetime.now(timezone.utc),
        reliability_score=reliability_score,
        confidence_score=confidence_score,
        verification_status=VerificationStatus.VERIFIED,
        agent_name="company_research_v1",
        content_hash=EvidenceNormalizer.compute_hash(claim, source_url, text),
    )


# ------------------------------------------------------------
# 1. Valid EvidenceGroup
# ------------------------------------------------------------
def test_valid_evidence_group():
    ev = make_sample_evidence()
    group = EvidenceGroup(
        canonical_claim="Google LLC operates global search services",
        evidence=[ev],
        supporting_evidence=[ev],
        contradicting_evidence=[],
    )

    assert group.group_id is not None
    assert len(group.group_id) > 0
    assert group.canonical_claim == "Google LLC operates global search services"
    assert len(group.evidence) == 1
    assert len(group.supporting_evidence) == 1
    assert len(group.contradicting_evidence) == 0


# ------------------------------------------------------------
# 2. Valid FusedClaim
# ------------------------------------------------------------
def test_valid_fused_claim():
    supp_ev = make_sample_evidence()
    claim = FusedClaim(
        canonical_claim="Google LLC is headquartered in Mountain View, CA",
        status=FusedClaimStatus.SUPPORTED,
        supporting_evidence=[supp_ev],
        contradicting_evidence=[],
        source_count=1,
        independent_source_count=1,
        agreement_score=1.0,
        contradiction_score=0.0,
        freshness_score=0.9,
        source_quality_score=0.95,
        evidence_strength=0.92,
        fused_confidence=0.94,
        explanation="Single official source confirms location.",
    )

    assert claim.claim_id is not None
    assert claim.canonical_claim == "Google LLC is headquartered in Mountain View, CA"
    assert claim.status == FusedClaimStatus.SUPPORTED
    assert claim.source_count == 1
    assert claim.agreement_score == 1.0
    assert claim.fused_confidence == 0.94
    assert claim.explanation == "Single official source confirms location."


# ------------------------------------------------------------
# 3. All FusedClaim Status Values
# ------------------------------------------------------------
def test_all_fused_claim_status_values():
    expected_statuses = [
        FusedClaimStatus.SUPPORTED,
        FusedClaimStatus.CONFLICTED,
        FusedClaimStatus.INSUFFICIENT,
        FusedClaimStatus.UNVERIFIED,
    ]

    for status_val in expected_statuses:
        claim = FusedClaim(
            canonical_claim="Test claim status enum validation",
            status=status_val,
        )
        assert claim.status == status_val

    # Test case-insensitive string parsing
    assert FusedClaim(canonical_claim="C", status="SUPPORTED").status == FusedClaimStatus.SUPPORTED
    assert FusedClaim(canonical_claim="C", status="conflicted").status == FusedClaimStatus.CONFLICTED
    assert FusedClaim(canonical_claim="C", status="INSUFFICIENT").status == FusedClaimStatus.INSUFFICIENT
    assert FusedClaim(canonical_claim="C", status="unverified").status == FusedClaimStatus.UNVERIFIED


# ------------------------------------------------------------
# 4. Valid FusionResult
# ------------------------------------------------------------
def test_valid_fusion_result():
    claim1 = FusedClaim(
        canonical_claim="Google LLC is a tech company",
        status=FusedClaimStatus.SUPPORTED,
    )
    claim2 = FusedClaim(
        canonical_claim="Google LLC operates 500 offices in Ohio",
        status=FusedClaimStatus.CONFLICTED,
    )

    res = FusionResult(
        fused_claims=[claim1, claim2],
        total_input_evidence=10,
        total_unique_evidence=8,
        total_claim_groups=2,
        conflicted_claims=1,
        warnings=["Discrepancy detected in office location counts"],
        metadata={"run_type": "unit_test"},
    )

    assert len(res.fused_claims) == 2
    assert res.total_input_evidence == 10
    assert res.total_unique_evidence == 8
    assert res.total_claim_groups == 2
    assert res.conflicted_claims == 1
    assert len(res.warnings) == 1
    assert res.metadata["run_type"] == "unit_test"


# ------------------------------------------------------------
# 5. NormalizedEvidence Compatibility
# ------------------------------------------------------------
def test_normalized_evidence_compatibility():
    ev = make_sample_evidence(
        claim="Alphabet Inc is parent of Google LLC",
        source_url="https://abc.xyz",
    )

    # Verify directly initializing EvidenceGroup and FusedClaim with NormalizedEvidence instances
    eg = EvidenceGroup(
        canonical_claim="Alphabet Inc is parent of Google LLC",
        evidence=[ev],
        supporting_evidence=[ev],
    )
    fc = FusedClaim(
        canonical_claim="Alphabet Inc is parent of Google LLC",
        status=FusedClaimStatus.SUPPORTED,
        supporting_evidence=[ev],
    )

    assert isinstance(eg.evidence[0], NormalizedEvidence)
    assert isinstance(fc.supporting_evidence[0], NormalizedEvidence)
    assert fc.supporting_evidence[0].source_url == "https://abc.xyz"
    assert fc.supporting_evidence[0].reliability_score == 0.90


# ------------------------------------------------------------
# 6. Serialization (model_dump & model_dump_json)
# ------------------------------------------------------------
def test_serialization():
    ev = make_sample_evidence()
    fc = FusedClaim(
        canonical_claim="Serialized claim test",
        status=FusedClaimStatus.SUPPORTED,
        supporting_evidence=[ev],
        agreement_score=0.88,
    )
    res = FusionResult(
        fused_claims=[fc],
        total_input_evidence=1,
        total_unique_evidence=1,
        total_claim_groups=1,
    )

    # 1. Dict serialization
    dump_dict = res.model_dump()
    assert dump_dict["total_input_evidence"] == 1
    assert dump_dict["fused_claims"][0]["status"] == "supported"
    assert dump_dict["fused_claims"][0]["agreement_score"] == 0.88

    # 2. JSON serialization
    json_str = res.model_dump_json()
    assert '"total_input_evidence":1' in json_str or '"total_input_evidence": 1' in json_str
    assert '"status":"supported"' in json_str or '"status": "supported"' in json_str


# ------------------------------------------------------------
# 7. Deserialization (model_validate & model_validate_json)
# ------------------------------------------------------------
def test_deserialization():
    ev = make_sample_evidence()
    fc = FusedClaim(
        canonical_claim="Deserialized claim test",
        status=FusedClaimStatus.CONFLICTED,
        supporting_evidence=[ev],
        contradiction_score=0.75,
    )
    res = FusionResult(
        fused_claims=[fc],
        total_input_evidence=5,
        total_unique_evidence=4,
        total_claim_groups=1,
        conflicted_claims=1,
    )

    # 1. From dict
    res_dict = res.model_dump()
    restored_dict = FusionResult.model_validate(res_dict)
    assert restored_dict.total_input_evidence == 5
    assert restored_dict.fused_claims[0].status == FusedClaimStatus.CONFLICTED
    assert restored_dict.fused_claims[0].contradiction_score == 0.75

    # 2. From JSON
    res_json = res.model_dump_json()
    restored_json = FusionResult.model_validate_json(res_json)
    assert restored_json.total_unique_evidence == 4
    assert restored_json.fused_claims[0].canonical_claim == "Deserialized claim test"
    assert isinstance(restored_json.fused_claims[0].supporting_evidence[0], NormalizedEvidence)


# ------------------------------------------------------------
# 8. Invalid Values Rejected
# ------------------------------------------------------------
def test_invalid_values_rejected():
    # 1. Out of bounds agreement_score (> 1.0)
    with pytest.raises(ValidationError):
        FusedClaim(
            canonical_claim="Invalid score",
            agreement_score=1.5,
        )

    # 2. Negative score (< 0.0)
    with pytest.raises(ValidationError):
        FusedClaim(
            canonical_claim="Negative score",
            fused_confidence=-0.1,
        )

    # 3. Invalid status value
    with pytest.raises(ValidationError):
        FusedClaim(
            canonical_claim="Invalid status enum",
            status="INVALID_STATUS_NAME",
        )

    # 4. Empty canonical claim string
    with pytest.raises(ValidationError):
        FusedClaim(
            canonical_claim="",
        )


# ------------------------------------------------------------
# 9. Provenance Preserved
# ------------------------------------------------------------
def test_provenance_preserved():
    ev = make_sample_evidence(
        claim="Original factual claim",
        source_url="https://provenance.example.com",
    )
    original_hash = ev.content_hash

    fc = FusedClaim(
        canonical_claim="Aggregated factual claim",
        status=FusedClaimStatus.SUPPORTED,
        supporting_evidence=[ev],
    )

    # Provenance fields MUST remain intact inside FusedClaim
    retained_ev = fc.supporting_evidence[0]
    assert retained_ev.content_hash == original_hash
    assert retained_ev.source_url == "https://provenance.example.com"
    assert retained_ev.agent_name == "company_research_v1"
    assert retained_ev.reliability_score == 0.90
    assert retained_ev.confidence_score == 0.95


# ------------------------------------------------------------
# 10. Supporting / Contradicting Evidence Preserved
# ------------------------------------------------------------
def test_supporting_contradicting_evidence_preserved():
    supp_ev = make_sample_evidence(
        claim="Company revenue is $10B",
        source_url="https://official.com/sec",
    )
    contra_ev = make_sample_evidence(
        claim="Company revenue is $5B",
        source_url="https://unverified-blog.com/post",
        reliability_score=0.30,
        confidence_score=0.40,
    )

    fc = FusedClaim(
        canonical_claim="Company annual revenue",
        status=FusedClaimStatus.CONFLICTED,
        supporting_evidence=[supp_ev],
        contradicting_evidence=[contra_ev],
        source_count=2,
        independent_source_count=2,
    )

    assert len(fc.supporting_evidence) == 1
    assert len(fc.contradicting_evidence) == 1
    assert fc.supporting_evidence[0].source_url == "https://official.com/sec"
    assert fc.contradicting_evidence[0].source_url == "https://unverified-blog.com/post"
    assert fc.contradicting_evidence[0].reliability_score == 0.30

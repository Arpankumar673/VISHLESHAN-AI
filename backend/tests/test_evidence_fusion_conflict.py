from datetime import datetime, timezone
import pytest
from app.research.evidence.conflict import detect_conflicts
from app.research.evidence.models import EvidenceGroup
from app.research.models import NormalizedEvidence
from app.schemas.evidence import SourceType, VerificationStatus


def make_evidence(claim: str, text: str = "", url: str = "https://example.com") -> NormalizedEvidence:
    full_text = text if text else f"Factual detail for {claim}"
    return NormalizedEvidence(
        claim=claim,
        evidence_text=full_text,
        source_url=url,
        source_title="Source Title",
        source_type=SourceType.OFFICIAL_COMPANY,
        observed_at=datetime.now(timezone.utc),
        reliability_score=0.90,
        confidence_score=0.95,
        verification_status=VerificationStatus.VERIFIED,
        agent_name="company_research_v1",
        content_hash=f"hash_{url}_{claim}",
    )


# 1. Conflicting Years
def test_conflict_conflicting_years():
    ev1 = make_evidence("Acme Corp was founded in 2018", url="https://acme.com/about")
    ev2 = make_evidence("Acme Corp was founded in 2020", url="https://news.com/acme")

    group = EvidenceGroup(
        canonical_claim="Acme Corp founding year",
        evidence=[ev1, ev2],
    )

    updated = detect_conflicts(group)

    assert len(updated.supporting_evidence) == 1
    assert len(updated.contradicting_evidence) == 1
    assert updated.supporting_evidence[0].source_url == "https://acme.com/about"
    assert updated.contradicting_evidence[0].source_url == "https://news.com/acme"


# 2. Conflicting Numeric Values
def test_conflict_conflicting_numeric_values():
    ev1 = make_evidence("Company has 500 employees", url="https://source1.com")
    ev2 = make_evidence("Company has 500 employees", url="https://source2.com")
    ev3 = make_evidence("Company has 1000 employees", url="https://source3.com")

    group = EvidenceGroup(
        canonical_claim="Company employee headcount",
        evidence=[ev1, ev2, ev3],
    )

    updated = detect_conflicts(group)

    assert len(updated.supporting_evidence) == 2
    assert len(updated.contradicting_evidence) == 1
    assert updated.contradicting_evidence[0].source_url == "https://source3.com"


# 3. Conflicting Domains
def test_conflict_conflicting_domains():
    ev1 = make_evidence("Official domain is acme.com", url="https://source1.com")
    ev2 = make_evidence("Official domain is acme.org", url="https://source2.com")

    group = EvidenceGroup(
        canonical_claim="Official website domain",
        evidence=[ev1, ev2],
    )

    updated = detect_conflicts(group)

    assert len(updated.supporting_evidence) == 1
    assert len(updated.contradicting_evidence) == 1


# 4. Conflicting Categorical Values
def test_conflict_conflicting_categorical_values():
    ev1 = make_evidence("CEO is Alice Smith", url="https://source1.com")
    ev2 = make_evidence("CEO is Bob Jones", url="https://source2.com")

    group = EvidenceGroup(
        canonical_claim="Company CEO name",
        evidence=[ev1, ev2],
    )

    updated = detect_conflicts(group)

    assert len(updated.supporting_evidence) == 1
    assert len(updated.contradicting_evidence) == 1


# 5. Non-Conflicting Claims
def test_conflict_non_conflicting_claims():
    ev1 = make_evidence("Google is headquartered in Mountain View, CA", url="https://about.google")
    ev2 = make_evidence("Google maintains offices in California", url="https://google.com/careers")

    group = EvidenceGroup(
        canonical_claim="Google location info",
        evidence=[ev1, ev2],
    )

    updated = detect_conflicts(group)

    assert len(updated.supporting_evidence) == 2
    assert len(updated.contradicting_evidence) == 0


# 6. Ambiguous Claims Remain Unclassified (Safeguard)
def test_conflict_ambiguous_claims_unclassified():
    ev1 = make_evidence("Company expands cloud operations", url="https://s1.com")
    ev2 = make_evidence("Company increases cloud infrastructure investment", url="https://s2.com")

    group = EvidenceGroup(
        canonical_claim="Cloud expansion strategy",
        evidence=[ev1, ev2],
    )

    updated = detect_conflicts(group)

    assert len(updated.supporting_evidence) == 2
    assert len(updated.contradicting_evidence) == 0


# 7. Supporting and Contradicting Evidence Preserved
def test_conflict_supporting_contradicting_evidence_preserved():
    ev1 = make_evidence("Founded in 2015", url="https://official.com")
    ev2 = make_evidence("Founded in 2019", url="https://unverified-blog.com")

    group = EvidenceGroup(
        canonical_claim="Founding year",
        evidence=[ev1, ev2],
    )

    updated = detect_conflicts(group)

    assert len(updated.evidence) == 2
    assert len(updated.supporting_evidence) == 1
    assert len(updated.contradicting_evidence) == 1
    assert updated.supporting_evidence[0].source_url == "https://official.com"
    assert updated.contradicting_evidence[0].source_url == "https://unverified-blog.com"
    # Ensure items inside evidence list are unmutated
    assert updated.evidence[0].content_hash == ev1.content_hash
    assert updated.evidence[1].content_hash == ev2.content_hash

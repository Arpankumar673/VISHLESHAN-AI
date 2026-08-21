from datetime import datetime, timezone
import pytest
from app.research.evidence.grouping import group_evidence, normalize_claim_text
from app.research.models import NormalizedEvidence
from app.research.normalizer import EvidenceNormalizer
from app.schemas.evidence import SourceType, VerificationStatus


def make_evidence(claim: str, url: str = "https://example.com") -> NormalizedEvidence:
    text = f"Sample text for {claim}"
    return NormalizedEvidence(
        claim=claim,
        evidence_text=text,
        source_url=url,
        source_title="Example Title",
        source_type=SourceType.OFFICIAL_COMPANY,
        observed_at=datetime.now(timezone.utc),
        reliability_score=0.90,
        confidence_score=0.95,
        verification_status=VerificationStatus.VERIFIED,
        agent_name="company_research_v1",
        content_hash=EvidenceNormalizer.compute_hash(claim, url, text),
    )


# 1. Whitespace Normalization
def test_claim_whitespace_normalization():
    assert normalize_claim_text("   Google   LLC   operates   search.  ") == "google llc operates search"


# 2. Case Normalization
def test_claim_case_normalization():
    assert normalize_claim_text("MICROSOFT CORPORATION operates Azure") == "microsoft corporation operates azure"


# 3. URL Normalization
def test_claim_url_normalization():
    norm = normalize_claim_text("Official domain is https://www.google.com/")
    assert norm == "official domain is google.com"


# 4. Equivalent Safe Claims Grouped
def test_equivalent_safe_claims_grouped():
    ev1 = make_evidence("Google LLC operates search", "https://google.com/about")
    ev2 = make_evidence("  google llc operates search.  ", "https://google.com/search")

    groups = group_evidence([ev1, ev2])

    assert len(groups) == 1
    assert groups[0].canonical_claim == "Google LLC operates search"
    assert len(groups[0].evidence) == 2


# 5. Unrelated Claims Remain Separate
def test_unrelated_claims_remain_separate():
    ev1 = make_evidence("Google LLC operates search engine", "https://google.com")
    ev2 = make_evidence("Microsoft operates Azure cloud services", "https://azure.microsoft.com")

    groups = group_evidence([ev1, ev2])

    assert len(groups) == 2
    claims = {g.canonical_claim for g in groups}
    assert "Google LLC operates search engine" in claims
    assert "Microsoft operates Azure cloud services" in claims


# 6. Provenance Preserved
def test_grouping_provenance_preserved():
    ev = make_evidence("Apple designs custom silicon", "https://apple.com/newsroom")
    original_hash = ev.content_hash
    original_url = ev.source_url

    groups = group_evidence([ev])

    retained_item = groups[0].evidence[0]
    assert retained_item.content_hash == original_hash
    assert retained_item.source_url == original_url
    assert retained_item.agent_name == "company_research_v1"
    assert retained_item.reliability_score == 0.90

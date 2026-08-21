from datetime import datetime, timezone
import pytest
from app.research.evidence.independence import (
    SourceIndependenceResult,
    assess_source_independence,
    normalize_url_for_independence,
)
from app.research.models import NormalizedEvidence
from app.schemas.evidence import SourceType, VerificationStatus


def make_evidence_item(url: str, claim: str = "Claim text", text: str = "Evidence text", fixed_hash: str = None) -> NormalizedEvidence:
    h = fixed_hash if fixed_hash else f"hash_{url}_{claim}"
    return NormalizedEvidence(
        claim=claim,
        evidence_text=text,
        source_url=url,
        source_title="Title",
        source_type=SourceType.OFFICIAL_COMPANY,
        observed_at=datetime.now(timezone.utc),
        reliability_score=0.90,
        confidence_score=0.95,
        verification_status=VerificationStatus.VERIFIED,
        agent_name="company_research_v1",
        content_hash=h,
    )


# 1. Same Content Hash
def test_independence_same_content_hash():
    ev1 = make_evidence_item("https://siteA.com/page1", fixed_hash="identical_hash_123")
    ev2 = make_evidence_item("https://siteB.com/page2", fixed_hash="identical_hash_123")

    result = assess_source_independence([ev1, ev2])

    assert result.total_sources == 2
    assert result.independent_sources == 1
    assert result.dependent_sources == 1
    assert len(result.source_clusters) == 1


# 2. Same URL
def test_independence_same_url():
    ev1 = make_evidence_item("https://example.com/about", claim="Claim A", fixed_hash="hash_1")
    ev2 = make_evidence_item("http://www.example.com/about/", claim="Claim B", fixed_hash="hash_2")

    result = assess_source_independence([ev1, ev2])

    assert result.total_sources == 2
    assert result.independent_sources == 1
    assert result.dependent_sources == 1


# 3. Different URLs Same Content Hash
def test_independence_different_urls_same_hash():
    ev1 = make_evidence_item("https://mirror1.org/doc", fixed_hash="hash_xyz")
    ev2 = make_evidence_item("https://mirror2.net/doc", fixed_hash="hash_xyz")

    result = assess_source_independence([ev1, ev2])

    assert result.independent_sources == 1
    assert result.dependent_sources == 1


# 4. Independent Domains
def test_independence_distinct_domains():
    ev1 = make_evidence_item("https://gov.in/registry", fixed_hash="hash_gov")
    ev2 = make_evidence_item("https://reuters.com/article", fixed_hash="hash_reuters")

    result = assess_source_independence([ev1, ev2])

    assert result.total_sources == 2
    assert result.independent_sources == 2
    assert result.dependent_sources == 0


# 5. Source Cluster Creation
def test_independence_source_cluster_creation():
    ev1 = make_evidence_item("https://alpha.com", fixed_hash="shared_hash")
    ev2 = make_evidence_item("https://alpha.com/duplicate", fixed_hash="shared_hash")
    ev3 = make_evidence_item("https://beta.com", fixed_hash="unique_hash")

    result = assess_source_independence([ev1, ev2, ev3])

    assert result.total_sources == 3
    assert result.independent_sources == 2
    assert result.dependent_sources == 1
    assert len(result.source_clusters) == 2


# 6. Deterministic Output
def test_independence_deterministic_output():
    ev1 = make_evidence_item("https://site1.com", fixed_hash="h1")
    ev2 = make_evidence_item("https://site2.com", fixed_hash="h2")

    res1 = assess_source_independence([ev1, ev2])
    res2 = assess_source_independence([ev1, ev2])

    assert res1.independent_sources == res2.independent_sources
    assert res1.source_clusters == res2.source_clusters
    assert res1.explanation == res2.explanation

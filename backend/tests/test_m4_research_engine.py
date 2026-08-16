from datetime import datetime, timezone
from uuid import uuid4
import pytest
from app.research.deduplicator import EvidenceDeduplicator
from app.research.identity import IdentityResolver
from app.research.models import IdentityResult, NormalizedEvidence, SourceFinding
from app.research.normalizer import DEFAULT_RELIABILITY_TIERS, EvidenceNormalizer
from app.research.report_builder import ReportBuilder
from app.research.sources.official_website import OfficialWebsiteAdapter
from app.research.sources.search import PublicSearchAdapter
from app.schemas.evidence import SourceType, VerificationStatus


# ------------------------------------------------------------
# 1. Evidence Normalization & Content Hashing
# ------------------------------------------------------------
def test_evidence_normalizer_and_sha256_hash():
    now = datetime.now(timezone.utc)
    raw_finding = SourceFinding(
        claim=" Google operates official domain google.com  ",
        evidence_text="  Official homepage title: 'Google'. Meta description: 'Search the world'.  ",
        source_url="https://google.com",
        source_title="Google Homepage",
        source_type=SourceType.OFFICIAL_COMPANY,
        observed_at=now,
    )

    normalized = EvidenceNormalizer.normalize_finding(raw_finding)

    assert normalized.claim == "Google operates official domain google.com"
    assert "Search the world" in normalized.evidence_text
    assert normalized.reliability_score == 0.90
    assert normalized.verification_status == VerificationStatus.VERIFIED
    assert len(normalized.content_hash) == 64  # SHA-256 hex string

    # Verify hash is strictly deterministic
    second_hash = EvidenceNormalizer.compute_hash(
        normalized.claim,
        normalized.source_url,
        normalized.evidence_text,
    )
    assert normalized.content_hash == second_hash


# ------------------------------------------------------------
# 2. Source Reliability Defaults
# ------------------------------------------------------------
def test_source_reliability_defaults():
    assert DEFAULT_RELIABILITY_TIERS[SourceType.GOVERNMENT] == 0.98
    assert DEFAULT_RELIABILITY_TIERS[SourceType.REGULATOR] == 0.98
    assert DEFAULT_RELIABILITY_TIERS[SourceType.CERTIFICATION_BODY] == 0.95
    assert DEFAULT_RELIABILITY_TIERS[SourceType.OFFICIAL_COMPANY] == 0.90
    assert DEFAULT_RELIABILITY_TIERS[SourceType.OFFICIAL_CAREERS] == 0.90
    assert DEFAULT_RELIABILITY_TIERS[SourceType.NEWS] == 0.80
    assert DEFAULT_RELIABILITY_TIERS[SourceType.PROFESSIONAL_NETWORK] == 0.65
    assert DEFAULT_RELIABILITY_TIERS[SourceType.OTHER] == 0.50


# ------------------------------------------------------------
# 3. Deduplication
# ------------------------------------------------------------
def test_evidence_deduplication():
    now = datetime.now(timezone.utc)
    ev1 = NormalizedEvidence(
        claim="Infosys is headquartered in Bengaluru",
        evidence_text="Corporate headquarters located at Electronics City, Bengaluru.",
        source_url="https://infosys.com/about",
        source_type=SourceType.OFFICIAL_COMPANY,
        observed_at=now,
        reliability_score=0.90,
        confidence_score=0.95,
        verification_status=VerificationStatus.VERIFIED,
        content_hash=EvidenceNormalizer.compute_hash(
            "Infosys is headquartered in Bengaluru",
            "https://infosys.com/about",
            "Corporate headquarters located at Electronics City, Bengaluru.",
        ),
    )
    # Exact duplicate
    ev2 = NormalizedEvidence(
        claim="Infosys is headquartered in Bengaluru",
        evidence_text="Corporate headquarters located at Electronics City, Bengaluru.",
        source_url="https://infosys.com/about",
        source_type=SourceType.OFFICIAL_COMPANY,
        observed_at=now,
        reliability_score=0.90,
        confidence_score=0.95,
        verification_status=VerificationStatus.VERIFIED,
        content_hash=ev1.content_hash,
    )
    # Distinct claim
    ev3 = NormalizedEvidence(
        claim="Infosys operates official careers portal",
        evidence_text="Hiring portal at career.infosys.com",
        source_url="https://career.infosys.com",
        source_type=SourceType.OFFICIAL_CAREERS,
        observed_at=now,
        reliability_score=0.90,
        confidence_score=0.95,
        verification_status=VerificationStatus.VERIFIED,
        content_hash=EvidenceNormalizer.compute_hash(
            "Infosys operates official careers portal",
            "https://career.infosys.com",
            "Hiring portal at career.infosys.com",
        ),
    )

    deduped = EvidenceDeduplicator.deduplicate([ev1, ev2, ev3])
    assert len(deduped) == 2
    assert deduped[0].content_hash == ev1.content_hash
    assert deduped[1].content_hash == ev3.content_hash


# ------------------------------------------------------------
# 4. Identity Resolution
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_identity_resolution():
    resolver = IdentityResolver()
    identity = await resolver.resolve(
        company_name="Microsoft",
        company_url="microsoft.com",
    )

    assert identity.canonical_name == "Microsoft"
    assert identity.official_domain == "microsoft.com"
    assert identity.official_website == "https://microsoft.com"
    assert len(identity.identifiers) >= 1
    assert identity.identifiers[0]["identifier_type"] == "official_domain"


# ------------------------------------------------------------
# 5. Report Builder
# ------------------------------------------------------------
def test_report_builder_structured_report():
    now = datetime.now(timezone.utc)
    identity = IdentityResult(
        canonical_name="Tata Consultancy Services",
        official_domain="tcs.com",
        official_website="https://tcs.com",
        description="Global IT services and consulting organization.",
        industry="Information Technology",
        headquarters="Mumbai, India",
    )

    evidence_items = [
        NormalizedEvidence(
            claim="TCS operates official website at tcs.com",
            evidence_text="Homepage and domain registered to Tata Consultancy Services.",
            source_url="https://tcs.com",
            source_title="TCS Homepage",
            source_type=SourceType.OFFICIAL_COMPANY,
            observed_at=now,
            reliability_score=0.90,
            confidence_score=0.95,
            verification_status=VerificationStatus.VERIFIED,
            content_hash="mock-hash-1",
        ),
        NormalizedEvidence(
            claim="TCS official careers portal active",
            evidence_text="Recruitment portal available at tcs.com/careers.",
            source_url="https://tcs.com/careers",
            source_title="TCS Careers",
            source_type=SourceType.OFFICIAL_CAREERS,
            observed_at=now,
            reliability_score=0.90,
            confidence_score=0.95,
            verification_status=VerificationStatus.VERIFIED,
            content_hash="mock-hash-2",
        ),
    ]

    report = ReportBuilder.build_report_content(identity, evidence_items)

    assert "overview" in report
    assert report["overview"]["name"] == "Tata Consultancy Services"
    assert report["overview"]["official_domain"] == "tcs.com"
    assert "official_resources" in report
    assert report["official_resources"]["careers_portal"] == "https://tcs.com/careers"
    assert "trust_score" in report
    assert report["trust_score"]["score"] >= 75.0
    assert report["trust_score"]["risk_level"] == "low"
    assert len(report["references"]) == 2
    assert len(report["evidence"]) == 2
    assert report["references"][0]["url"] == "https://tcs.com"


# ------------------------------------------------------------
# 6. Official Website Adapter (Mock HTML)
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_official_website_adapter_parsing():
    sample_html = """
    <!DOCTYPE html>
    <html>
      <head>
        <title>Acme Corporation — Leading Cloud Solutions</title>
        <meta name="description" content="Acme Corporation provides enterprise cloud infrastructure and security.">
      </head>
      <body>
        <h1>Welcome to Acme</h1>
        <p>Empowering organizations globally with scalable technology.</p>
        <a href="/about">About Us</a>
        <a href="/careers">Join Our Team</a>
      </body>
    </html>
    """

    adapter = OfficialWebsiteAdapter()
    # Mock fetch_html to avoid making live network calls in unit tests
    async def mock_fetch(url):
        return sample_html

    adapter.fetch_html = mock_fetch

    findings = await adapter.collect(company_name="Acme Corporation", domain="acme.com")

    assert len(findings) >= 1
    assert any("acme.com" in f.source_url for f in findings)
    assert any("Acme Corporation" in f.claim for f in findings)

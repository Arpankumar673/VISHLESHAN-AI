from datetime import datetime, timezone
from uuid import uuid4
from app.research.models import IdentityResult, NormalizedEvidence
from app.research.report_builder import ReportBuilder
from app.research.validator import ReportValidator
from app.schemas.evidence import SourceType, VerificationStatus


def test_report_validator_sanitizes_placeholder_urls():
    raw_content = {
        "executive_intelligence": {
            "official_domain": "google.com",
        },
        "registration_findings": {
            "findings": [
                {
                    "authority": "Registry",
                    "source_url": "https://example.com/fake",
                }
            ]
        },
        "domain_provenance": {
            "canonical_url": "about:blank",
        },
    }

    evidence_items = []
    validated = ReportValidator.validate_report(raw_content, evidence_items)

    assert validated["registration_findings"]["findings"][0]["source_url"] is None
    assert validated["domain_provenance"]["canonical_url"] is None


def test_report_validator_reconciles_contradictions():
    raw_content = {
        "executive_intelligence": {
            "verified_claims": 5,
        },
        "domain_provenance": {
            "status": "verified",
        },
        "registration_findings": {
            "status": "verified",
        },
        "risk_score_explanation": {
            "factors": ["Public registration cross-match: VERIFIED"],
        },
    }

    # Pass 0 verified evidence items
    evidence_items = [
        NormalizedEvidence(
            claim="Unverified claim",
            evidence_text="Some text",
            source_url="https://unverified.org",
            source_type=SourceType.OTHER,
            verification_status=VerificationStatus.UNVERIFIED,
            reliability_score=0.5,
            confidence_score=0.5,
            observed_at=datetime.now(timezone.utc),
            content_hash="hash123",
        )
    ]

    validated = ReportValidator.validate_report(raw_content, evidence_items)

    # Must be reconciled to unverified / unable to verify
    assert validated["executive_intelligence"]["verified_claims"] == 0
    assert validated["domain_provenance"]["status"] == "unverified"
    assert validated["registration_findings"]["status"] == "unable_to_verify"
    assert "Public registration cross-match: UNABLE_TO_VERIFY" in validated["risk_score_explanation"]["factors"][1]


def test_report_builder_evidence_driven():
    identity = IdentityResult(
        canonical_name="Google LLC",
        official_domain="google.com",
        official_website="https://google.com",
        description="Search engine & cloud technology corporate entity.",
        industry="Technology",
        headquarters="Mountain View, CA",
    )

    ev1 = NormalizedEvidence(
        claim="Google operates official domain google.com",
        evidence_text="HTTPS probe 200 OK from https://google.com",
        source_url="https://google.com",
        source_title="Google Homepage",
        source_type=SourceType.OFFICIAL_COMPANY,
        verification_status=VerificationStatus.VERIFIED,
        reliability_score=0.95,
        confidence_score=0.98,
        observed_at=datetime.now(timezone.utc),
        content_hash="hash_google_1",
    )

    # Duplicate evidence item
    ev2 = NormalizedEvidence(
        claim="Google operates official domain google.com",
        evidence_text="HTTPS probe 200 OK from https://google.com",
        source_url="https://google.com",
        source_title="Google Homepage",
        source_type=SourceType.OFFICIAL_COMPANY,
        verification_status=VerificationStatus.VERIFIED,
        reliability_score=0.95,
        confidence_score=0.98,
        observed_at=datetime.now(timezone.utc),
        content_hash="hash_google_1",
    )

    content = ReportBuilder.build_report_content(identity, [ev1, ev2])

    assert content is not None
    # Deduplication check: evidence list should contain 1 item, not 2
    assert len(content["evidence"]) == 1
    assert content["executive_intelligence"]["verified_claims"] == 1
    assert content["domain_provenance"]["status"] == "verified"
    assert content["registration_findings"]["status"] == "unable_to_verify"

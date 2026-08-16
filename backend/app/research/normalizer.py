import hashlib
import re
from typing import Dict
from app.research.models import NormalizedEvidence, SourceFinding
from app.schemas.evidence import SourceType, VerificationStatus

# Preliminary deterministic M4 source reliability configuration defaults
DEFAULT_RELIABILITY_TIERS: Dict[SourceType, float] = {
    SourceType.GOVERNMENT: 0.98,
    SourceType.REGULATOR: 0.98,
    SourceType.CERTIFICATION_BODY: 0.95,
    SourceType.OFFICIAL_COMPANY: 0.90,
    SourceType.OFFICIAL_CAREERS: 0.90,
    SourceType.OFFICIAL_ANNOUNCEMENT: 0.88,
    SourceType.NEWS: 0.80,
    SourceType.PROFESSIONAL_NETWORK: 0.65,
    SourceType.EMPLOYEE_REVIEW: 0.50,
    SourceType.FORUM: 0.50,
    SourceType.BLOG: 0.50,
    SourceType.OTHER: 0.50,
}


class EvidenceNormalizer:
    """Normalizes raw findings into auditable, hashed, and scored evidence records."""

    @staticmethod
    def normalize_text(text: str) -> str:
        """Strip and collapse multiple consecutive whitespaces."""
        if not text:
            return ""
        return re.sub(r"\s+", " ", text).strip()

    @classmethod
    def compute_hash(cls, claim: str, source_url: str, evidence_text: str) -> str:
        """
        Calculates SHA-256 hash of normalized evidence attributes for deterministic deduplication.
        """
        payload = f"{cls.normalize_text(claim).lower()}|{source_url.strip().lower()}|{cls.normalize_text(evidence_text).lower()}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    @classmethod
    def normalize_finding(cls, finding: SourceFinding) -> NormalizedEvidence:
        norm_claim = cls.normalize_text(finding.claim)
        norm_text = cls.normalize_text(finding.evidence_text)
        norm_url = finding.source_url.strip()

        reliability = DEFAULT_RELIABILITY_TIERS.get(finding.source_type, 0.50)
        confidence = 0.95 if reliability >= 0.90 else (0.80 if reliability >= 0.70 else 0.60)

        # Verification status derivation
        if reliability >= 0.90:
            verification_status = VerificationStatus.VERIFIED
        else:
            verification_status = VerificationStatus.UNVERIFIED

        content_hash = cls.compute_hash(norm_claim, norm_url, norm_text)

        return NormalizedEvidence(
            claim=norm_claim,
            evidence_text=norm_text,
            source_url=norm_url,
            source_title=finding.source_title or norm_url,
            source_type=finding.source_type,
            published_at=finding.published_at,
            observed_at=finding.observed_at,
            reliability_score=reliability,
            confidence_score=confidence,
            verification_status=verification_status,
            agent_name="company_research_v1",
            content_hash=content_hash,
        )

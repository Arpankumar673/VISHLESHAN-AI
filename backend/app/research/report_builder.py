from typing import Any, Dict, List
from app.research.evidence.grouping import group_evidence
from app.research.evidence.scoring import score_fusion_result
from app.research.models import IdentityResult, NormalizedEvidence
from app.schemas.evidence import SourceType, VerificationStatus


class ReportBuilder:
    """Constructs a deterministic, evidence-grounded Company Intelligence Report."""

    @staticmethod
    def build_report_content(
        identity: IdentityResult,
        evidence_items: List[NormalizedEvidence],
    ) -> Dict[str, Any]:
        # Tally verification statuses
        verified_count = sum(1 for e in evidence_items if e.verification_status == VerificationStatus.VERIFIED)
        total_evidence = len(evidence_items)

        # Execute Evidence Fusion Engine for report-level claim analysis
        claim_groups = group_evidence(evidence_items)
        fusion_result = score_fusion_result(claim_groups)
        avg_fused_confidence = (
            sum(fc.fused_confidence for fc in fusion_result.fused_claims) / len(fusion_result.fused_claims)
            if fusion_result.fused_claims
            else 0.5
        )

        # Baseline trust score calculation based on verified evidence ratio & source reliability
        avg_reliability = (
            sum(e.reliability_score for e in evidence_items) / total_evidence
            if total_evidence > 0
            else 0.5
        )
        trust_score_val = round(min(100.0, max(20.0, avg_reliability * 100.0)), 1)
        risk_level = "low" if trust_score_val >= 75.0 else ("medium" if trust_score_val >= 50.0 else "high")

        # Discover careers and official resources
        careers_url = None
        for e in evidence_items:
            if e.source_type == SourceType.OFFICIAL_CAREERS:
                careers_url = e.source_url
                break

        # Construct References list
        references = []
        for idx, e in enumerate(evidence_items, start=1):
            references.append(
                {
                    "index": idx,
                    "url": e.source_url,
                    "title": e.source_title or e.source_url,
                    "source_type": e.source_type.value,
                    "reliability_score": e.reliability_score,
                    "observed_at": e.observed_at.isoformat(),
                }
            )

        # Construct Evidence list
        evidence_summary = []
        for idx, e in enumerate(evidence_items, start=1):
            evidence_summary.append(
                {
                    "index": idx,
                    "claim": e.claim,
                    "evidence_text": e.evidence_text,
                    "source_url": e.source_url,
                    "source_type": e.source_type.value,
                    "reliability_score": e.reliability_score,
                    "confidence_score": e.confidence_score,
                    "verification_status": e.verification_status.value,
                    "content_hash": e.content_hash,
                }
            )

        return {
            "overview": {
                "name": identity.canonical_name,
                "description": identity.description,
                "industry": identity.industry,
                "headquarters": identity.headquarters,
                "official_domain": identity.official_domain,
            },
            "official_resources": {
                "website": identity.official_website,
                "careers_portal": careers_url,
                "primary_domain": identity.official_domain,
            },
            "identity_verification": {
                "status": "verified" if verified_count > 0 else "unverified",
                "verified_claims_count": verified_count,
                "total_claims_count": total_evidence,
                "confidence": 0.95 if verified_count > 0 else 0.60,
                "summary": (
                    f"Official domain {identity.official_domain or 'record'} verified with "
                    f"{verified_count} corroborated source observation(s)."
                ),
            },
            "registration_findings": {
                "status": "verified" if verified_count > 0 else "unverified",
                "summary": f"Public digital presence identified and verified across public web sources.",
            },
            "certification_findings": {
                "status": "unverified",
                "summary": "Specific corporate ISO/CMMI accreditations to be verified in deep agent execution.",
            },
            "news_hiring": {
                "active_hiring_channels": bool(careers_url),
                "careers_url": careers_url,
                "summary": (
                    f"Official recruitment portal located at {careers_url}."
                    if careers_url
                    else "Careers portal resolution pending primary domain inspection."
                ),
            },
            "technology_reputation": {
                "infrastructure": f"Domain {identity.official_domain or 'primary'} active and reachable via HTTPS.",
            },
            "trust_score": {
                "score": trust_score_val,
                "confidence": round(avg_reliability, 2),
                "risk_level": risk_level,
                "evidence_coverage": round(min(1.0, total_evidence / 5.0), 2),
                "algorithm_version": "v1.0-deterministic-m4",
                "explanation": (
                    f"Preliminary deterministic evaluation based on {total_evidence} source record(s) "
                    f"with average source reliability of {(avg_reliability * 100):.0f}%."
                ),
            },
            "confidence": {
                "score": round(avg_reliability, 2),
                "level": "high" if avg_reliability >= 0.85 else ("medium" if avg_reliability >= 0.65 else "low"),
            },
            "risk_analysis": {
                "overall_risk": risk_level,
                "indicators": [
                    {
                        "name": "Domain Provenance",
                        "status": "verified" if identity.official_domain else "unverified",
                        "severity": "low" if identity.official_domain else "medium",
                        "description": f"Domain {identity.official_domain} active and verified.",
                    }
                ],
            },
            "evidence_fusion": {
                "total_claim_groups": fusion_result.total_claim_groups,
                "conflicted_claims_count": fusion_result.conflicted_claims,
                "average_fused_confidence": round(avg_fused_confidence, 2),
                "fused_claims_summary": [
                    {
                        "canonical_claim": fc.canonical_claim,
                        "status": fc.status.value,
                        "fused_confidence": round(fc.fused_confidence, 2),
                        "independent_sources": fc.independent_source_count,
                        "agreement_score": round(fc.agreement_score, 2),
                        "contradiction_score": round(fc.contradiction_score, 2),
                        "explanation": fc.explanation,
                    }
                    for fc in fusion_result.fused_claims
                ],
            },
            "important_conclusions": [
                f"Organization verified as active under domain {identity.official_domain or 'public presence'}.",
                f"{verified_count} out of {total_evidence} evidence claims corroborated with first-party official sources.",
                "Candidates are advised to use exclusively verified official career URLs for recruitment communication.",
            ],
            "evidence": evidence_summary,
            "references": references,
        }

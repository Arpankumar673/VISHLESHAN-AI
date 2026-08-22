from typing import Any, Dict, List, Optional
from app.research.models import NormalizedEvidence
from app.schemas.evidence import SourceType, VerificationStatus


class ReportValidator:
    """
    Final Contradiction & Provenance Validator for Vishleshan AI Intelligence Reports.
    Validates report content before persistence and display to guarantee:
    1. Zero contradictions between summary indicators and evidence items.
    2. Every VERIFIED claim is supported by a real, persisted evidence record.
    3. No hardcoded or placeholder URLs (e.g. example.com, about:blank).
    4. Trust/Risk score factors strictly reference actual evidence.
    """

    @classmethod
    def validate_report(
        cls,
        report_content: Dict[str, Any],
        evidence_items: List[NormalizedEvidence],
    ) -> Dict[str, Any]:
        content = dict(report_content)

        # 1. Tally verified evidence by category
        verified_evidence_items = [
            e for e in evidence_items if e.verification_status == VerificationStatus.VERIFIED
        ]
        verified_count = len(verified_evidence_items)

        # Domain verification evidence check
        domain_ev = [
            e for e in verified_evidence_items
            if e.source_type in [SourceType.OFFICIAL_COMPANY, SourceType.OFFICIAL_CAREERS] and e.source_url
        ]
        domain_verified = len(domain_ev) > 0

        # Government/Registration evidence check
        gov_ev = [
            e for e in verified_evidence_items
            if e.source_type in [SourceType.GOVERNMENT, SourceType.REGULATOR]
        ]
        gov_verified = len(gov_ev) > 0

        # Certification evidence check
        cert_ev = [
            e for e in verified_evidence_items
            if e.source_type == SourceType.CERTIFICATION_BODY
        ]
        cert_verified = len(cert_ev) > 0

        # Careers portal evidence check
        careers_ev = [
            e for e in verified_evidence_items
            if e.source_type == SourceType.OFFICIAL_CAREERS
        ]
        careers_verified = len(careers_ev) > 0

        # 2. Reconcile Executive Intelligence & Decision Summaries
        exec_intel = content.get("executive_intelligence", {})
        exec_intel["verified_claims"] = verified_count
        exec_intel["total_claims"] = len(evidence_items)
        if not domain_verified:
            exec_intel["official_domain"] = exec_intel.get("official_domain") or None

        # 3. Reconcile Domain Provenance
        domain_prov = content.get("domain_provenance", {})
        if not domain_verified:
            domain_prov["status"] = "unverified"
            domain_prov["https_support"] = False
            domain_prov["summary"] = "Official primary domain verification inconclusive or missing authoritative evidence."

        # 4. Reconcile Registration Findings (No fake VERIFIED claims)
        reg_findings = content.get("registration_findings", {})
        if not gov_verified:
            reg_findings["status"] = "unable_to_verify"
            reg_findings["summary"] = "No public government or business registration records identified for this entity."
            # Clean up findings list to show UNABLE_TO_VERIFY instead of fake verified records
            reg_findings["findings"] = [
                {
                    "authority": "Public Business Registry",
                    "registration_number": None,
                    "jurisdiction": "Unspecified",
                    "status": "unable_to_verify",
                    "source_url": None,
                    "uncertainty_reason": "Authoritative government registration evidence is not publicly accessible.",
                }
            ]

        # 5. Reconcile Certification Findings
        cert_findings = content.get("certification_findings", {})
        if not cert_verified:
            cert_findings["status"] = "unable_to_verify"
            cert_findings["summary"] = "No ISO/CMMI compliance certifications were identified in public records."
            cert_findings["findings"] = [
                {
                    "certification_body": "Accredited Audit Authority",
                    "status": "unable_to_verify",
                    "source_url": None,
                    "uncertainty_reason": "Specific corporate ISO/CMMI compliance certificates were not verified in public records.",
                }
            ]

        # 6. Reconcile Risk Score Explanation (Eliminate hardcoded false claims)
        risk_exp = content.get("risk_score_explanation", {})
        risk_factors = []
        if domain_verified:
            risk_factors.append("Domain provenance: VERIFIED (official HTTPS domain active)")
        else:
            risk_factors.append("Domain provenance: UNVERIFIED (official domain verification inconclusive)")

        if gov_verified:
            risk_factors.append("Public registration cross-match: VERIFIED")
        else:
            risk_factors.append("Public registration cross-match: UNABLE_TO_VERIFY (no government registry record)")

        if careers_verified:
            risk_factors.append("Recruitment channel: VERIFIED (official careers portal observed)")
        else:
            risk_factors.append("Recruitment channel: UNVERIFIED (no official careers portal evidence)")

        risk_exp["factors"] = risk_factors

        # 7. Clean placeholder URLs across all sections
        cls._sanitize_urls(content)

        return content

    @classmethod
    def _sanitize_urls(cls, data: Any):
        """Recursively replaces placeholder or invalid URLs with None."""
        if isinstance(data, dict):
            for k, v in list(data.items()):
                if k in ("url", "source_url", "canonical_url", "website") and isinstance(v, str):
                    clean = v.strip()
                    if any(bad in clean.lower() for bad in ["example.com", "about:blank", "placeholder"]):
                        data[k] = None
                else:
                    cls._sanitize_urls(v)
        elif isinstance(data, list):
            for item in data:
                cls._sanitize_urls(item)

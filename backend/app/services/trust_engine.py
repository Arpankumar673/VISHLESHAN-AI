from datetime import datetime, timezone
import math
import re
from typing import Any, Dict, List, Optional, Tuple, Union
from uuid import UUID

from app.core.logging import logger
from app.research.models import NormalizedEvidence
from app.schemas.evidence import SourceType, VerificationStatus
from app.schemas.trust import (
    ConflictLevel,
    ConflictSummary,
    DimensionScore,
    RiskAdjustment,
    TrustIndexResult,
    TrustVerificationStatus,
)
from app.services.claim_normalizer import ClaimNormalizer
from app.services.nli_conflict_engine import NLIConflictEngine, NLILabel

TRUST_MODEL_VERSION = "v1"

TRUST_WEIGHTS: Dict[str, float] = {
    "identity": 0.20,
    "technical_provenance": 0.20,
    "regulatory": 0.25,
    "evidence": 0.20,
    "risk": 0.15,
}

SOURCE_TIERS: Dict[str, float] = {
    "government": 1.00,
    "regulator": 1.00,
    "certification_body": 0.95,
    "official_company": 0.90,
    "official_careers": 0.88,
    "official_announcement": 0.85,
    "news": 0.75,
    "professional_network": 0.70,
    "employee_review": 0.60,
    "forum": 0.50,
    "blog": 0.50,
    "other": 0.40,
}


def validate_trust_config(
    weights: Dict[str, float] = TRUST_WEIGHTS,
    version: str = TRUST_MODEL_VERSION,
) -> None:
    """
    Validates model configuration parameters.
    Enforces non-negative weights, required dimensions, sum equal to 1.0, and version presence.
    """
    if not version or not isinstance(version, str):
        raise ValueError("TRUST_MODEL_VERSION must be a non-empty string.")

    required_dimensions = {"identity", "technical_provenance", "regulatory", "evidence", "risk"}
    missing = required_dimensions - set(weights.keys())
    if missing:
        raise ValueError(f"Missing required trust model dimensions: {missing}")

    for k, v in weights.items():
        if not isinstance(v, (int, float)) or v < 0:
            raise ValueError(f"Trust model weight for '{k}' must be a non-negative number. Got: {v}")

    total_weight = sum(weights.values())
    if not math.isclose(total_weight, 1.0, rel_tol=1e-5):
        raise ValueError(f"Trust model weights must sum to 1.0. Current sum: {total_weight:.4f}")


class TrustEngine:
    """
    Deterministic Vishleshan AI v2 Trust Scoring Engine.
    Computes explainable 5-dimension Trust Index grounded in normalized evidence data.
    """

    def __init__(
        self,
        weights: Dict[str, float] = TRUST_WEIGHTS,
        model_version: str = TRUST_MODEL_VERSION,
    ):
        validate_trust_config(weights=weights, version=model_version)
        self.weights = weights
        self.model_version = model_version

    def _calculate_freshness_factor(
        self,
        published_at: Optional[datetime],
        observed_at: Optional[datetime],
        source_type: str,
    ) -> float:
        """
        Calculates source-aware temporal evidence freshness factor (0.5 to 1.0).
        Different source types decay at different rates.
        """
        ref_dt = published_at or observed_at or datetime.now(timezone.utc)
        if ref_dt.tzinfo is None:
            ref_dt = ref_dt.replace(tzinfo=timezone.utc)

        now = datetime.now(timezone.utc)
        age_days = max(0, (now - ref_dt).days)

        # Half-life in days by source category
        if source_type in ("government", "regulator", "certification_body"):
            half_life_days = 1825  # 5 years
        elif source_type in ("official_company", "official_announcement"):
            half_life_days = 730   # 2 years
        elif source_type == "official_careers":
            half_life_days = 90    # 3 months
        elif source_type == "news":
            half_life_days = 365   # 1 year
        else:
            half_life_days = 180   # 6 months

        # Exponential decay factor bounded between 0.50 and 1.00
        decay = math.exp(-0.693 * (age_days / half_life_days))
        return round(max(0.50, min(1.00, decay)), 4)

    def calculate_entity_identity_dimension(
        self,
        evidence_items: List[NormalizedEvidence],
        target_name: str,
        target_domain: Optional[str],
    ) -> DimensionScore:
        """
        Dimension 1: Entity Identity (20%)
        Evaluates canonical name match, official domain presence, JSON-LD schema, and identity corroboration.
        """
        weight = self.weights["identity"]
        identity_evidence = [
            e for e in evidence_items
            if e.source_type in (SourceType.OFFICIAL_COMPANY, SourceType.GOVERNMENT, SourceType.REGULATOR)
            or "identity" in (getattr(e, "category", "") or "").lower()
            or "domain" in e.claim.lower()
        ]

        evidence_ids = [str(e.id) for e in identity_evidence if hasattr(e, "id") and e.id]

        if not identity_evidence:
            return DimensionScore(
                name="Entity Identity",
                score=50.0,
                confidence=0.40,
                weight=weight,
                weighted_score=round(50.0 * weight, 2),
                verification_status=TrustVerificationStatus.UNABLE_TO_VERIFY,
                evidence_count=0,
                evidence_ids=[],
                details={"reason": "No corporate identity evidence collected."},
            )

        has_official_domain = False
        has_verified_name = False
        has_json_ld_schema = False
        conflicts = False

        for e in identity_evidence:
            claim_lower = e.claim.lower()
            if "operates official domain" in claim_lower or (target_domain and target_domain in claim_lower):
                has_official_domain = True
            if target_name.lower() in claim_lower or "legal entity name" in claim_lower:
                has_verified_name = True
            if "json-ld" in e.evidence_text.lower() or "schema" in e.evidence_text.lower():
                has_json_ld_schema = True
            if e.verification_status == VerificationStatus.CONFLICTING:
                conflicts = True

        if conflicts:
            status = TrustVerificationStatus.CONFLICTING
            score = 55.0
            confidence = 0.50
        elif has_official_domain and has_verified_name:
            status = TrustVerificationStatus.VERIFIED
            score = 95.0 if has_json_ld_schema else 85.0
            confidence = 0.90
        elif has_official_domain or has_verified_name:
            status = TrustVerificationStatus.PARTIALLY_VERIFIED
            score = 70.0
            confidence = 0.70
        else:
            status = TrustVerificationStatus.UNABLE_TO_VERIFY
            score = 50.0
            confidence = 0.45

        return DimensionScore(
            name="Entity Identity",
            score=round(score, 1),
            confidence=round(confidence, 2),
            weight=weight,
            weighted_score=round(score * weight, 2),
            verification_status=status,
            evidence_count=len(identity_evidence),
            evidence_ids=evidence_ids,
            details={
                "has_official_domain": has_official_domain,
                "has_verified_name": has_verified_name,
                "has_json_ld_schema": has_json_ld_schema,
                "conflicts_detected": conflicts,
            },
        )

    def calculate_technical_provenance_dimension(
        self,
        evidence_items: List[NormalizedEvidence],
        target_domain: Optional[str],
    ) -> DimensionScore:
        """
        Dimension 2: Technical / Domain Provenance (20%)
        Evaluates HTTPS/TLS observability, DNS responsiveness, and domain consistency.
        CRITICAL RULE: Only score signals that were ACTUALLY observed. Missing evidence = UNABLE_TO_VERIFY with low confidence.
        """
        weight = self.weights["technical_provenance"]
        tech_evidence = [
            e for e in evidence_items
            if e.agent_name == "technology_reputation"
            or "https" in e.claim.lower()
            or "infrastructure" in e.claim.lower()
            or "tls" in e.evidence_text.lower()
            or "200 ok" in e.claim.lower()
        ]

        evidence_ids = [str(e.id) for e in tech_evidence if hasattr(e, "id") and e.id]

        if not target_domain or not tech_evidence:
            return DimensionScore(
                name="Technical / Domain Provenance",
                score=50.0,
                confidence=0.30,
                weight=weight,
                weighted_score=round(50.0 * weight, 2),
                verification_status=TrustVerificationStatus.UNABLE_TO_VERIFY,
                evidence_count=0,
                evidence_ids=[],
                details={
                    "https_observed": False,
                    "dns_active": False,
                    "domain_consistent": False,
                    "reason": "Technical infrastructure evidence was not directly observed or domain un-configured.",
                },
            )

        https_observed = False
        dns_active = False
        domain_consistent = False

        for e in tech_evidence:
            claim_lower = e.claim.lower()
            text_lower = e.evidence_text.lower()
            full_text = f"{claim_lower} {text_lower}"

            if any(term in full_text for term in ["https", "tls", "ssl", "200 ok", "dns active", "infrastructure"]):
                if not any(neg in full_text for neg in ["no https", "invalid ssl", "dns failure", "down"]):
                    https_observed = True
                    dns_active = True

            if target_domain and (target_domain.lower() in (e.source_url or "").lower() or target_domain.lower() in full_text):
                domain_consistent = True

        if https_observed and domain_consistent:
            status = TrustVerificationStatus.VERIFIED
            score = 90.0
            confidence = 0.88
        elif https_observed or dns_active:
            status = TrustVerificationStatus.PARTIALLY_VERIFIED
            score = 75.0
            confidence = 0.75
        else:
            status = TrustVerificationStatus.UNABLE_TO_VERIFY
            score = 50.0
            confidence = 0.35

        return DimensionScore(
            name="Technical / Domain Provenance",
            score=round(score, 1),
            confidence=round(confidence, 2),
            weight=weight,
            weighted_score=round(score * weight, 2),
            verification_status=status,
            evidence_count=len(tech_evidence),
            evidence_ids=evidence_ids,
            details={
                "https_observed": https_observed,
                "dns_active": dns_active,
                "domain_consistent": domain_consistent,
            },
        )


    def calculate_regulatory_dimension(
        self,
        evidence_items: List[NormalizedEvidence],
    ) -> DimensionScore:
        """
        Dimension 3: Regulatory / Compliance (25%)
        Evaluates official government filings, corporate registrations, and recognized certifications.
        Missing public evidence = UNABLE_TO_VERIFY with reduced confidence, NEVER "fraudulent" or "fake".
        """
        weight = self.weights["regulatory"]
        regulatory_evidence = [
            e for e in evidence_items
            if e.source_type in (SourceType.GOVERNMENT, SourceType.REGULATOR, SourceType.CERTIFICATION_BODY)
            or "registration" in e.claim.lower()
            or "certification" in e.claim.lower()
        ]

        evidence_ids = [str(e.id) for e in regulatory_evidence if hasattr(e, "id") and e.id]

        if not regulatory_evidence:
            return DimensionScore(
                name="Regulatory / Compliance",
                score=50.0,
                confidence=0.40,
                weight=weight,
                weighted_score=round(50.0 * weight, 2),
                verification_status=TrustVerificationStatus.UNABLE_TO_VERIFY,
                evidence_count=0,
                evidence_ids=[],
                details={"reason": "No public government registration or regulatory filing evidence available."},
            )

        has_gov_registry = False
        has_certification = False
        is_conflicting = False

        for e in regulatory_evidence:
            if e.verification_status == VerificationStatus.CONFLICTING:
                is_conflicting = True
            if e.source_type in (SourceType.GOVERNMENT, SourceType.REGULATOR) and e.verification_status == VerificationStatus.VERIFIED:
                has_gov_registry = True
            if e.source_type == SourceType.CERTIFICATION_BODY and e.verification_status == VerificationStatus.VERIFIED:
                has_certification = True

        if is_conflicting:
            status = TrustVerificationStatus.CONFLICTING
            score = 40.0
            confidence = 0.40
        elif has_gov_registry and has_certification:
            status = TrustVerificationStatus.VERIFIED
            score = 98.0
            confidence = 0.95
        elif has_gov_registry:
            status = TrustVerificationStatus.VERIFIED
            score = 90.0
            confidence = 0.90
        elif has_certification:
            status = TrustVerificationStatus.PARTIALLY_VERIFIED
            score = 75.0
            confidence = 0.75
        else:
            status = TrustVerificationStatus.UNABLE_TO_VERIFY
            score = 50.0
            confidence = 0.40

        return DimensionScore(
            name="Regulatory / Compliance",
            score=round(score, 1),
            confidence=round(confidence, 2),
            weight=weight,
            weighted_score=round(score * weight, 2),
            verification_status=status,
            evidence_count=len(regulatory_evidence),
            evidence_ids=evidence_ids,
            details={
                "has_gov_registry": has_gov_registry,
                "has_certification": has_certification,
                "is_conflicting": is_conflicting,
            },
        )

    def calculate_evidence_fusion_dimension(
        self,
        evidence_items: List[NormalizedEvidence],
    ) -> DimensionScore:
        """
        Dimension 4: Evidence Reliability & Fusion (20%)
        Evaluates source tiers, deduplicates same-source copies before corroboration scoring, and applies temporal freshness decay.
        """
        weight = self.weights["evidence"]
        if not evidence_items:
            return DimensionScore(
                name="Evidence Reliability & Fusion",
                score=50.0,
                confidence=0.30,
                weight=weight,
                weighted_score=round(50.0 * weight, 2),
                verification_status=TrustVerificationStatus.UNABLE_TO_VERIFY,
                evidence_count=0,
                evidence_ids=[],
                details={"reason": "Zero evidence items collected."},
            )

        # Deduplicate same-source evidence items based on content_hash or (source_url, claim)
        seen_keys = set()
        unique_evidence: List[NormalizedEvidence] = []
        for e in evidence_items:
            key = getattr(e, "content_hash", None) or f"{e.source_url}::{e.claim}"
            if key not in seen_keys:
                seen_keys.add(key)
                unique_evidence.append(e)

        evidence_ids = [str(e.id) for e in unique_evidence if hasattr(e, "id") and e.id]

        # Calculate weighted reliability score with tier weights and freshness decay
        reliability_accum = 0.0
        confidence_accum = 0.0
        total_weight_accum = 0.0

        for e in unique_evidence:
            s_type_val = getattr(e.source_type, "value", str(e.source_type))
            tier_weight = SOURCE_TIERS.get(s_type_val, 0.40)

            freshness = self._calculate_freshness_factor(
                published_at=getattr(e, "published_at", None),
                observed_at=getattr(e, "observed_at", None),
                source_type=s_type_val,
            )

            rel_score = float(getattr(e, "reliability_score", 0.70)) * 100.0
            conf_score = float(getattr(e, "confidence_score", 0.70))

            weighted_item_rel = rel_score * tier_weight * freshness
            weighted_item_conf = conf_score * tier_weight * freshness

            reliability_accum += weighted_item_rel
            confidence_accum += weighted_item_conf
            total_weight_accum += (tier_weight * freshness)

        avg_reliability = (reliability_accum / total_weight_accum) if total_weight_accum > 0 else 50.0
        avg_confidence = (confidence_accum / total_weight_accum) if total_weight_accum > 0 else 0.50

        # Multi-source independent corroboration bonus (up to +10.0 points)
        distinct_sources = len({e.source_url for e in unique_evidence if e.source_url})
        corroboration_bonus = min(10.0, max(0.0, (distinct_sources - 1) * 2.5))

        fused_score = min(100.0, max(0.0, avg_reliability + corroboration_bonus))
        fused_confidence = min(1.0, max(0.20, avg_confidence))

        status = TrustVerificationStatus.VERIFIED if fused_score >= 80.0 else (
            TrustVerificationStatus.PARTIALLY_VERIFIED if fused_score >= 60.0 else TrustVerificationStatus.UNABLE_TO_VERIFY
        )

        return DimensionScore(
            name="Evidence Reliability & Fusion",
            score=round(fused_score, 1),
            confidence=round(fused_confidence, 2),
            weight=weight,
            weighted_score=round(fused_score * weight, 2),
            verification_status=status,
            evidence_count=len(unique_evidence),
            evidence_ids=evidence_ids,
            details={
                "total_collected": len(evidence_items),
                "unique_deduplicated": len(unique_evidence),
                "distinct_sources": distinct_sources,
                "corroboration_bonus": corroboration_bonus,
            },
        )

    def calculate_risk_adjustment_dimension(
        self,
        evidence_items: List[NormalizedEvidence],
        target_name: str = "",
    ) -> DimensionScore:
        """
        Dimension 5: Risk Adjustment (15%)
        Evaluates risk signals while separating recruitment/job-offer scam risks from core company legitimacy penalties.
        Formula:
        legitimacy_penalty is bounded (0 to 50 points).
        recruitment_scam_risk is computed independently (0.0 to 1.0) and does NOT reduce company legitimacy score unless domain spoofing is detected.
        """
        weight = self.weights["risk"]
        risk_evidence = [
            e for e in evidence_items
            if "risk" in e.claim.lower()
            or "scam" in e.claim.lower()
            or "fee" in e.evidence_text.lower()
            or e.agent_name == "risk_analysis"
        ]

        evidence_ids = [str(e.id) for e in risk_evidence if hasattr(e, "id") and e.id]

        legitimacy_penalty = 0.0
        risk_factors: List[str] = []

        # Check company legitimacy risks (domain spoofing, fraudulent registration in evidence claims)
        for e in evidence_items:
            text_lower = f"{e.claim} {e.evidence_text}".lower()

            if "unverified domain spoofing" in text_lower or "fraudulent registration" in text_lower:
                legitimacy_penalty += 25.0
                risk_factors.append("Domain spoofing / identity mismatch risk")

            if "unauthorized contact information" in text_lower:
                legitimacy_penalty += 15.0
                risk_factors.append("Unauthorized contact channel risk")

        # Evaluate recruitment scam risk via RecruitmentClassifier
        from app.services.recruitment_classifier import RecruitmentClassifier
        recruitment_classifier = RecruitmentClassifier()

        recruitment_texts = [f"{e.claim} {e.evidence_text}" for e in evidence_items]
        combined_text = " ".join(recruitment_texts)

        # Extract potential email from evidence if present
        contact_email = ""
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', combined_text)
        if email_match:
            contact_email = email_match.group(0)

        evidence_sources = [
            {"source_type": getattr(e.source_type, "value", str(e.source_type))}
            for e in evidence_items
        ]

        recruitment_result = recruitment_classifier.evaluate(
            job_title=target_name or "",
            company_name=target_name or "",
            description=combined_text,
            contact_email=contact_email,
            evidence_sources=evidence_sources
        )

        recruitment_scam_risk = recruitment_result.score
        recruitment_risk_level = recruitment_result.risk_level

        for sig in recruitment_result.signals:
            if sig not in risk_factors:
                risk_factors.append(sig)

        # Decoupling rule: only apply legitimacy penalty if domain spoofing is explicitly detected
        if recruitment_result.domain_spoofing_detected and "Domain spoofing / identity mismatch detected" not in risk_factors:
            legitimacy_penalty += 25.0
            risk_factors.append("Domain spoofing / identity mismatch detected")

        legitimacy_penalty = min(50.0, max(0.0, legitimacy_penalty))
        risk_dimension_score = max(0.0, 100.0 - (legitimacy_penalty * 1.5))

        status = TrustVerificationStatus.VERIFIED if risk_dimension_score >= 80.0 else (
            TrustVerificationStatus.PARTIALLY_VERIFIED if risk_dimension_score >= 60.0 else TrustVerificationStatus.CONFLICTING
        )

        return DimensionScore(
            name="Risk Adjustment",
            score=round(risk_dimension_score, 1),
            confidence=recruitment_result.confidence,
            weight=weight,
            weighted_score=round(risk_dimension_score * weight, 2),
            verification_status=status,
            evidence_count=len(risk_evidence),
            evidence_ids=evidence_ids,
            details={
                "legitimacy_penalty": legitimacy_penalty,
                "recruitment_scam_risk": recruitment_scam_risk,
                "recruitment_risk_level": recruitment_risk_level,
                "recruitment_details": recruitment_result.model_dump() if hasattr(recruitment_result, "model_dump") else recruitment_result.dict(),
                "risk_factors": risk_factors,
            },
        )

    def evaluate_conflicts(self, evidence_items: List[NormalizedEvidence]) -> ConflictSummary:
        """
        Detects conflicting claim pairs across evidence items using NLI conflict detection.
        Categories: NO_CONFLICT, MINOR_CONFLICT, MAJOR_CONFLICT.
        Conflicts reduce confidence without automatically declaring fraud.
        """
        conflicting_items = [e for e in evidence_items if e.verification_status == VerificationStatus.CONFLICTING]
        conflict_details: List[Dict[str, Any]] = [
            {"claim": e.claim, "source": e.source_url, "evidence_id": str(e.id), "source_type": "status_conflicting"}
            for e in conflicting_items
        ]

        # Evaluate semantic NLI claim pair conflicts
        if len(evidence_items) >= 2:
            try:
                normalizer = ClaimNormalizer()
                nli_engine = NLIConflictEngine()
                claims = normalizer.normalize(evidence_items)
                nli_results = nli_engine.evaluate_evidence_claims(claims)

                for res in nli_results:
                    if res.label == NLILabel.CONTRADICTION:
                        conflict_details.append({
                            "claim": f"NLI Contradiction between evidence {res.premise_evidence_id[:8]} and {res.hypothesis_claim_id[:8]}",
                            "evidence_id": res.premise_evidence_id,
                            "hypothesis_id": res.hypothesis_claim_id,
                            "nli_label": res.label.value,
                            "confidence": res.confidence,
                            "confidence_label": res.confidence_label,
                            "model_name": res.model_name,
                            "implementation_type": res.implementation_type,
                        })
            except Exception as err:
                logger.warning(f"NLI conflict evaluation failed safely: {err}")

        conflict_count = len(conflict_details)

        if conflict_count == 0:
            return ConflictSummary(
                conflict_level=ConflictLevel.NO_CONFLICT,
                conflict_count=0,
                confidence_penalty=0.0,
                conflict_details=[],
            )
        elif conflict_count <= 2:
            return ConflictSummary(
                conflict_level=ConflictLevel.MINOR_CONFLICT,
                conflict_count=conflict_count,
                confidence_penalty=0.10,
                conflict_details=conflict_details,
            )
        else:
            return ConflictSummary(
                conflict_level=ConflictLevel.MAJOR_CONFLICT,
                conflict_count=conflict_count,
                confidence_penalty=0.25,
                conflict_details=conflict_details,
            )

    def compute_trust_index(
        self,
        evidence_items: List[NormalizedEvidence],
        target_name: str,
        target_domain: Optional[str] = None,
    ) -> TrustIndexResult:
        """
        Computes deterministic Trust Index grounded in normalized evidence data.
        Returns complete, explainable TrustIndexResult.
        """
        now_iso = datetime.now(timezone.utc).isoformat()

        # Calculate 5 independent dimensions
        dim_identity = self.calculate_entity_identity_dimension(evidence_items, target_name, target_domain)
        dim_tech = self.calculate_technical_provenance_dimension(evidence_items, target_domain)
        dim_reg = self.calculate_regulatory_dimension(evidence_items)
        dim_fusion = self.calculate_evidence_fusion_dimension(evidence_items)
        dim_risk = self.calculate_risk_adjustment_dimension(evidence_items, target_name)

        dimension_scores: Dict[str, DimensionScore] = {
            "identity": dim_identity,
            "technical_provenance": dim_tech,
            "regulatory": dim_reg,
            "evidence": dim_fusion,
            "risk": dim_risk,
        }

        # Weighted Base Trust Score calculation
        weighted_base = sum(d.weighted_score for d in dimension_scores.values())
        risk_details = dim_risk.details or {}
        legitimacy_penalty = float(risk_details.get("legitimacy_penalty", 0.0))

        raw_index = weighted_base - legitimacy_penalty
        trust_index = min(100.0, max(0.0, round(raw_index, 1)))

        # Conflict Evaluation & Confidence Penalties
        conflict_summary = self.evaluate_conflicts(evidence_items)
        weighted_confidence = sum(d.confidence * d.weight for d in dimension_scores.values())
        final_confidence = min(1.0, max(0.0, round(weighted_confidence - conflict_summary.confidence_penalty, 2)))

        # Overall Verification Status Determination
        if conflict_summary.conflict_level == ConflictLevel.MAJOR_CONFLICT:
            overall_status = TrustVerificationStatus.CONFLICTING
        elif dim_reg.verification_status == TrustVerificationStatus.VERIFIED and dim_identity.verification_status in (TrustVerificationStatus.VERIFIED, TrustVerificationStatus.PARTIALLY_VERIFIED):
            overall_status = TrustVerificationStatus.VERIFIED
        elif sum(1 for d in dimension_scores.values() if d.verification_status in (TrustVerificationStatus.VERIFIED, TrustVerificationStatus.PARTIALLY_VERIFIED)) >= 2:
            overall_status = TrustVerificationStatus.PARTIALLY_VERIFIED
        else:
            overall_status = TrustVerificationStatus.UNABLE_TO_VERIFY

        risk_level = "low" if trust_index >= 75.0 else ("medium" if trust_index >= 50.0 else ("high" if trust_index >= 30.0 else "critical"))

        # Traceable Evidence References
        references: List[Dict[str, Any]] = []
        for e in evidence_items[:15]:
            if hasattr(e, "source_url") and e.source_url:
                references.append({
                    "evidence_id": str(getattr(e, "id", "")),
                    "source_url": e.source_url,
                    "source_title": getattr(e, "source_title", "Evidence Record"),
                    "source_type": getattr(e.source_type, "value", str(e.source_type)),
                    "reliability_score": float(getattr(e, "reliability_score", 0.80)),
                    "verification_status": getattr(e.verification_status, "value", str(e.verification_status)),
                })

        explanation = (
            f"Vishleshan Trust Index computed at {trust_index}/100 ({risk_level.upper()} risk, "
            f"Confidence: {final_confidence * 100:.0f}%, Status: {overall_status.value.upper()}) using model {self.model_version}. "
            f"Evaluated across 5 dimensions: Entity Identity ({dim_identity.score}), Technical Provenance ({dim_tech.score}), "
            f"Regulatory Compliance ({dim_reg.score}), Evidence Fusion ({dim_fusion.score}), and Risk Adjustment ({dim_risk.score})."
        )

        risk_factors = risk_details.get("risk_factors", [])
        if not risk_factors:
            risk_explanation = (
                f"No elevated corporate risk signals detected. Risk score of {dim_risk.score}/100 indicates no configured penalties "
                f"were triggered by deterministic rules. Recruitment scam risk note: Deterministic rule-based assessment; ML classifier not yet active."
            )
        else:
            risk_explanation = (
                f"Identified {len(risk_factors)} risk signals: {', '.join(risk_factors)}. "
                f"Recruitment scam risk note: Deterministic rule-based assessment; ML classifier not yet active."
            )

        return TrustIndexResult(
            trust_index=trust_index,
            confidence=final_confidence,
            verification_status=overall_status,
            risk_level=risk_level,
            model_version=self.model_version,
            calculated_at=now_iso,
            computed_at=now_iso,
            updated_at=now_iso,
            dimension_scores=dimension_scores,
            risk_adjustment=RiskAdjustment(
                company_legitimacy_penalty=legitimacy_penalty,
                recruitment_scam_risk=float(risk_details.get("recruitment_scam_risk", 0.0)),
                recruitment_risk_level=str(risk_details.get("recruitment_risk_level", "low")),
                risk_factors=risk_factors,
                evidence_ids=dim_risk.evidence_ids,
                explanation=risk_explanation,
            ),
            conflict_summary=conflict_summary,
            explanation=explanation,
            evidence_references=references,
        )


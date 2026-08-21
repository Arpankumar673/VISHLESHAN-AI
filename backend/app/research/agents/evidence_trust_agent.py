from typing import Any, Dict, List, Optional, Union
from uuid import UUID
from app.core.logging import logger
from app.research.agents.base import (
    AgentInput,
    AgentResponse,
    AgentResult,
    AgentStatus,
    BaseAgent,
)
from app.research.deduplicator import EvidenceDeduplicator
from app.research.evidence.grouping import group_evidence
from app.research.evidence.scoring import score_fusion_result
from app.research.models import NormalizedEvidence
from app.research.normalizer import EvidenceNormalizer
from app.schemas.evidence import VerificationStatus


class EvidenceTrustAgent(BaseAgent):
    """
    Agent 7: Evidence & Trust Agent
    Responsible for:
    - Aggregating evidence across all specialized research agents
    - Enforcing SHA-256 content hash deduplication
    - Preserving exact evidence provenance and source reliability scores
    - Executing Evidence Fusion Engine (Phase 2A + 2B claim grouping, independence, conflict, scoring)
    - Computing preliminary trust scores and risk levels from deduplicated and fused evidence
    """

    def __init__(self):
        super().__init__(
            agent_name="evidence_trust",
            agent_description="Aggregates evidence across all agent branches, enforces SHA-256 deduplication, executes Evidence Fusion Engine, evaluates source diversity, and prepares structured findings for report building.",
            agent_version="1.0",
        )

    async def execute(
        self,
        input_data: Union[AgentInput, UUID, None] = None,
        company_id: Optional[UUID] = None,
        company_name: Optional[str] = None,
        domain: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> AgentResult:
        """
        Executes evidence aggregation, SHA-256 deduplication, Evidence Fusion Engine processing, and trust metric calculation.
        Supports both modern AgentInput and backward-compatible positional signatures.
        """
        # 1. Normalize input into AgentInput contract
        if isinstance(input_data, AgentInput):
            agent_input = input_data
        elif isinstance(input_data, dict):
            agent_input = AgentInput.model_validate(input_data)
        else:
            run_id = input_data or kwargs.get("research_run_id")
            c_id = company_id or kwargs.get("company_id")
            c_name = company_name or kwargs.get("company_name", "")
            c_url = domain or kwargs.get("company_url") or kwargs.get("domain")
            c_ctx = context or kwargs.get("context") or {}

            if not run_id or not c_id or not c_name:
                raise ValueError("Missing required fields for EvidenceTrustAgent: research_run_id, company_id, company_name")

            agent_input = AgentInput(
                research_run_id=run_id,
                company_id=c_id,
                company_name=c_name,
                company_url=c_url,
                context=c_ctx,
            )

        name = agent_input.company_name.strip()
        run_id = agent_input.research_run_id

        logger.info(f"[{self.agent_name}] Aggregating & deduplicating evidence for run {run_id}")

        raw_evidence_list: List[NormalizedEvidence] = []
        warnings: List[str] = []
        errors: List[str] = []

        # 2. Extract evidence contributed directly on AgentInput
        if agent_input.previous_evidence:
            raw_evidence_list.extend(agent_input.previous_evidence)

        # 3. Extract evidence contributed by prior parallel agents from context
        exec_ctx = agent_input.context or {}
        if "agent_responses" in exec_ctx:
            for resp in exec_ctx["agent_responses"]:
                try:
                    if isinstance(resp, (AgentResult, AgentResponse)):
                        raw_evidence_list.extend(resp.evidence)
                        warnings.extend(resp.warnings)
                        errors.extend(resp.errors)
                    elif isinstance(resp, dict) and "evidence" in resp:
                        for item in resp["evidence"]:
                            if isinstance(item, NormalizedEvidence):
                                raw_evidence_list.append(item)
                            elif isinstance(item, dict):
                                raw_evidence_list.append(NormalizedEvidence.model_validate(item))
                except Exception as ext_exc:
                    logger.warning(f"[{self.agent_name}] Error extracting evidence from agent response: {ext_exc}")
                    warnings.append(f"Could not parse evidence from agent response: {ext_exc}")

        # 4. Enforce SHA-256 Content Hash Deduplication
        unique_evidence = EvidenceDeduplicator.deduplicate(raw_evidence_list)

        # 5. Execute Evidence Fusion Engine (Phase 2A + Phase 2B)
        claim_groups = group_evidence(unique_evidence)
        fusion_result = score_fusion_result(claim_groups)

        if fusion_result.warnings:
            warnings.extend(fusion_result.warnings)

        avg_fused_confidence = (
            sum(fc.fused_confidence for fc in fusion_result.fused_claims) / len(fusion_result.fused_claims)
            if fusion_result.fused_claims
            else 0.5
        )

        # 6. Calculate Existing Trust & Reliability Metrics
        total_items = len(unique_evidence)
        verified_count = sum(1 for e in unique_evidence if e.verification_status == VerificationStatus.VERIFIED)
        avg_reliability = (
            sum(e.reliability_score for e in unique_evidence) / total_items
            if total_items > 0
            else 0.5
        )
        avg_confidence = (
            sum(e.confidence_score for e in unique_evidence) / total_items
            if total_items > 0
            else 0.5
        )
        trust_score_val = round(min(100.0, max(20.0, avg_reliability * 100.0)), 1)
        risk_level = "low" if trust_score_val >= 75.0 else ("medium" if trust_score_val >= 50.0 else "high")

        structured_findings = [
            {
                "category": "evidence_aggregation",
                "total_evidence_received": len(raw_evidence_list),
                "unique_evidence_count": total_items,
                "duplicates_removed": len(raw_evidence_list) - total_items,
                "verified_count": verified_count,
                "avg_reliability": round(avg_reliability, 2),
                "avg_confidence": round(avg_confidence, 2),
                "trust_score": trust_score_val,
                "risk_level": risk_level,
            },
            {
                "category": "evidence_fusion",
                "total_claim_groups": fusion_result.total_claim_groups,
                "conflicted_claims": fusion_result.conflicted_claims,
                "avg_fused_confidence": round(avg_fused_confidence, 2),
                "fused_claims": [fc.model_dump() for fc in fusion_result.fused_claims],
            },
        ]

        status = AgentStatus.COMPLETED.value if total_items > 0 else AgentStatus.PARTIAL.value
        if total_items == 0:
            warnings.append("No evidence items were provided for aggregation and trust scoring.")

        fused_trust_candidate = round(min(100.0, max(20.0, avg_fused_confidence * 100.0)), 1)

        return AgentResult(
            agent_name=self.agent_name,
            agent_version=self.agent_version,
            status=status,
            research_run_id=run_id,
            findings=structured_findings,
            evidence=unique_evidence,
            warnings=warnings,
            errors=errors,
            metadata={
                "company_name": name,
                "total_evidence": total_items,
                "raw_evidence_count": len(raw_evidence_list),
                "verified_count": verified_count,
                "avg_reliability": round(avg_reliability, 2),
                "preliminary_trust_score": trust_score_val,
                "preliminary_risk_level": risk_level,
                "overall_confidence": round(avg_confidence, 2),
                "findings_count": len(structured_findings),
                "evidence_count": len(unique_evidence),
                # Evidence Fusion Engine metadata integration
                "fusion_result": fusion_result.model_dump(),
                "total_claim_groups": fusion_result.total_claim_groups,
                "conflicted_claims": fusion_result.conflicted_claims,
                "avg_fused_confidence": round(avg_fused_confidence, 2),
                # Diagnostic candidate trust metric (non-authoritative)
                "fused_trust_candidate": fused_trust_candidate,
                "fused_trust_candidate_label": "diagnostic_experimental",
            },
        )

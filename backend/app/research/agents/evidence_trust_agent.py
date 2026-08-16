from typing import Any, Dict, List, Optional
from uuid import UUID
from app.core.logging import logger
from app.research.agents.base import AgentResponse, BaseAgent
from app.research.deduplicator import EvidenceDeduplicator
from app.research.models import NormalizedEvidence
from app.research.normalizer import EvidenceNormalizer
from app.schemas.evidence import VerificationStatus


class EvidenceTrustAgent(BaseAgent):
    """
    Agent 7: Evidence & Trust Agent
    Aggregates evidence across all agent branches, enforces SHA-256 deduplication,
    evaluates source diversity, and prepares structured findings for report building.
    """

    def __init__(self):
        super().__init__(agent_name="evidence_trust", agent_version="1.0")

    async def execute(
        self,
        research_run_id: UUID,
        company_id: UUID,
        company_name: str,
        domain: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> AgentResponse:
        logger.info(f"[{self.agent_name}] Aggregating & deduplicating evidence for run {research_run_id}")
        raw_evidence_list: List[NormalizedEvidence] = []
        warnings: List[str] = []
        errors: List[str] = []

        # Extract evidence contributed by prior parallel agents from context
        if context and "agent_responses" in context:
            for resp in context["agent_responses"]:
                if isinstance(resp, AgentResponse):
                    raw_evidence_list.extend(resp.evidence)
                    warnings.extend(resp.warnings)
                    errors.extend(resp.errors)
                elif isinstance(resp, dict) and "evidence" in resp:
                    for item in resp["evidence"]:
                        if isinstance(item, NormalizedEvidence):
                            raw_evidence_list.append(item)
                        elif isinstance(item, dict):
                            raw_evidence_list.append(NormalizedEvidence.model_validate(item))

        # Deduplicate on SHA-256 content hashes
        unique_evidence = EvidenceDeduplicator.deduplicate(raw_evidence_list)

        # Calculate preliminary metrics
        total_items = len(unique_evidence)
        verified_count = sum(1 for e in unique_evidence if e.verification_status == VerificationStatus.VERIFIED)
        avg_reliability = (
            sum(e.reliability_score for e in unique_evidence) / total_items
            if total_items > 0
            else 0.5
        )
        trust_score_val = round(min(100.0, max(20.0, avg_reliability * 100.0)), 1)
        risk_level = "low" if trust_score_val >= 75.0 else ("medium" if trust_score_val >= 50.0 else "high")

        return AgentResponse(
            agent_name=self.agent_name,
            agent_version=self.agent_version,
            status="completed" if total_items > 0 else "partial",
            research_run_id=research_run_id,
            evidence=unique_evidence,
            warnings=warnings,
            errors=errors,
            metadata={
                "total_evidence": total_items,
                "verified_count": verified_count,
                "avg_reliability": round(avg_reliability, 2),
                "preliminary_trust_score": trust_score_val,
                "preliminary_risk_level": risk_level,
            },
        )

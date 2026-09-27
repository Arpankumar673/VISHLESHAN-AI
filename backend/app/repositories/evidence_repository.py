from typing import Any, Dict, List, Optional
from uuid import UUID
from app.core.logging import logger
from app.integrations.supabase import get_supabase_client


class EvidenceRepository:
    def __init__(self):
        self.supabase = get_supabase_client()

    def get_by_id(self, evidence_id: UUID) -> Optional[Dict[str, Any]]:
        try:
            res = (
                self.supabase.table("evidence")
                .select("*")
                .eq("id", str(evidence_id))
                .maybe_single()
                .execute()
            )
            return res.data if res else None
        except Exception as exc:
            logger.error(f"EvidenceRepository.get_by_id failed: {exc}")
            return None

    def list_by_company_id(self, company_id: UUID) -> List[Dict[str, Any]]:
        try:
            res = (
                self.supabase.table("evidence")
                .select("*")
                .eq("company_id", str(company_id))
                .order("observed_at", desc=True)
                .execute()
            )
            return res.data if res and res.data else []
        except Exception as exc:
            logger.error(f"EvidenceRepository.list_by_company_id failed: {exc}")
            return []

    def list_by_research_run_id(self, research_run_id: UUID) -> List[Dict[str, Any]]:
        try:
            res = (
                self.supabase.table("evidence")
                .select("*")
                .eq("research_run_id", str(research_run_id))
                .order("observed_at", desc=True)
                .execute()
            )
            return res.data if res and res.data else []
        except Exception as exc:
            logger.error(f"EvidenceRepository.list_by_research_run_id failed: {exc}")
            return []

    def create(
        self,
        company_id: UUID,
        research_run_id: UUID,
        claim: str,
        evidence_text: str,
        source_url: str,
        source_title: Optional[str] = None,
        source_type: Any = "official_company",
        reliability_score: float = 0.8,
        confidence_score: float = 0.8,
        verification_status: Any = "verified",
        agent_name: str = "seed_agent",
        content_hash: Optional[str] = None,
        evidence_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        s_type = source_type.value if hasattr(source_type, "value") else str(source_type)
        v_status = verification_status.value if hasattr(verification_status, "value") else str(verification_status)
        payload = {
            "company_id": str(company_id),
            "research_run_id": str(research_run_id),
            "claim": claim,
            "evidence_text": evidence_text,
            "source_url": source_url if source_url else "https://hackindia.org/",
            "source_title": source_title,
            "source_type": s_type,
            "reliability_score": reliability_score,
            "confidence_score": confidence_score,
            "verification_status": v_status,
            "agent_name": agent_name,
            "content_hash": content_hash,
        }
        if evidence_id:
            payload["id"] = str(evidence_id)
        res = self.supabase.table("evidence").insert(payload).execute()
        if res.data and len(res.data) > 0:
            return res.data[0]
        raise RuntimeError("Failed to insert evidence record")


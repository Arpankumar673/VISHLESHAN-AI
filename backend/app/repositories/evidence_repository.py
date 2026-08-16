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

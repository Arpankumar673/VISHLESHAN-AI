from typing import Any, Dict, Optional
from uuid import UUID
from app.core.logging import logger
from app.integrations.supabase import get_supabase_client


class ReportRepository:
    def __init__(self):
        self.supabase = get_supabase_client()

    def get_by_id(self, report_id: UUID) -> Optional[Dict[str, Any]]:
        try:
            res = (
                self.supabase.table("reports")
                .select("*, companies(*), research_runs(*)")
                .eq("id", str(report_id))
                .maybe_single()
                .execute()
            )
            return res.data if res else None
        except Exception as exc:
            logger.error(f"ReportRepository.get_by_id failed: {exc}")
            return None

    def get_by_research_run_id(self, run_id: UUID) -> Optional[Dict[str, Any]]:
        try:
            res = (
                self.supabase.table("reports")
                .select("*, companies(*), research_runs(*)")
                .eq("research_run_id", str(run_id))
                .maybe_single()
                .execute()
            )
            return res.data if res else None
        except Exception as exc:
            logger.error(f"ReportRepository.get_by_research_run_id failed: {exc}")
            return None

    def create(
        self,
        company_id: UUID,
        research_run_id: UUID,
        title: str,
        content: Dict[str, Any],
        report_version: str = "1.0",
    ) -> Dict[str, Any]:
        payload = {
            "company_id": str(company_id),
            "research_run_id": str(research_run_id),
            "title": title,
            "content": content,
            "report_version": report_version,
        }
        res = self.supabase.table("reports").insert(payload).execute()
        if res.data and len(res.data) > 0:
            return res.data[0]
        raise RuntimeError("Failed to insert report record")

from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID
from app.core.logging import logger
from app.integrations.supabase import get_supabase_client


class ResearchRepository:
    def __init__(self):
        self.supabase = get_supabase_client()

    def create(self, user_id: UUID, company_id: UUID, status: str = "queued") -> Dict[str, Any]:
        payload = {
            "user_id": str(user_id),
            "company_id": str(company_id),
            "status": status,
        }
        res = self.supabase.table("research_runs").insert(payload).execute()
        if res.data and len(res.data) > 0:
            return res.data[0]
        raise RuntimeError("Failed to insert research run record")

    def get_by_id(self, run_id: UUID) -> Optional[Dict[str, Any]]:
        try:
            res = (
                self.supabase.table("research_runs")
                .select("*, companies(*), trust_scores(*)")
                .eq("id", str(run_id))
                .maybe_single()
                .execute()
            )
            return res.data if res else None
        except Exception as exc:
            logger.error(f"ResearchRepository.get_by_id failed: {exc}")
            return None

    def update_status(
        self,
        run_id: UUID,
        status: str,
        error_message: Optional[str] = None,
        started_at: Optional[str] = None,
        completed_at: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        payload: Dict[str, Any] = {"status": status}
        if error_message is not None:
            payload["error_message"] = error_message
        if started_at is not None:
            payload["started_at"] = started_at
        if completed_at is not None:
            payload["completed_at"] = completed_at

        try:
            res = (
                self.supabase.table("research_runs")
                .update(payload)
                .eq("id", str(run_id))
                .execute()
            )
            return res.data[0] if res.data and len(res.data) > 0 else None
        except Exception as exc:
            logger.error(f"ResearchRepository.update_status failed: {exc}")
            return None

    def list_by_user(
        self,
        user_id: UUID,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Dict[str, Any]], int]:
        try:
            query = (
                self.supabase.table("research_runs")
                .select("*, companies(*), trust_scores(*)", count="exact")
                .eq("user_id", str(user_id))
            )

            if status:
                query = query.eq("status", status)

            offset = (page - 1) * page_size
            res = (
                query.order("created_at", desc=True)
                .range(offset, offset + page_size - 1)
                .execute()
            )

            items = res.data if res and res.data else []
            total = res.count if res and res.count is not None else len(items)
            return items, total
        except Exception as exc:
            logger.error(f"ResearchRepository.list_by_user failed: {exc}")
            return [], 0

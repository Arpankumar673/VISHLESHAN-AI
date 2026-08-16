from typing import Any, Dict, List, Optional
from uuid import UUID
from app.core.logging import logger
from app.integrations.supabase import get_supabase_client


class CompanyRepository:
    def __init__(self):
        self.supabase = get_supabase_client()

    def get_by_id(self, company_id: UUID) -> Optional[Dict[str, Any]]:
        try:
            res = (
                self.supabase.table("companies")
                .select("*, company_identifiers(*)")
                .eq("id", str(company_id))
                .maybe_single()
                .execute()
            )
            return res.data if res else None
        except Exception as exc:
            logger.error(f"CompanyRepository.get_by_id failed: {exc}")
            return None

    def get_by_normalized_name(self, normalized_name: str) -> Optional[Dict[str, Any]]:
        try:
            res = (
                self.supabase.table("companies")
                .select("*")
                .eq("normalized_name", normalized_name)
                .maybe_single()
                .execute()
            )
            return res.data if res else None
        except Exception as exc:
            logger.error(f"CompanyRepository.get_by_normalized_name failed: {exc}")
            return None

    def create(
        self,
        name: str,
        normalized_name: str,
        official_domain: Optional[str] = None,
        description: Optional[str] = None,
        industry: Optional[str] = None,
        headquarters: Optional[str] = None,
    ) -> Dict[str, Any]:
        payload = {
            "name": name,
            "normalized_name": normalized_name,
            "official_domain": official_domain,
            "description": description,
            "industry": industry,
            "headquarters": headquarters,
        }
        res = self.supabase.table("companies").insert(payload).execute()
        if res.data and len(res.data) > 0:
            return res.data[0]
        raise RuntimeError("Failed to insert company record")

    def get_evidence(self, company_id: UUID) -> List[Dict[str, Any]]:
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
            logger.error(f"CompanyRepository.get_evidence failed: {exc}")
            return []

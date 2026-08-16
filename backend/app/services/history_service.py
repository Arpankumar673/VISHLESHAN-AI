import math
from typing import Optional
from uuid import UUID
from app.repositories.history_repository import HistoryRepository
from app.schemas.common import PaginatedData
from app.schemas.company import CompanyResponse
from app.schemas.research import ResearchRunResponse, ResearchStatus
from app.schemas.trust import TrustScoreResponse


class HistoryService:
    def __init__(self, history_repo: Optional[HistoryRepository] = None):
        self.history_repo = history_repo or HistoryRepository()

    def get_history(
        self,
        user_id: UUID,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedData[ResearchRunResponse]:
        items, total = self.history_repo.get_user_history(
            user_id=user_id,
            status=status,
            page=page,
            page_size=page_size,
        )

        response_items = []
        for run_data in items:
            company_dict = run_data.get("companies")
            company_model = CompanyResponse.model_validate(company_dict) if company_dict else None

            trust_dict = run_data.get("trust_scores")
            trust_model = None
            if trust_dict:
                if isinstance(trust_dict, list) and len(trust_dict) > 0:
                    trust_model = TrustScoreResponse.model_validate(trust_dict[0])
                elif isinstance(trust_dict, dict):
                    trust_model = TrustScoreResponse.model_validate(trust_dict)

            response_items.append(
                ResearchRunResponse(
                    research_run_id=UUID(run_data["id"]),
                    company_id=UUID(run_data["company_id"]),
                    user_id=UUID(run_data["user_id"]) if run_data.get("user_id") else None,
                    status=ResearchStatus(run_data["status"]),
                    started_at=run_data.get("started_at"),
                    completed_at=run_data.get("completed_at"),
                    error_message=run_data.get("error_message"),
                    created_at=run_data["created_at"],
                    updated_at=run_data["updated_at"],
                    company=company_model,
                    trust_score=trust_model,
                )
            )

        total_pages = math.ceil(total / page_size) if total > 0 else 1

        return PaginatedData(
            items=response_items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )


def get_history_service() -> HistoryService:
    return HistoryService()

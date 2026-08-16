from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID
from app.repositories.research_repository import ResearchRepository


class HistoryRepository:
    def __init__(self, research_repository: Optional[ResearchRepository] = None):
        self.research_repo = research_repository or ResearchRepository()

    def get_user_history(
        self,
        user_id: UUID,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Dict[str, Any]], int]:
        return self.research_repo.list_by_user(
            user_id=user_id,
            status=status,
            page=page,
            page_size=page_size,
        )

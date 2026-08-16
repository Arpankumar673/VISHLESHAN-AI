from typing import Optional
from fastapi import APIRouter, Depends, Query
from app.core.security import AuthenticatedUser, get_current_user
from app.schemas.common import ApiResponse, PaginatedData
from app.schemas.research import ResearchRunResponse, ResearchStatus
from app.services.history_service import HistoryService, get_history_service

router = APIRouter(prefix="/history", tags=["History"])


@router.get(
    "",
    response_model=ApiResponse[PaginatedData[ResearchRunResponse]],
    summary="Get User Research Run Audit History",
    description="Retrieve paginated history of past company intelligence runs initiated by the authenticated user.",
)
async def get_history(
    page: int = Query(default=1, ge=1, description="Page index"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    status: Optional[ResearchStatus] = Query(default=None, description="Optional status filter"),
    current_user: AuthenticatedUser = Depends(get_current_user),
    history_service: HistoryService = Depends(get_history_service),
) -> ApiResponse[PaginatedData[ResearchRunResponse]]:
    paginated_result = history_service.get_history(
        user_id=current_user.id,
        status=status.value if status else None,
        page=page,
        page_size=page_size,
    )
    return ApiResponse(data=paginated_result)

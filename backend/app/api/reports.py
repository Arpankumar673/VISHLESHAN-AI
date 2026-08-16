from uuid import UUID
from fastapi import APIRouter, Depends
from app.core.security import AuthenticatedUser, get_current_user
from app.schemas.common import ApiResponse
from app.schemas.report import ReportResponse
from app.services.report_service import ReportService, get_report_service

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get(
    "/{report_id}",
    response_model=ApiResponse[ReportResponse],
    summary="Get Company Intelligence Report",
    description="Retrieve a complete 13-section Company Intelligence Report for an authorized user.",
)
async def get_report(
    report_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    report_service: ReportService = Depends(get_report_service),
) -> ApiResponse[ReportResponse]:
    report = report_service.get_report(
        report_id=report_id,
        user_id=current_user.id,
    )
    return ApiResponse(data=report)

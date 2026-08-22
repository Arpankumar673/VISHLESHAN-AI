from uuid import UUID
from fastapi import APIRouter, Depends
from app.core.security import AuthenticatedUser, get_current_user
from app.schemas.common import ApiResponse
from app.schemas.report import ReportResponse
from app.services.report_export_service import ReportExportService
from app.services.report_service import ReportService, get_report_service

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get(
    "/{report_id}",
    response_model=ApiResponse[ReportResponse],
    summary="Get Company Intelligence Report",
    description="Retrieve a complete Company Intelligence Report for an authorized user.",
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


@router.get(
    "/{report_id}/export/csv",
    summary="Export Report as Atomic Claims/Evidence CSV Dataset",
    description="Generates an RFC 4180 compliant CSV stream containing one row per atomic claim/evidence record with complete provenance.",
)
async def export_report_csv(
    report_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    from fastapi.responses import Response

    export_service = ReportExportService()
    csv_content = export_service.generate_report_csv(report_id=report_id, user_id=current_user.id)

    return Response(
        content=csv_content.encode("utf-8"),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="vishleshan_report_{report_id}.csv"'
        },
    )


@router.get(
    "/{report_id}/export/json",
    summary="Export Report as Hierarchical JSON",
    description="Returns the full hierarchical report object in machine-readable JSON format.",
)
async def export_report_json(
    report_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    report_service: ReportService = Depends(get_report_service),
) -> ApiResponse[ReportResponse]:
    report = report_service.get_report(
        report_id=report_id,
        user_id=current_user.id,
    )
    return ApiResponse(data=report)

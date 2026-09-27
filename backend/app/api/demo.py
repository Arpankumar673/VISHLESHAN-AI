from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from app.core.logging import logger
from app.schemas.common import ApiResponse
from app.services.gemini_live_service import GeminiLiveService, get_gemini_live_service

router = APIRouter(prefix="/demo", tags=["Presentation Mode"])


class DemoCompanyReportRequest(BaseModel):
    company_name: str = Field(..., description="Target company or organization name")
    official_url: Optional[str] = Field(None, description="Optional official website or domain URL")


@router.post(
    "/company-report",
    response_model=ApiResponse[Dict[str, Any]],
    status_code=status.HTTP_200_OK,
    summary="Generate Live Gemini Company Intelligence Report",
    description="Emergency Presentation Mode: Calls Gemini API to generate structured company intelligence for any enterprise.",
)
async def generate_demo_company_report(
    payload: DemoCompanyReportRequest,
    live_service: GeminiLiveService = Depends(get_gemini_live_service),
) -> ApiResponse[Dict[str, Any]]:
    company_name = payload.company_name.strip() if payload.company_name else ""
    if not company_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please enter a valid company name.",
        )

    try:
        result = await live_service.generate_company_report(
            company_name=company_name,
            official_url=payload.official_url,
        )
        return ApiResponse(data=result)
    except ValueError as val_err:
        logger.warning(f"[DemoAPI] Validation/Integrity rejection for '{company_name}': {val_err}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(val_err),
        )
    except RuntimeError as run_err:
        err_msg = str(run_err)
        logger.error(f"[DemoAPI] Live Gemini failure for '{company_name}': {err_msg}")
        if "not configured" in err_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Gemini API key is not configured in backend environment. Please verify Render environment variables.",
            )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Gemini API temporarily unavailable. Please retry.",
        )
    except Exception as exc:
        logger.exception(f"[DemoAPI] Unexpected error in presentation report for '{company_name}': {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AI report generation failed. Please retry.",
        )


@router.get(
    "/reports/{report_id}",
    response_model=ApiResponse[Dict[str, Any]],
    summary="Get Presentation Mode Report by ID",
    description="Retrieve cached presentation intelligence report for seamless client-side page reload.",
)
async def get_demo_report(
    report_id: str,
    live_service: GeminiLiveService = Depends(get_gemini_live_service),
) -> ApiResponse[Dict[str, Any]]:
    report = live_service.get_report_by_id(report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Presentation report not found or expired from session cache.",
        )
    return ApiResponse(data=report)

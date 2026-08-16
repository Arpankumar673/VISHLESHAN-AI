from typing import Any, Dict, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Header, HTTPException, status
from app.core.config import settings
from app.core.logging import logger
from app.core.security import AuthenticatedUser, get_current_user
from app.schemas.common import ApiResponse
from app.schemas.research import (
    ResearchRunResponse,
    StartResearchRequest,
    StartResearchResponse,
)
from app.services.research_service import ResearchService, get_research_service

router = APIRouter(prefix="/research", tags=["Research"])


@router.post(
    "",
    response_model=ApiResponse[StartResearchResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Initiate Company Research Run",
    description="Queue an asynchronous research run for a target company under the authenticated user.",
)
async def start_research(
    payload: StartResearchRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    research_service: ResearchService = Depends(get_research_service),
) -> ApiResponse[StartResearchResponse]:
    response = research_service.start_research(
        user_id=current_user.id,
        company_name=payload.company_name,
        company_url=payload.company_url,
    )
    return ApiResponse(data=response)


@router.get(
    "/{research_run_id}",
    response_model=ApiResponse[ResearchRunResponse],
    summary="Get Research Run Execution Status",
    description="Retrieve execution state, timestamps, and current step results for a specific research run.",
)
async def get_research_status(
    research_run_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    research_service: ResearchService = Depends(get_research_service),
) -> ApiResponse[ResearchRunResponse]:
    response = research_service.get_research_status(
        run_id=research_run_id,
        user_id=current_user.id,
    )
    return ApiResponse(data=response)


@router.post(
    "/callback",
    response_model=ApiResponse[Dict[str, Any]],
    summary="n8n Orchestration Webhook Callback",
    description="Secure endpoint receiving asynchronous agent results from authenticated n8n workflow.",
)
async def n8n_callback(
    payload: Dict[str, Any],
    x_vishleshan_webhook_secret: Optional[str] = Header(None, alias="X-Vishleshan-Webhook-Secret"),
    research_service: ResearchService = Depends(get_research_service),
) -> ApiResponse[Dict[str, Any]]:
    # Enforce webhook secret authentication
    if not x_vishleshan_webhook_secret or x_vishleshan_webhook_secret != settings.N8N_WEBHOOK_SECRET:
        logger.warning("Unauthorized n8n callback attempt: invalid or missing webhook secret header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-Vishleshan-Webhook-Secret header",
        )

    logger.info(f"Received authenticated callback from n8n for run: {payload.get('research_run_id')}")
    result = await research_service.handle_n8n_callback(payload)
    return ApiResponse(data=result)

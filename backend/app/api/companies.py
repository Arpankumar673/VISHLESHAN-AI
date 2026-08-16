from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends
from app.core.security import AuthenticatedUser, get_current_user
from app.schemas.common import ApiResponse
from app.schemas.company import CompanyResponse
from app.schemas.evidence import EvidenceResponse
from app.services.company_service import CompanyService, get_company_service

router = APIRouter(prefix="/companies", tags=["Companies"])


@router.get(
    "/{company_id}",
    response_model=ApiResponse[CompanyResponse],
    summary="Get Company Intelligence Record",
    description="Retrieve canonical company metadata and registered corporate identifiers.",
)
async def get_company(
    company_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    company_service: CompanyService = Depends(get_company_service),
) -> ApiResponse[CompanyResponse]:
    company = company_service.get_company(company_id)
    return ApiResponse(data=company)


@router.get(
    "/{company_id}/evidence",
    response_model=ApiResponse[List[EvidenceResponse]],
    summary="List Evidence for Company",
    description="Retrieve all observed forensic evidence records linked to this company.",
)
async def get_company_evidence(
    company_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    company_service: CompanyService = Depends(get_company_service),
) -> ApiResponse[List[EvidenceResponse]]:
    evidence = company_service.get_company_evidence(company_id)
    return ApiResponse(data=evidence)

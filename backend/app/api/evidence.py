from uuid import UUID
from fastapi import APIRouter, Depends
from app.core.security import AuthenticatedUser, get_current_user
from app.schemas.common import ApiResponse
from app.schemas.evidence import EvidenceResponse
from app.services.evidence_service import EvidenceService, get_evidence_service

router = APIRouter(prefix="/evidence", tags=["Evidence"])


@router.get(
    "/{evidence_id}",
    response_model=ApiResponse[EvidenceResponse],
    summary="Get Specific Evidence Item",
    description="Retrieve a single forensic evidence record and its cryptographic provenance details.",
)
async def get_evidence(
    evidence_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    evidence_service: EvidenceService = Depends(get_evidence_service),
) -> ApiResponse[EvidenceResponse]:
    evidence = evidence_service.get_evidence_by_id(evidence_id)
    return ApiResponse(data=evidence)

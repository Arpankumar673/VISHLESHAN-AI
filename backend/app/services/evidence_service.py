from typing import List, Optional
from uuid import UUID
from app.core.errors import NotFoundError
from app.repositories.evidence_repository import EvidenceRepository
from app.schemas.evidence import EvidenceResponse


class EvidenceService:
    def __init__(self, evidence_repo: Optional[EvidenceRepository] = None):
        self.evidence_repo = evidence_repo or EvidenceRepository()

    def get_evidence_by_id(self, evidence_id: UUID) -> EvidenceResponse:
        data = self.evidence_repo.get_by_id(evidence_id)
        if not data:
            raise NotFoundError(f"Evidence record with ID {evidence_id} not found")
        return EvidenceResponse.model_validate(data)

    def get_evidence_by_company(self, company_id: UUID) -> List[EvidenceResponse]:
        items = self.evidence_repo.list_by_company_id(company_id)
        return [EvidenceResponse.model_validate(item) for item in items]


def get_evidence_service() -> EvidenceService:
    return EvidenceService()

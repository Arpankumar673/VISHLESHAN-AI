from typing import List, Optional
from uuid import UUID
from app.core.errors import NotFoundError
from app.repositories.company_repository import CompanyRepository
from app.schemas.company import CompanyResponse
from app.schemas.evidence import EvidenceResponse


class CompanyService:
    def __init__(self, company_repo: Optional[CompanyRepository] = None):
        self.company_repo = company_repo or CompanyRepository()

    def get_company(self, company_id: UUID) -> CompanyResponse:
        company_data = self.company_repo.get_by_id(company_id)
        if not company_data:
            raise NotFoundError(f"Company with ID {company_id} not found")
        return CompanyResponse.model_validate(company_data)

    def get_company_evidence(self, company_id: UUID) -> List[EvidenceResponse]:
        # Verify company exists first
        self.get_company(company_id)
        evidence_list = self.company_repo.get_evidence(company_id)
        return [EvidenceResponse.model_validate(e) for e in evidence_list]

    def resolve_or_create(self, name: str, official_domain: Optional[str] = None) -> CompanyResponse:
        normalized = name.strip().lower()
        existing = self.company_repo.get_by_normalized_name(normalized)
        if existing:
            return CompanyResponse.model_validate(existing)

        created = self.company_repo.create(
            name=name.strip(),
            normalized_name=normalized,
            official_domain=official_domain.strip().lower() if official_domain else None,
        )
        return CompanyResponse.model_validate(created)


def get_company_service() -> CompanyService:
    return CompanyService()

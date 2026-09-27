from typing import Optional
from uuid import UUID
from app.core.errors import AuthorizationError, NotFoundError
from app.repositories.report_repository import ReportRepository
from app.schemas.company import CompanyResponse
from app.schemas.report import ReportResponse


class ReportService:
    def __init__(self, report_repo: Optional[ReportRepository] = None):
        self.report_repo = report_repo or ReportRepository()

    def get_report(self, report_id: UUID, user_id: UUID) -> ReportResponse:
        report_data = self.report_repo.get_by_id(report_id)
        if not report_data:
            # Fallback: Check if report_id was provided as a research_run_id
            report_data = self.report_repo.get_by_research_run_id(report_id)

        if not report_data:
            raise NotFoundError(f"Report with ID {report_id} not found")

        # Verify ownership through the associated research run
        run_data = report_data.get("research_runs")
        if run_data and run_data.get("user_id"):
            if run_data["user_id"] != str(user_id):
                raise AuthorizationError("You do not have access to this intelligence report")

        company_dict = report_data.get("companies")
        company_model = CompanyResponse.model_validate(company_dict) if company_dict else None

        content_dict = report_data.get("content", {})
        ts_dict = content_dict.get("trust_score") or content_dict.get("trust_index_details") or {}
        
        trust_score_model = None
        if ts_dict:
            try:
                from app.schemas.trust import TrustScoreResponse
                # Normalize keys for TrustScoreResponse schema
                payload = {
                    "score": ts_dict.get("score", ts_dict.get("trust_index")),
                    "trust_index": ts_dict.get("trust_index", ts_dict.get("score")),
                    "confidence": ts_dict.get("confidence"),
                    "risk_level": ts_dict.get("risk_level", "low"),
                    "verification_status": ts_dict.get("verification_status", "unable_to_verify"),
                    "evidence_coverage": ts_dict.get("evidence_coverage", 1.0),
                    "algorithm_version": ts_dict.get("algorithm_version", "v1"),
                    "explanation": ts_dict.get("explanation"),
                    "computed_at": ts_dict.get("computed_at"),
                    "updated_at": ts_dict.get("updated_at"),
                    "dimension_scores": ts_dict.get("dimension_scores"),
                    "risk_adjustment": ts_dict.get("risk_adjustment"),
                    "conflict_summary": ts_dict.get("conflict_summary"),
                    "evidence_references": ts_dict.get("evidence_references"),
                }
                trust_score_model = TrustScoreResponse.model_validate(payload)
            except Exception as ts_err:
                logger.warning(f"Could not parse trust_score in ReportResponse: {ts_err}")

        return ReportResponse(
            id=UUID(report_data["id"]),
            company_id=UUID(report_data["company_id"]),
            research_run_id=UUID(report_data["research_run_id"]),
            title=report_data["title"],
            content=content_dict,
            report_version=report_data.get("report_version", "1.0"),
            created_at=report_data["created_at"],
            updated_at=report_data["updated_at"],
            company=company_model,
            trust_score=trust_score_model,
        )



def get_report_service() -> ReportService:
    return ReportService()

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4
from app.core.errors import AuthorizationError, NotFoundError
from app.core.logging import logger
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
            # Self-healing recovery: Check if report_id matches a research_run_id in research_runs table
            from app.repositories.research_repository import ResearchRepository
            run_data = ResearchRepository().get_by_id(report_id)
            if run_data:
                status = run_data.get("status")
                if status in ("queued", "running"):
                    raise NotFoundError(
                        f"Research run {report_id} is currently executing ({status}). Intelligence report will be available upon completion."
                    )

                # Recover or build report on-the-fly from stored evidence & company data
                company_dict = run_data.get("companies") or {}
                company_name = company_dict.get("name", "Target Organization")
                company_domain = company_dict.get("official_domain")
                company_id = UUID(run_data["company_id"])

                from app.integrations.supabase import get_supabase_client
                from app.models.evidence import NormalizedEvidence
                from app.research.models import IdentityResult
                from app.research.report_builder import ReportBuilder

                supabase = get_supabase_client()
                try:
                    ev_res = (
                        supabase.table("evidence")
                        .select("*")
                        .eq("research_run_id", str(report_id))
                        .execute()
                    )
                    raw_ev = ev_res.data if ev_res and ev_res.data else []
                except Exception as ev_err:
                    logger.warning(f"Could not fetch evidence for recovery: {ev_err}")
                    raw_ev = []

                evidence_items = []
                for ev in raw_ev:
                    try:
                        evidence_items.append(
                            NormalizedEvidence(
                                id=UUID(ev["id"]) if "id" in ev and ev["id"] else uuid4(),
                                research_run_id=UUID(ev["research_run_id"]),
                                company_id=UUID(ev["company_id"]),
                                claim=ev.get("claim", ""),
                                evidence_text=ev.get("evidence_text", ""),
                                source_url=ev.get("source_url", ""),
                                source_title=ev.get("source_title", ""),
                                source_type=ev.get("source_type", "web_search"),
                                reliability_score=float(ev.get("reliability_score", 0.8)),
                                confidence_score=float(ev.get("confidence_score", 0.8)),
                                verification_status=ev.get("verification_status", "corroborated"),
                                agent_name=ev.get("agent_name", "unknown"),
                                content_hash=ev.get("content_hash", ""),
                            )
                        )
                    except Exception:
                        pass

                identity = IdentityResult(
                    canonical_name=company_name,
                    official_domain=company_domain,
                    description=company_dict.get("description", ""),
                    industry=company_dict.get("industry", ""),
                    headquarters=company_dict.get("headquarters", ""),
                )

                recovered_content = ReportBuilder.build_report_content(identity, evidence_items)
                report_title = f"Company Intelligence Report — {company_name}"

                try:
                    report_data = self.report_repo.create(
                        company_id=company_id,
                        research_run_id=report_id,
                        title=report_title,
                        content=recovered_content,
                    )
                except Exception as create_exc:
                    logger.warning(f"Could not persist recovered report to DB: {create_exc}")
                    now_str = datetime.now(timezone.utc).isoformat()
                    report_data = {
                        "id": str(report_id),
                        "company_id": str(company_id),
                        "research_run_id": str(report_id),
                        "title": report_title,
                        "content": recovered_content,
                        "report_version": "1.0",
                        "created_at": run_data.get("created_at", now_str),
                        "updated_at": now_str,
                        "companies": company_dict,
                        "research_runs": run_data,
                    }

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

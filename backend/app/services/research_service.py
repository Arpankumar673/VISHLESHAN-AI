import asyncio
from typing import Any, Dict, Optional
from uuid import UUID
from app.core.config import settings
from app.core.errors import AuthorizationError, NotFoundError
from app.core.logging import logger
from app.repositories.research_repository import ResearchRepository
from app.research.agents.orchestrator import MultiAgentOrchestrator
from app.research.engine import ResearchEngine
from app.schemas.company import CompanyResponse
from app.schemas.research import (
    ResearchRunResponse,
    ResearchStatus,
    StartResearchResponse,
)
from app.schemas.trust import TrustScoreResponse
from app.services.company_service import CompanyService


class ResearchService:
    def __init__(
        self,
        research_repo: Optional[ResearchRepository] = None,
        company_service: Optional[CompanyService] = None,
        multi_agent_orchestrator: Optional[MultiAgentOrchestrator] = None,
        fallback_engine: Optional[ResearchEngine] = None,
    ):
        self.research_repo = research_repo or ResearchRepository()
        self.company_service = company_service or CompanyService()
        self.orchestrator = multi_agent_orchestrator or MultiAgentOrchestrator()
        self.fallback_engine = fallback_engine or ResearchEngine()

    def start_research(
        self,
        user_id: UUID,
        company_name: str,
        company_url: Optional[str] = None,
    ) -> StartResearchResponse:
        company = self.company_service.resolve_or_create(
            name=company_name,
            official_domain=company_url,
        )

        run_data = self.research_repo.create(
            user_id=user_id,
            company_id=company.id,
            status=ResearchStatus.QUEUED.value,
        )

        run_id = UUID(run_data["id"])

        # Asynchronously trigger research pipeline
        asyncio.create_task(
            self._dispatch_research_run(
                research_run_id=run_id,
                company_id=company.id,
                company_name=company_name,
                company_url=company_url,
            )
        )

        return StartResearchResponse(
            research_run_id=run_id,
            company_id=company.id,
            status=ResearchStatus.QUEUED,
        )

    async def _dispatch_research_run(
        self,
        research_run_id: UUID,
        company_id: UUID,
        company_name: str,
        company_url: Optional[str] = None,
    ):
        orchestrator_mode = settings.RESEARCH_ORCHESTRATOR_MODE.lower()

        if orchestrator_mode == "langgraph":
            logger.info(f"Executing research run {research_run_id} via LangGraph orchestration engine...")
            try:
                await self.orchestrator.execute_langgraph_run(
                    research_run_id=research_run_id,
                    company_id=company_id,
                    company_name=company_name,
                    company_url=company_url,
                )
                return
            except Exception as lg_exc:
                logger.error(f"LangGraph execution failed for run {research_run_id}: {lg_exc}. Falling back to standard orchestrator...")

        # Local multi-agent execution (or fallback if langgraph was unavailable)
        try:
            await self.orchestrator.execute_run(
                research_run_id=research_run_id,
                company_id=company_id,
                company_name=company_name,
                company_url=company_url,
            )
        except Exception as exc:
            logger.error(
                f"MultiAgentOrchestrator failed for run {research_run_id}: {exc}. Invoking fallback engine..."
            )
            try:
                await self.fallback_engine.run(
                    research_run_id=research_run_id,
                    company_id=company_id,
                    company_name=company_name,
                    company_url=company_url,
                )
            except Exception as fatal_exc:
                logger.exception(f"Fatal failure in fallback engine for run {research_run_id}: {fatal_exc}")

    def get_research_status(self, run_id: UUID, user_id: UUID) -> ResearchRunResponse:
        run_data = self.research_repo.get_by_id(run_id)
        if not run_data:
            raise NotFoundError(f"Research run with ID {run_id} not found")

        if run_data.get("user_id") and run_data["user_id"] != str(user_id):
            raise AuthorizationError("You do not have access to this research run")

        company_dict = run_data.get("companies")
        company_model = CompanyResponse.model_validate(company_dict) if company_dict else None

        trust_dict = run_data.get("trust_scores")
        trust_model = None
        if trust_dict:
            if isinstance(trust_dict, list) and len(trust_dict) > 0:
                trust_model = TrustScoreResponse.model_validate(trust_dict[0])
            elif isinstance(trust_dict, dict):
                trust_model = TrustScoreResponse.model_validate(trust_dict)

        # Check if an associated report exists for this run
        report_id = None
        try:
            from app.repositories.report_repository import ReportRepository
            report_data = ReportRepository().get_by_research_run_id(run_id)
            if report_data and "id" in report_data:
                report_id = UUID(report_data["id"])
        except Exception:
            pass

        return ResearchRunResponse(
            research_run_id=UUID(run_data["id"]),
            company_id=UUID(run_data["company_id"]),
            user_id=UUID(run_data["user_id"]) if run_data.get("user_id") else None,
            status=ResearchStatus(run_data["status"]),
            started_at=run_data.get("started_at"),
            completed_at=run_data.get("completed_at"),
            error_message=run_data.get("error_message"),
            created_at=run_data["created_at"],
            updated_at=run_data["updated_at"],
            company=company_model,
            trust_score=trust_model,
            report_id=report_id,
        )


def get_research_service() -> ResearchService:
    return ResearchService()

from typing import Any, Dict, List, Optional
from uuid import UUID
from app.core.logging import logger
from app.research.agents.base import AgentResponse, BaseAgent
from app.research.identity import IdentityResolver
from app.research.models import IdentityResult, NormalizedEvidence
from app.research.report_builder import ReportBuilder


class ReportAgent(BaseAgent):
    """
    Agent 8: Report Agent
    Assembles structured 13-section Company Intelligence Report from verified evidence items.
    Ensures every assertion is grounded in traceable, hashed evidence.
    """

    def __init__(self, identity_resolver: Optional[IdentityResolver] = None):
        super().__init__(agent_name="report_agent", agent_version="1.0")
        self.identity_resolver = identity_resolver or IdentityResolver()

    async def execute(
        self,
        research_run_id: UUID,
        company_id: UUID,
        company_name: str,
        domain: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> AgentResponse:
        logger.info(f"[{self.agent_name}] Generating structured intelligence report for run {research_run_id}")

        evidence_items: List[NormalizedEvidence] = []
        if context and "evidence" in context:
            evidence_items = context["evidence"]

        identity: Optional[IdentityResult] = None
        if context and "identity" in context and isinstance(context["identity"], IdentityResult):
            identity = context["identity"]
        else:
            identity = await self.identity_resolver.resolve(
                company_name=company_name,
                company_url=domain,
            )

        report_content = ReportBuilder.build_report_content(identity, evidence_items)

        return AgentResponse(
            agent_name=self.agent_name,
            agent_version=self.agent_version,
            status="completed",
            research_run_id=research_run_id,
            evidence=evidence_items,
            metadata={
                "report_title": f"Company Intelligence Report — {identity.canonical_name}",
                "report_content": report_content,
                "sections_count": len(report_content),
            },
        )

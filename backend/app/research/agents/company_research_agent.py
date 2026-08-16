from typing import Any, Dict, List, Optional
from uuid import UUID
from app.core.logging import logger
from app.research.agents.base import AgentResponse, BaseAgent
from app.research.models import NormalizedEvidence
from app.research.normalizer import EvidenceNormalizer
from app.research.sources.official_website import OfficialWebsiteAdapter
from app.research.sources.search import PublicSearchAdapter


class CompanyResearchAgent(BaseAgent):
    """
    Agent 2: Company Research Agent
    Extracts canonical profile, official domain, overview, products, and operations.
    """

    def __init__(
        self,
        official_adapter: Optional[OfficialWebsiteAdapter] = None,
        search_adapter: Optional[PublicSearchAdapter] = None,
    ):
        super().__init__(agent_name="company_research", agent_version="1.0")
        self.official_adapter = official_adapter or OfficialWebsiteAdapter()
        self.search_adapter = search_adapter or PublicSearchAdapter()

    async def execute(
        self,
        research_run_id: UUID,
        company_id: UUID,
        company_name: str,
        domain: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> AgentResponse:
        logger.info(f"[{self.agent_name}] Executing for '{company_name}' (domain: {domain})")
        evidence_items: List[NormalizedEvidence] = []
        warnings: List[str] = []
        errors: List[str] = []

        try:
            # 1. Search knowledge graph findings
            search_findings = await self.search_adapter.collect(company_name, domain)
            for f in search_findings:
                ev = EvidenceNormalizer.normalize_finding(f)
                ev.agent_name = self.agent_name
                evidence_items.append(ev)

            # 2. Official website overview findings
            resolved_domain = domain or await self.search_adapter.resolve_domain(company_name)
            if resolved_domain:
                site_findings = await self.official_adapter.collect(company_name, resolved_domain)
                for f in site_findings:
                    ev = EvidenceNormalizer.normalize_finding(f)
                    ev.agent_name = self.agent_name
                    evidence_items.append(ev)
            else:
                warnings.append(f"Official domain for '{company_name}' could not be resolved.")

            status = "completed" if len(evidence_items) > 0 else "partial"

            return AgentResponse(
                agent_name=self.agent_name,
                agent_version=self.agent_version,
                status=status,
                research_run_id=research_run_id,
                evidence=evidence_items,
                warnings=warnings,
                errors=errors,
                metadata={
                    "company_name": company_name,
                    "resolved_domain": resolved_domain,
                    "evidence_count": len(evidence_items),
                },
            )

        except Exception as exc:
            logger.error(f"[{self.agent_name}] Execution failed: {exc}")
            return AgentResponse(
                agent_name=self.agent_name,
                agent_version=self.agent_version,
                status="failed",
                research_run_id=research_run_id,
                errors=[str(exc)],
            )

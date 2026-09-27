from typing import Any, Dict, List, Optional, Union
from uuid import UUID
from app.core.logging import logger
from app.research.agents.base import (
    AgentInput,
    AgentResponse,
    AgentResult,
    AgentStatus,
    BaseAgent,
)
from app.research.agents.errors import AgentSourceError
from app.research.models import NormalizedEvidence
from app.research.normalizer import EvidenceNormalizer
from app.research.sources.official_website import OfficialWebsiteAdapter
from app.research.sources.search import PublicSearchAdapter


class CompanyResearchAgent(BaseAgent):
    """
    Agent 2: Company Research Agent
    Responsible for:
    - Company profile, overview, products, and operational background discovery
    - Public knowledge graph research (via PublicSearchAdapter)
    - Official website first-party research (via OfficialWebsiteAdapter)
    - Structured findings and NormalizedEvidence collection
    """

    def __init__(
        self,
        official_adapter: Optional[OfficialWebsiteAdapter] = None,
        search_adapter: Optional[PublicSearchAdapter] = None,
    ):
        super().__init__(
            agent_name="company_research",
            agent_description="Discovers corporate overview, canonical domain, products, and public profiles.",
            agent_version="1.0",
        )
        self.official_adapter = official_adapter or OfficialWebsiteAdapter()
        self.search_adapter = search_adapter or PublicSearchAdapter()

    async def execute(
        self,
        input_data: Union[AgentInput, UUID, None] = None,
        company_id: Optional[UUID] = None,
        company_name: Optional[str] = None,
        domain: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> AgentResult:
        """
        Executes company intelligence research.
        Supports both modern AgentInput and backward-compatible parameter signatures.
        """
        # 1. Normalize input into AgentInput contract
        if isinstance(input_data, AgentInput):
            agent_input = input_data
        elif isinstance(input_data, dict):
            agent_input = AgentInput.model_validate(input_data)
        else:
            # Handle legacy positional/keyword parameters
            run_id = input_data or kwargs.get("research_run_id")
            c_id = company_id or kwargs.get("company_id")
            c_name = company_name or kwargs.get("company_name", "")
            c_url = domain or kwargs.get("company_url") or kwargs.get("domain")
            c_ctx = context or kwargs.get("context") or {}

            if not run_id or not c_id or not c_name:
                raise ValueError("Missing required fields for CompanyResearchAgent: research_run_id, company_id, company_name")

            agent_input = AgentInput(
                research_run_id=run_id,
                company_id=c_id,
                company_name=c_name,
                company_url=c_url,
                context=c_ctx,
            )

        name = agent_input.company_name.strip()
        run_id = agent_input.research_run_id
        resolved_domain = (
            agent_input.domain
            or domain
            or (agent_input.context.get("domain") if agent_input.context else None)
        )

        logger.info(f"[{self.agent_name}] Executing for '{name}' (domain: {resolved_domain})")

        evidence_items: List[NormalizedEvidence] = []
        structured_findings: List[Dict[str, Any]] = []
        warnings: List[str] = []
        errors: List[str] = []
        sources_queried: List[str] = []

        search_failed = False
        website_failed = False

        # 2. Query Public Knowledge Graph (Wikipedia / Open Public APIs)
        try:
            search_findings = await self.search_adapter.collect(name, resolved_domain)
            sources_queried.append("PublicSearchAdapter")

            for f in search_findings:
                ev = EvidenceNormalizer.normalize_finding(f)
                ev.agent_name = self.agent_name
                evidence_items.append(ev)
                structured_findings.append({
                    "source": "public_search",
                    "claim": f.claim,
                    "url": f.source_url,
                    "title": f.source_title,
                    "metadata": f.raw_metadata,
                })
        except Exception as exc:
            search_failed = True
            logger.warning(f"[{self.agent_name}] Public search source query failed: {exc}")
            warnings.append(f"Public search query encountered error: {exc}")

        # 3. Query Official Website if a verified domain is provided
        if resolved_domain:
            try:
                site_findings = await self.official_adapter.collect(name, resolved_domain)
                sources_queried.append("OfficialWebsiteAdapter")

                for f in site_findings:
                    ev = EvidenceNormalizer.normalize_finding(f)
                    ev.agent_name = self.agent_name
                    evidence_items.append(ev)
                    structured_findings.append({
                        "source": "official_website",
                        "claim": f.claim,
                        "url": f.source_url,
                        "title": f.source_title,
                        "metadata": f.raw_metadata,
                    })
            except Exception as exc:
                website_failed = True
                logger.warning(f"[{self.agent_name}] Official website collection failed: {exc}")
                warnings.append(f"Official website collection failed for {resolved_domain}: {exc}")
        else:
            warnings.append(f"Official corporate domain for '{name}' was not provided; skipping direct website crawl.")

        # 4. Status Determination
        if len(evidence_items) > 0:
            if search_failed or website_failed or not resolved_domain:
                status = AgentStatus.PARTIAL.value if (search_failed or website_failed) else AgentStatus.COMPLETED.value
            else:
                status = AgentStatus.COMPLETED.value
        else:
            if search_failed and (website_failed or not resolved_domain):
                status = AgentStatus.FAILED.value
                errors.append("All primary corporate information sources failed to return evidence.")
            else:
                status = AgentStatus.PARTIAL.value

        return AgentResult(
            agent_name=self.agent_name,
            agent_version=self.agent_version,
            status=status,
            research_run_id=run_id,
            findings=structured_findings,
            evidence=evidence_items,
            warnings=warnings,
            errors=errors,
            metadata={
                "company_name": name,
                "resolved_domain": resolved_domain,
                "evidence_count": len(evidence_items),
                "findings_count": len(structured_findings),
                "sources_queried": sources_queried,
            },
        )

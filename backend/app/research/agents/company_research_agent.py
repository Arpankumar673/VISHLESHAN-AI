import asyncio
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
from app.research.models import NormalizedEvidence, SourceFinding
from app.research.normalizer import EvidenceNormalizer
from app.research.sources.official_website import OfficialWebsiteAdapter
from app.research.sources.search import PublicSearchAdapter
from app.schemas.evidence import SourceType


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
        Executes company intelligence research across public search and official corporate website concurrently.
        Supports both modern AgentInput and backward-compatible parameter signatures.
        """
        # 1. Normalize input into AgentInput contract
        if isinstance(input_data, AgentInput):
            agent_input = input_data
        elif isinstance(input_data, dict):
            agent_input = AgentInput.model_validate(input_data)
        else:
            # Handle legacy positional/keyword parameters
            run_id = input_data if isinstance(input_data, UUID) else kwargs.get("research_run_id") or UUID("00000000-0000-0000-0000-000000000000")
            c_id = company_id or kwargs.get("company_id") or UUID("00000000-0000-0000-0000-000000000000")
            c_name = company_name or kwargs.get("company_name", "")
            c_url = domain or kwargs.get("company_url") or kwargs.get("domain")
            c_ctx = context or kwargs.get("context") or {}

            if not c_name:
                raise ValueError("Either agent_input or company_name must be provided to CompanyResearchAgent.")

            agent_input = AgentInput(
                research_run_id=run_id,
                company_id=c_id,
                company_name=c_name,
                company_url=f"https://{c_url}" if c_url and not c_url.startswith("http") else c_url,
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

        # 2. Concurrent Adapter Execution
        tasks = [self.search_adapter.collect(name, resolved_domain)]
        if resolved_domain:
            tasks.append(self.official_adapter.collect(name, resolved_domain))
        else:
            warnings.append(f"Official corporate domain for '{name}' was not provided; skipping direct website crawl.")

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process PublicSearchAdapter results
        search_res = results[0]
        if isinstance(search_res, Exception):
            search_failed = True
            logger.warning(f"[{self.agent_name}] Public search source query failed: {search_res}")
            warnings.append(f"Public search query encountered error: {search_res}")
        elif isinstance(search_res, list):
            sources_queried.append("PublicSearchAdapter")
            for f in search_res:
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

        # Process OfficialWebsiteAdapter results if domain was provided
        if resolved_domain:
            site_res = results[1]
            if isinstance(site_res, Exception):
                website_failed = True
                logger.warning(f"[{self.agent_name}] Official website collection failed: {site_res}")
                warnings.append(f"Official website collection failed for {resolved_domain}: {site_res}")
            elif isinstance(site_res, list):
                sources_queried.append("OfficialWebsiteAdapter")
                for f in site_res:
                    if "operates official domain" in f.claim:
                        f.raw_metadata.update({
                            "claim_key": "official_domain",
                            "claim_value": resolved_domain,
                            "category": "website",
                        })

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

                    # Extract atomic claims from JSON-LD metadata if present
                    json_ld = f.raw_metadata.get("json_ld") if f.raw_metadata else None
                    if json_ld and isinstance(json_ld, dict):
                        # Atomic Claim: legal_name
                        if json_ld.get("legal_name"):
                            legal_name_val = json_ld["legal_name"]
                            atom_finding = SourceFinding(
                                claim=f"{name} official legal entity name is {legal_name_val}",
                                evidence_text=f"Official legal entity name extracted from JSON-LD schema: '{legal_name_val}'",
                                source_url=f.source_url,
                                source_title=f.source_title,
                                source_type=SourceType.OFFICIAL_COMPANY,
                                raw_metadata={
                                    "claim_key": "legal_name",
                                    "claim_value": legal_name_val,
                                    "category": "identity",
                                    "json_ld": json_ld,
                                },
                            )
                            atom_ev = EvidenceNormalizer.normalize_finding(atom_finding)
                            atom_ev.agent_name = self.agent_name
                            evidence_items.append(atom_ev)

                        # Atomic Claim: founding_year
                        if json_ld.get("founding_date"):
                            founding_val = json_ld["founding_date"]
                            atom_finding = SourceFinding(
                                claim=f"{name} was founded on {founding_val}",
                                evidence_text=f"Official founding date extracted from JSON-LD schema: '{founding_val}'",
                                source_url=f.source_url,
                                source_title=f.source_title,
                                source_type=SourceType.OFFICIAL_COMPANY,
                                raw_metadata={
                                    "claim_key": "founding_year",
                                    "claim_value": founding_val,
                                    "category": "registration",
                                    "json_ld": json_ld,
                                },
                            )
                            atom_ev = EvidenceNormalizer.normalize_finding(atom_finding)
                            atom_ev.agent_name = self.agent_name
                            evidence_items.append(atom_ev)

                        # Atomic Claim: headquarters
                        if json_ld.get("address"):
                            addr_val = json_ld["address"]
                            atom_finding = SourceFinding(
                                claim=f"{name} official corporate address is {addr_val}",
                                evidence_text=f"Official corporate address extracted from JSON-LD schema: '{addr_val}'",
                                source_url=f.source_url,
                                source_title=f.source_title,
                                source_type=SourceType.OFFICIAL_COMPANY,
                                raw_metadata={
                                    "claim_key": "headquarters",
                                    "claim_value": addr_val,
                                    "category": "identity",
                                    "json_ld": json_ld,
                                },
                            )
                            atom_ev = EvidenceNormalizer.normalize_finding(atom_finding)
                            atom_ev.agent_name = self.agent_name
                            evidence_items.append(atom_ev)

                        # Atomic Claim: corporate_reference (sameAs)
                        if json_ld.get("same_as") and isinstance(json_ld["same_as"], list):
                            for ref_url in json_ld["same_as"]:
                                atom_finding = SourceFinding(
                                    claim=f"{name} verified corporate reference at {ref_url}",
                                    evidence_text=f"Verified corporate reference URL extracted from JSON-LD schema: '{ref_url}'",
                                    source_url=f.source_url,
                                    source_title=f.source_title,
                                    source_type=SourceType.OFFICIAL_COMPANY,
                                    raw_metadata={
                                        "claim_key": "corporate_reference",
                                        "claim_value": ref_url,
                                        "category": "identity",
                                        "json_ld": json_ld,
                                    },
                                )
                                atom_ev = EvidenceNormalizer.normalize_finding(atom_finding)
                                atom_ev.agent_name = self.agent_name
                                evidence_items.append(atom_ev)

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

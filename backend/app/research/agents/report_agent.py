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
from app.research.identity import IdentityResolver
from app.research.models import IdentityResult, NormalizedEvidence
from app.research.report_builder import ReportBuilder


class ReportAgent(BaseAgent):
    """
    Agent 8: Report Agent
    Assembles structured 13-section Company Intelligence Report from verified evidence items and identity results.
    Ensures every assertion is grounded in traceable, hashed evidence.
    """

    def __init__(self, identity_resolver: Optional[IdentityResolver] = None):
        super().__init__(
            agent_name="report_agent",
            agent_description="Assembles structured 13-section Company Intelligence Report from verified evidence items.",
            agent_version="1.0",
        )
        self.identity_resolver = identity_resolver or IdentityResolver()

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
        Executes intelligence report construction.
        Supports both modern AgentInput and backward-compatible positional signatures.
        """
        # 1. Normalize input into AgentInput contract
        if isinstance(input_data, AgentInput):
            agent_input = input_data
        elif isinstance(input_data, dict):
            agent_input = AgentInput.model_validate(input_data)
        else:
            run_id = input_data or kwargs.get("research_run_id")
            c_id = company_id or kwargs.get("company_id")
            c_name = company_name or kwargs.get("company_name", "")
            c_url = domain or kwargs.get("company_url") or kwargs.get("domain")
            c_ctx = context or kwargs.get("context") or {}

            if not run_id or not c_id or not c_name:
                raise ValueError("Missing required fields for ReportAgent: research_run_id, company_id, company_name")

            agent_input = AgentInput(
                research_run_id=run_id,
                company_id=c_id,
                company_name=c_name,
                company_url=c_url,
                context=c_ctx,
            )

        name = agent_input.company_name.strip()
        run_id = agent_input.research_run_id
        url = agent_input.domain

        logger.info(f"[{self.agent_name}] Generating structured intelligence report for run {run_id}")

        evidence_items: List[NormalizedEvidence] = []
        exec_ctx = agent_input.context or {}

        # Extract evidence from context or previous_evidence
        if agent_input.previous_evidence:
            evidence_items.extend(agent_input.previous_evidence)

        if "evidence" in exec_ctx and isinstance(exec_ctx["evidence"], list):
            for item in exec_ctx["evidence"]:
                if isinstance(item, NormalizedEvidence) and item not in evidence_items:
                    evidence_items.append(item)

        if "agent_responses" in exec_ctx:
            for resp in exec_ctx["agent_responses"]:
                if isinstance(resp, (AgentResult, AgentResponse)):
                    for ev in resp.evidence:
                        if ev not in evidence_items:
                            evidence_items.append(ev)

        # Extract or resolve IdentityResult
        identity: Optional[IdentityResult] = None
        if "identity" in exec_ctx and isinstance(exec_ctx["identity"], IdentityResult):
            identity = exec_ctx["identity"]
        else:
            identity = await self.identity_resolver.resolve(
                company_name=name,
                company_url=url,
            )

        # Build 13-section report dictionary via ReportBuilder
        report_content = ReportBuilder.build_report_content(identity, evidence_items)

        # Build structured findings summary
        findings = [
            {
                "category": "report_generation",
                "report_title": f"Company Intelligence Report — {identity.canonical_name}",
                "sections_count": len(report_content),
                "trust_score": report_content.get("trust_score", {}).get("score"),
                "risk_level": report_content.get("risk_analysis", {}).get("overall_risk"),
            }
        ]

        return AgentResult(
            agent_name=self.agent_name,
            agent_version=self.agent_version,
            status=AgentStatus.COMPLETED.value,
            research_run_id=run_id,
            findings=findings,
            evidence=evidence_items,
            warnings=[],
            errors=[],
            metadata={
                "report_title": f"Company Intelligence Report — {identity.canonical_name}",
                "report_content": report_content,
                "sections_count": len(report_content),
                "canonical_name": identity.canonical_name,
                "official_domain": identity.official_domain,
                "trust_score": report_content.get("trust_score", {}).get("score"),
                "risk_level": report_content.get("risk_analysis", {}).get("overall_risk"),
                "evidence_count": len(evidence_items),
            },
        )

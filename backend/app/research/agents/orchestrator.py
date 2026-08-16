import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID
from app.core.logging import logger
from app.integrations.supabase import get_supabase_client
from app.research.agents.base import AgentResponse
from app.research.agents.company_research_agent import CompanyResearchAgent
from app.research.agents.evidence_trust_agent import EvidenceTrustAgent
from app.research.agents.news_hiring_agent import NewsHiringAgent
from app.research.agents.report_agent import ReportAgent
from app.research.agents.risk_analysis_agent import RiskAnalysisAgent
from app.research.agents.technology_reputation_agent import TechnologyReputationAgent
from app.research.agents.verification_agent import VerificationAgent
from app.research.identity import IdentityResolver
from app.research.models import IdentityResult, NormalizedEvidence, ResearchEngineResult


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class MultiAgentOrchestrator:
    """
    Agent 1: Orchestrator Agent
    Coordinates distributed multi-agent research execution:
    - Resolves initial identity
    - Dispatches 5 parallel research branches
    - Aggregates findings through Evidence & Trust Agent
    - Assembles final intelligence report through Report Agent
    - Persists audit trail to Supabase
    """

    def __init__(
        self,
        company_research_agent: Optional[CompanyResearchAgent] = None,
        verification_agent: Optional[VerificationAgent] = None,
        news_hiring_agent: Optional[NewsHiringAgent] = None,
        technology_agent: Optional[TechnologyReputationAgent] = None,
        risk_agent: Optional[RiskAnalysisAgent] = None,
        evidence_trust_agent: Optional[EvidenceTrustAgent] = None,
        report_agent: Optional[ReportAgent] = None,
        identity_resolver: Optional[IdentityResolver] = None,
    ):
        self.company_research_agent = company_research_agent or CompanyResearchAgent()
        self.verification_agent = verification_agent or VerificationAgent()
        self.news_hiring_agent = news_hiring_agent or NewsHiringAgent()
        self.technology_agent = technology_agent or TechnologyReputationAgent()
        self.risk_agent = risk_agent or RiskAnalysisAgent()
        self.evidence_trust_agent = evidence_trust_agent or EvidenceTrustAgent()
        self.report_agent = report_agent or ReportAgent()
        self.identity_resolver = identity_resolver or IdentityResolver()
        self.supabase = get_supabase_client()

    async def execute_run(
        self,
        research_run_id: UUID,
        company_id: UUID,
        company_name: str,
        company_url: Optional[str] = None,
    ) -> ResearchEngineResult:
        logger.info(f"[Orchestrator] Launching multi-agent research run {research_run_id} for '{company_name}'")

        # 1. Update status to 'running'
        now_str = utc_now().isoformat()
        try:
            self.supabase.table("research_runs").update(
                {"status": "running", "started_at": now_str}
            ).eq("id", str(research_run_id)).execute()
        except Exception as exc:
            logger.warning(f"Could not update status to running in DB: {exc}")

        try:
            # 2. Stage: Initial Identity Resolution
            identity = await self.identity_resolver.resolve(
                company_name=company_name,
                company_url=company_url,
            )
            domain = identity.official_domain

            # 3. Stage: Parallel Execution of 5 Specialized Research Branches
            logger.info(f"[Orchestrator] Dispatching 5 parallel research agent branches...")
            branch_tasks = [
                self.company_research_agent.execute(research_run_id, company_id, company_name, domain),
                self.verification_agent.execute(research_run_id, company_id, company_name, domain),
                self.news_hiring_agent.execute(research_run_id, company_id, company_name, domain),
                self.technology_agent.execute(research_run_id, company_id, company_name, domain),
                self.risk_agent.execute(research_run_id, company_id, company_name, domain),
            ]

            results = await asyncio.gather(*branch_tasks, return_exceptions=True)

            agent_responses: List[AgentResponse] = []
            has_failures = False
            successful_agents_count = 0

            for idx, res in enumerate(results):
                if isinstance(res, Exception):
                    logger.error(f"[Orchestrator] Branch {idx} encountered uncaught exception: {res}")
                    has_failures = True
                elif isinstance(res, AgentResponse):
                    agent_responses.append(res)
                    if res.status == "completed":
                        successful_agents_count += 1
                    elif res.status in ("partial", "failed"):
                        has_failures = True

            # 4. Stage: Evidence & Trust Agent aggregation and deduplication
            trust_response = await self.evidence_trust_agent.execute(
                research_run_id=research_run_id,
                company_id=company_id,
                company_name=company_name,
                domain=domain,
                context={"agent_responses": agent_responses},
            )
            unique_evidence: List[NormalizedEvidence] = trust_response.evidence

            # 5. Stage: Report Agent generation
            report_response = await self.report_agent.execute(
                research_run_id=research_run_id,
                company_id=company_id,
                company_name=company_name,
                domain=domain,
                context={"evidence": unique_evidence, "identity": identity},
            )
            report_content = report_response.metadata.get("report_content", {})

            # 6. Stage: Database Persistence
            # Update company profile
            try:
                company_update = {
                    "official_domain": identity.official_domain,
                    "description": identity.description,
                    "industry": identity.industry,
                    "headquarters": identity.headquarters,
                    "updated_at": utc_now().isoformat(),
                }
                self.supabase.table("companies").update(company_update).eq("id", str(company_id)).execute()
            except Exception as exc:
                logger.warning(f"Failed to update company record: {exc}")

            # Insert identifiers
            for ident in identity.identifiers:
                try:
                    self.supabase.table("company_identifiers").upsert(
                        {
                            "company_id": str(company_id),
                            "identifier_type": ident["identifier_type"],
                            "identifier_value": ident["identifier_value"],
                            "source_url": ident.get("source_url"),
                            "confidence": ident.get("confidence", 1.0),
                        }
                    ).execute()
                except Exception as exc:
                    logger.warning(f"Failed to insert company identifier: {exc}")

            # Insert evidence records
            for ev in unique_evidence:
                try:
                    self.supabase.table("evidence").insert(
                        {
                            "company_id": str(company_id),
                            "research_run_id": str(research_run_id),
                            "claim": ev.claim,
                            "evidence_text": ev.evidence_text,
                            "source_url": ev.source_url,
                            "source_title": ev.source_title,
                            "source_type": ev.source_type.value,
                            "published_at": ev.published_at.isoformat() if ev.published_at else None,
                            "observed_at": ev.observed_at.isoformat(),
                            "reliability_score": ev.reliability_score,
                            "confidence_score": ev.confidence_score,
                            "verification_status": ev.verification_status.value,
                            "agent_name": ev.agent_name,
                            "content_hash": ev.content_hash,
                        }
                    ).execute()
                except Exception as exc:
                    logger.warning(f"Failed to insert evidence record: {exc}")

            # Insert trust score record
            trust_score_meta = trust_response.metadata
            try:
                self.supabase.table("trust_scores").insert(
                    {
                        "company_id": str(company_id),
                        "research_run_id": str(research_run_id),
                        "score": trust_score_meta.get("preliminary_trust_score", 75.0),
                        "confidence": trust_score_meta.get("avg_reliability", 0.8),
                        "risk_level": trust_score_meta.get("preliminary_risk_level", "low"),
                        "evidence_coverage": round(min(1.0, len(unique_evidence) / 5.0), 2),
                        "algorithm_version": "v1.0-multi-agent-m5",
                        "explanation": f"Multi-agent synthesis across {len(agent_responses)} agent modules with {len(unique_evidence)} corroborated evidence items.",
                    }
                ).execute()
            except Exception as exc:
                logger.warning(f"Failed to insert trust score: {exc}")

            # Insert report record
            report_id = None
            try:
                report_insert = self.supabase.table("reports").insert(
                    {
                        "company_id": str(company_id),
                        "research_run_id": str(research_run_id),
                        "title": f"Company Intelligence Report — {identity.canonical_name}",
                        "content": report_content,
                        "report_version": "1.0",
                    }
                ).execute()
                if report_insert.data and len(report_insert.data) > 0:
                    report_id = UUID(report_insert.data[0]["id"])
            except Exception as exc:
                logger.warning(f"Failed to insert report record: {exc}")

            # 7. Final status determination
            if len(unique_evidence) > 0 and not has_failures:
                final_status = "completed"
            elif len(unique_evidence) > 0:
                final_status = "partial"
            else:
                final_status = "failed"

            completed_time = utc_now().isoformat()
            try:
                self.supabase.table("research_runs").update(
                    {
                        "status": final_status,
                        "completed_at": completed_time,
                    }
                ).eq("id", str(research_run_id)).execute()
            except Exception as exc:
                logger.warning(f"Failed to update research run final status: {exc}")

            logger.info(
                f"[Orchestrator] Run {research_run_id} completed with status '{final_status}', "
                f"{len(unique_evidence)} total evidence items, {successful_agents_count} successful branches."
            )

            return ResearchEngineResult(
                research_run_id=research_run_id,
                company_id=company_id,
                identity=identity,
                evidence_items=unique_evidence,
                report_id=report_id,
                status=final_status,
            )

        except Exception as exc:
            logger.exception(f"[Orchestrator] Research run {research_run_id} terminated with fatal error: {exc}")
            failed_time = utc_now().isoformat()
            try:
                self.supabase.table("research_runs").update(
                    {
                        "status": "failed",
                        "error_message": str(exc),
                        "completed_at": failed_time,
                    }
                ).eq("id", str(research_run_id)).execute()
            except Exception:
                pass

            return ResearchEngineResult(
                research_run_id=research_run_id,
                company_id=company_id,
                identity=IdentityResult(canonical_name=company_name),
                evidence_items=[],
                status="failed",
                error_message=str(exc),
            )

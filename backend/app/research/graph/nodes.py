from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID
from app.core.logging import logger
from app.integrations.supabase import get_supabase_client
from app.research.agents.base import AgentInput, AgentResult
from app.research.agents.company_research_agent import CompanyResearchAgent
from app.research.agents.evidence_trust_agent import EvidenceTrustAgent
from app.research.agents.news_hiring_agent import NewsHiringAgent
from app.research.agents.report_agent import ReportAgent
from app.research.agents.risk_analysis_agent import RiskAnalysisAgent
from app.research.agents.technology_reputation_agent import TechnologyReputationAgent
from app.research.agents.verification_agent import VerificationAgent
from app.research.graph.state import ResearchGraphState
from app.research.identity import IdentityResolver
from app.research.models import IdentityResult, NormalizedEvidence


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


async def node_resolve_identity(state: ResearchGraphState) -> Dict[str, Any]:
    """
    Stage 1 Node: Identity Resolution.
    If identity resolution succeeds, stores IdentityResult.
    If resolution fails or no domain exists, DOES NOT fabricate a fake domain.
    Explicitly marks identity_status='unresolved' or 'unverified'.
    """
    company_name = state["company_name"]
    company_url = state.get("company_url")
    run_id = state["research_run_id"]

    logger.info(f"[LangGraph:node_resolve_identity] Resolving identity for '{company_name}' (run {run_id})")
    resolver = IdentityResolver()

    try:
        identity = await resolver.resolve(
            company_name=company_name,
            company_url=company_url,
        )

        if identity.official_domain:
            identity_status = "verified"
        else:
            identity_status = "unverified"

        return {
            "identity": identity,
            "identity_status": identity_status,
            "status": "running",
        }
    except Exception as exc:
        logger.warning(f"[LangGraph:node_resolve_identity] Failed to resolve identity for '{company_name}': {exc}")
        fallback_identity = IdentityResult(
            canonical_name=company_name,
            official_domain=None,
            official_website=None,
            description="Unresolved corporate entity identity.",
            confidence=0.30,
        )
        return {
            "identity": fallback_identity,
            "identity_status": "unresolved",
            "warnings": [f"Identity resolution could not verify an official corporate domain for '{company_name}'."],
            "status": "running",
        }


async def node_company_research(state: ResearchGraphState) -> Dict[str, Any]:
    """Stage 2 Branch Node: Company Research Agent execution."""
    agent = CompanyResearchAgent()
    domain = state["identity"].official_domain if state.get("identity") else None
    
    inp = AgentInput(
        research_run_id=state["research_run_id"],
        company_id=state["company_id"],
        company_name=state["company_name"],
        company_url=domain or state.get("company_url"),
        correlation_id=state.get("correlation_id"),
    )

    try:
        result = await agent.run(inp)
        return {
            "agent_results": {"company_research": result},
            "evidence": result.evidence,
            "findings": result.findings,
            "warnings": result.warnings,
            "errors": result.errors,
        }
    except Exception as exc:
        logger.error(f"[LangGraph:node_company_research] Uncaught exception: {exc}")
        return {
            "agent_results": {"company_research": AgentResult(agent_name="company_research", status="failed", research_run_id=state["research_run_id"], errors=[str(exc)])},
            "errors": [f"CompanyResearchAgent failed: {exc}"],
        }


async def node_verification(state: ResearchGraphState) -> Dict[str, Any]:
    """Stage 2 Branch Node: Verification Agent execution."""
    agent = VerificationAgent()
    domain = state["identity"].official_domain if state.get("identity") else None

    inp = AgentInput(
        research_run_id=state["research_run_id"],
        company_id=state["company_id"],
        company_name=state["company_name"],
        company_url=domain or state.get("company_url"),
        correlation_id=state.get("correlation_id"),
    )

    try:
        result = await agent.run(inp)
        return {
            "agent_results": {"verification": result},
            "evidence": result.evidence,
            "findings": result.findings,
            "warnings": result.warnings,
            "errors": result.errors,
        }
    except Exception as exc:
        logger.error(f"[LangGraph:node_verification] Uncaught exception: {exc}")
        return {
            "agent_results": {"verification": AgentResult(agent_name="verification", status="failed", research_run_id=state["research_run_id"], errors=[str(exc)])},
            "errors": [f"VerificationAgent failed: {exc}"],
        }


async def node_news_hiring(state: ResearchGraphState) -> Dict[str, Any]:
    """Stage 2 Branch Node: News & Hiring Agent execution."""
    agent = NewsHiringAgent()
    domain = state["identity"].official_domain if state.get("identity") else None

    inp = AgentInput(
        research_run_id=state["research_run_id"],
        company_id=state["company_id"],
        company_name=state["company_name"],
        company_url=domain or state.get("company_url"),
        correlation_id=state.get("correlation_id"),
    )

    try:
        result = await agent.run(inp)
        return {
            "agent_results": {"news_hiring": result},
            "evidence": result.evidence,
            "findings": result.findings,
            "warnings": result.warnings,
            "errors": result.errors,
        }
    except Exception as exc:
        logger.error(f"[LangGraph:node_news_hiring] Uncaught exception: {exc}")
        return {
            "agent_results": {"news_hiring": AgentResult(agent_name="news_hiring", status="failed", research_run_id=state["research_run_id"], errors=[str(exc)])},
            "errors": [f"NewsHiringAgent failed: {exc}"],
        }


async def node_technology_reputation(state: ResearchGraphState) -> Dict[str, Any]:
    """Stage 2 Branch Node: Technology & Reputation Agent execution."""
    agent = TechnologyReputationAgent()
    domain = state["identity"].official_domain if state.get("identity") else None

    inp = AgentInput(
        research_run_id=state["research_run_id"],
        company_id=state["company_id"],
        company_name=state["company_name"],
        company_url=domain or state.get("company_url"),
        correlation_id=state.get("correlation_id"),
    )

    try:
        result = await agent.run(inp)
        return {
            "agent_results": {"technology_reputation": result},
            "evidence": result.evidence,
            "findings": result.findings,
            "warnings": result.warnings,
            "errors": result.errors,
        }
    except Exception as exc:
        logger.error(f"[LangGraph:node_technology_reputation] Uncaught exception: {exc}")
        return {
            "agent_results": {"technology_reputation": AgentResult(agent_name="technology_reputation", status="failed", research_run_id=state["research_run_id"], errors=[str(exc)])},
            "errors": [f"TechnologyReputationAgent failed: {exc}"],
        }


async def node_risk_analysis(state: ResearchGraphState) -> Dict[str, Any]:
    """Stage 3 Node: Risk Analysis Agent execution (fan-in from Stage 2 primary branches)."""
    agent = RiskAnalysisAgent()
    domain = state["identity"].official_domain if state.get("identity") else None

    inp = AgentInput(
        research_run_id=state["research_run_id"],
        company_id=state["company_id"],
        company_name=state["company_name"],
        company_url=domain or state.get("company_url"),
        previous_evidence=state.get("evidence", []),
        previous_findings=state.get("findings", []),
        correlation_id=state.get("correlation_id"),
    )

    try:
        result = await agent.run(inp)
        return {
            "agent_results": {"risk_analysis": result},
            "evidence": result.evidence,
            "findings": result.findings,
            "risk_summary": result.metadata,
            "warnings": result.warnings,
            "errors": result.errors,
        }
    except Exception as exc:
        logger.error(f"[LangGraph:node_risk_analysis] Uncaught exception: {exc}")
        return {
            "agent_results": {"risk_analysis": AgentResult(agent_name="risk_analysis", status="failed", research_run_id=state["research_run_id"], errors=[str(exc)])},
            "errors": [f"RiskAnalysisAgent failed: {exc}"],
        }


async def node_evidence_trust(state: ResearchGraphState) -> Dict[str, Any]:
    """Stage 4 Node: Evidence & Trust Agent aggregation and SHA-256 deduplication."""
    agent = EvidenceTrustAgent()
    domain = state["identity"].official_domain if state.get("identity") else None

    inp = AgentInput(
        research_run_id=state["research_run_id"],
        company_id=state["company_id"],
        company_name=state["company_name"],
        company_url=domain or state.get("company_url"),
        previous_evidence=state.get("evidence", []),
        correlation_id=state.get("correlation_id"),
    )

    try:
        result = await agent.run(inp)
        return {
            "agent_results": {"evidence_trust": result},
            "trust_score": result.metadata,
            # Replace evidence with deduplicated list returned by EvidenceTrustAgent
            "evidence": result.evidence,
            "warnings": result.warnings,
            "errors": result.errors,
        }
    except Exception as exc:
        logger.error(f"[LangGraph:node_evidence_trust] Uncaught exception: {exc}")
        return {
            "agent_results": {"evidence_trust": AgentResult(agent_name="evidence_trust", status="failed", research_run_id=state["research_run_id"], errors=[str(exc)])},
            "errors": [f"EvidenceTrustAgent failed: {exc}"],
        }


async def node_report_agent(state: ResearchGraphState) -> Dict[str, Any]:
    """Stage 5 Node: Report Agent construction of 13-section intelligence report."""
    agent = ReportAgent()
    domain = state["identity"].official_domain if state.get("identity") else None

    inp = AgentInput(
        research_run_id=state["research_run_id"],
        company_id=state["company_id"],
        company_name=state["company_name"],
        company_url=domain or state.get("company_url"),
        previous_evidence=state.get("evidence", []),
        context={"identity": state.get("identity")},
        correlation_id=state.get("correlation_id"),
    )

    try:
        result = await agent.run(inp)
        return {
            "agent_results": {"report_agent": result},
            "report_content": result.metadata.get("report_content", {}),
            "warnings": result.warnings,
            "errors": result.errors,
        }
    except Exception as exc:
        logger.error(f"[LangGraph:node_report_agent] Uncaught exception: {exc}")
        return {
            "agent_results": {"report_agent": AgentResult(agent_name="report_agent", status="failed", research_run_id=state["research_run_id"], errors=[str(exc)])},
            "errors": [f"ReportAgent failed: {exc}"],
        }


async def node_persist_results(state: ResearchGraphState) -> Dict[str, Any]:
    """Stage 6 Node: Supabase database persistence and final status determination."""
    supabase = get_supabase_client()
    company_id = str(state["company_id"])
    run_id = str(state["research_run_id"])
    identity = state.get("identity")
    evidence_items = state.get("evidence", [])
    report_content = state.get("report_content", {})
    trust_meta = state.get("trust_score", {})
    errors = state.get("errors", [])

    # Update company record
    if identity:
        try:
            supabase.table("companies").update(
                {
                    "official_domain": identity.official_domain,
                    "description": identity.description,
                    "industry": identity.industry,
                    "headquarters": identity.headquarters,
                    "updated_at": utc_now().isoformat(),
                }
            ).eq("id", company_id).execute()
        except Exception as exc:
            logger.warning(f"[LangGraph:node_persist_results] Failed to update company record: {exc}")

        for ident in identity.identifiers:
            try:
                supabase.table("company_identifiers").upsert(
                    {
                        "company_id": company_id,
                        "identifier_type": ident["identifier_type"],
                        "identifier_value": ident["identifier_value"],
                        "source_url": ident.get("source_url"),
                        "confidence": ident.get("confidence", 1.0),
                    }
                ).execute()
            except Exception as exc:
                logger.warning(f"[LangGraph:node_persist_results] Failed to insert company identifier: {exc}")

    # Insert evidence
    for ev in evidence_items:
        try:
            supabase.table("evidence").insert(
                {
                    "company_id": company_id,
                    "research_run_id": run_id,
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
            logger.warning(f"[LangGraph:node_persist_results] Failed to insert evidence: {exc}")

    # Insert trust score
    try:
        supabase.table("trust_scores").insert(
            {
                "company_id": company_id,
                "research_run_id": run_id,
                "score": trust_meta.get("preliminary_trust_score", 75.0),
                "confidence": trust_meta.get("avg_reliability", 0.8),
                "risk_level": trust_meta.get("preliminary_risk_level", "low"),
                "evidence_coverage": round(min(1.0, len(evidence_items) / 5.0), 2),
                "algorithm_version": "v1.0-langgraph-m6",
                "explanation": f"LangGraph multi-agent synthesis with {len(evidence_items)} deduplicated evidence items.",
            }
        ).execute()
    except Exception as exc:
        logger.warning(f"[LangGraph:node_persist_results] Failed to insert trust score: {exc}")

    # Insert report
    report_id = None
    if identity and report_content:
        try:
            report_insert = supabase.table("reports").insert(
                {
                    "company_id": company_id,
                    "research_run_id": run_id,
                    "title": f"Company Intelligence Report — {identity.canonical_name}",
                    "content": report_content,
                    "report_version": "1.0",
                }
            ).execute()
            if report_insert.data and len(report_insert.data) > 0:
                report_id = UUID(report_insert.data[0]["id"])
        except Exception as exc:
            logger.warning(f"[LangGraph:node_persist_results] Failed to insert report: {exc}")

    # Determine final status
    if len(evidence_items) > 0 and len(errors) == 0:
        final_status = "completed"
    elif len(evidence_items) > 0:
        final_status = "partial"
    else:
        final_status = "failed"

    # Update research_runs final status
    try:
        supabase.table("research_runs").update(
            {
                "status": final_status,
                "completed_at": utc_now().isoformat(),
            }
        ).eq("id", run_id).execute()
    except Exception as exc:
        logger.warning(f"[LangGraph:node_persist_results] Failed to update research_runs final status: {exc}")

    return {
        "status": final_status,
        "report_id": report_id,
    }

import asyncio
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID
from app.core.logging import logger
from app.integrations.supabase import get_supabase_client
from app.research.deduplicator import EvidenceDeduplicator
from app.research.identity import IdentityResolver
from app.research.models import NormalizedEvidence, ResearchEngineResult, SourceFinding
from app.research.normalizer import EvidenceNormalizer
from app.research.report_builder import ReportBuilder
from app.research.sources.official_website import OfficialWebsiteAdapter
from app.research.sources.search import PublicSearchAdapter


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ResearchEngine:
    """
    Orchestrates end-to-end evidence-backed company intelligence research:
    Identity Resolution -> Source Collection -> Normalization -> Deduplication -> Persistence -> Report Generation.
    """

    def __init__(
        self,
        official_adapter: Optional[OfficialWebsiteAdapter] = None,
        search_adapter: Optional[PublicSearchAdapter] = None,
        identity_resolver: Optional[IdentityResolver] = None,
    ):
        self.official_adapter = official_adapter or OfficialWebsiteAdapter()
        self.search_adapter = search_adapter or PublicSearchAdapter()
        self.identity_resolver = identity_resolver or IdentityResolver(self.search_adapter)
        self.supabase = get_supabase_client()

    async def run(
        self,
        research_run_id: UUID,
        company_id: UUID,
        company_name: str,
        company_url: Optional[str] = None,
    ) -> ResearchEngineResult:
        logger.info(f"Starting research run {research_run_id} for company '{company_name}'")

        # 1. Update status to 'running'
        now_str = utc_now().isoformat()
        try:
            self.supabase.table("research_runs").update(
                {"status": "running", "started_at": now_str}
            ).eq("id", str(research_run_id)).execute()
        except Exception as exc:
            logger.warning(f"Could not update status to running in DB: {exc}")

        try:
            # 2. Stage: Identity Resolution & Source Collection
            raw_findings: List[SourceFinding] = []

            # First, resolve domain & query search adapter
            search_findings = await self.search_adapter.collect(company_name, company_url)
            raw_findings.extend(search_findings)

            # Resolve identity
            identity = await self.identity_resolver.resolve(
                company_name=company_name,
                company_url=company_url,
                findings=raw_findings,
            )

            # Query official website adapter using resolved domain
            if identity.official_domain:
                official_findings = await self.official_adapter.collect(
                    company_name=company_name,
                    domain=identity.official_domain,
                )
                raw_findings.extend(official_findings)

            # 3. Stage: Evidence Normalization & Deduplication
            normalized_items: List[NormalizedEvidence] = [
                EvidenceNormalizer.normalize_finding(f) for f in raw_findings
            ]
            unique_evidence = EvidenceDeduplicator.deduplicate(normalized_items)

            # 4. Stage: Database Persistence
            # Update company profile with resolved metadata
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

            # 5. Stage: Report Generation & Trust Score Calculation
            report_content = ReportBuilder.build_report_content(identity, unique_evidence)
            trust_score_data = report_content.get("trust_score", {})

            # Insert trust score record
            try:
                self.supabase.table("trust_scores").insert(
                    {
                        "company_id": str(company_id),
                        "research_run_id": str(research_run_id),
                        "score": trust_score_data.get("score", 75.0),
                        "confidence": trust_score_data.get("confidence", 0.8),
                        "risk_level": trust_score_data.get("risk_level", "low"),
                        "evidence_coverage": trust_score_data.get("evidence_coverage", 0.5),
                        "algorithm_version": trust_score_data.get("algorithm_version", "v1.0"),
                        "explanation": trust_score_data.get("explanation", "M4 initial evaluation"),
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

            # 6. Final Status Update
            final_status = "completed" if len(unique_evidence) > 0 else "partial"
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
                f"Research run {research_run_id} completed successfully with {len(unique_evidence)} evidence items."
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
            logger.exception(f"Research run {research_run_id} failed: {exc}")
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

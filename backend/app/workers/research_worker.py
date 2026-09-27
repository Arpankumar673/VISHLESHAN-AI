import asyncio
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import UUID

from arq.connections import RedisSettings

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.core.config import settings
from app.core.logging import logger
from app.repositories.company_repository import CompanyRepository
from app.repositories.research_repository import ResearchRepository
from app.research.agents.orchestrator import MultiAgentOrchestrator


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


async def run_research(
    ctx: Dict[str, Any],
    research_run_id_str: str,
    company_name: str,
    company_url: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Durable ARQ Background Job Function for executing Vishleshan AI Research Runs.
    Idempotent, fault-tolerant, and logs structured execution steps.
    """
    run_id = UUID(research_run_id_str)
    research_repo = ResearchRepository()
    company_repo = CompanyRepository()
    orchestrator = MultiAgentOrchestrator()

    logger.info(f"[ARQ Worker] Picked up research job {run_id} for target '{company_name}'")

    # 1. Idempotency Check
    run_data = research_repo.get_by_id(run_id)
    if not run_data:
        logger.error(f"[ARQ Worker] Research run {run_id} not found in database. Terminating job.")
        return {"status": "error", "message": "Research run ID not found"}

    if run_data.get("status") == "completed":
        logger.info(f"[ARQ Worker] Job {run_id} is already completed. Skipping duplicate execution.")
        return {"status": "already_completed", "research_run_id": str(run_id)}

    company_id = UUID(run_data["company_id"])

    # 2. Update status to 'running' and record worker metadata
    attempt_count = (run_data.get("attempt_count") or 0) + 1
    worker_id = f"arq-worker-{os.getpid()}"

    try:
        research_repo.supabase.table("research_runs").update(
            {
                "status": "running",
                "started_at": utc_now().isoformat(),
                "attempt_count": attempt_count,
                "worker_id": worker_id,
            }
        ).eq("id", str(run_id)).execute()
    except Exception as exc:
        logger.warning(f"[ARQ Worker] Could not update job running state in DB: {exc}")

    # 3. Execute LangGraph Research Workflow
    try:
        logger.info(f"[ARQ Worker] Executing LangGraph orchestrator for run {run_id}...")
        result = await orchestrator.execute_langgraph_run(
            research_run_id=run_id,
            company_id=company_id,
            company_name=company_name,
            company_url=company_url,
        )

        logger.info(f"[ARQ Worker] Research run {run_id} finished successfully with status '{result.status}'")
        return {
            "status": result.status,
            "research_run_id": str(run_id),
            "company_id": str(company_id),
            "evidence_count": len(result.evidence),
        }

    except Exception as fatal_exc:
        safe_error_msg = "An error occurred during multi-agent research execution."
        logger.exception(f"[ARQ Worker] Fatal error executing research run {run_id}: {fatal_exc}")

        try:
            research_repo.update_status(
                run_id=run_id,
                status="failed",
                error_message=safe_error_msg,
            )
            research_repo.supabase.table("research_runs").update(
                {"last_error": str(fatal_exc)}
            ).eq("id", str(run_id)).execute()
        except Exception as db_exc:
            logger.error(f"[ARQ Worker] Failed to persist error state for run {run_id}: {db_exc}")

        raise fatal_exc


class WorkerSettings:
    """
    ARQ Worker Process Configuration
    Run command: py -3 -m arq app.workers.research_worker.WorkerSettings
    """
    functions = [run_research]

    # Parse Redis URL or fallback to default DSN
    redis_url = settings.REDIS_URL or "redis://localhost:6379/0"
    redis_settings = RedisSettings.from_dsn(redis_url)

    max_jobs = 10
    job_timeout = 300
    max_tries = 3
    health_check_interval = 30

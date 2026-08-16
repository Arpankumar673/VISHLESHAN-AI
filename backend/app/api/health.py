import time
from fastapi import APIRouter
from app.core.config import settings
from app.integrations.supabase import get_supabase_client
from app.schemas.health import DatabaseHealthResponse, HealthResponse

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="API Health Status",
    description="Check whether the Vishleshan AI FastAPI backend service is operational.",
)
async def get_health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service="vishleshan-api",
        version=settings.VERSION,
    )


@router.get(
    "/health/database",
    response_model=DatabaseHealthResponse,
    summary="Database Connectivity Health Check",
    description="Verify live connectivity to Supabase PostgreSQL database without exposing credentials.",
)
async def get_database_health() -> DatabaseHealthResponse:
    start_time = time.perf_counter()
    try:
        supabase = get_supabase_client()
        # Non-destructive query to verify database response
        res = supabase.table("companies").select("id").limit(1).execute()
        latency = (time.perf_counter() - start_time) * 1000
        return DatabaseHealthResponse(
            status="ok",
            database="connected",
            latency_ms=round(latency, 2),
            service="vishleshan-api",
        )
    except Exception:
        latency = (time.perf_counter() - start_time) * 1000
        return DatabaseHealthResponse(
            status="degraded",
            database="disconnected",
            latency_ms=round(latency, 2),
            service="vishleshan-api",
        )

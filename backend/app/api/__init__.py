from fastapi import APIRouter
from app.api.health import router as health_router
from app.api.companies import router as companies_router
from app.api.research import router as research_router
from app.api.history import router as history_router
from app.api.evidence import router as evidence_router
from app.api.reports import router as reports_router

api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(companies_router)
api_router.include_router(research_router)
api_router.include_router(history_router)
api_router.include_router(evidence_router)
api_router.include_router(reports_router)

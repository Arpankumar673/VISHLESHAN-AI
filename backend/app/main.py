import time
from uuid import uuid4
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api import api_router
from app.core.config import settings
from app.core.errors import AppException
from app.core.logging import logger

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=(
        "Vishleshan AI — Enterprise AI-Powered Company Intelligence, "
        "Verification & Trust Analysis Platform Backend API."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
)

# ------------------------------------------------------------
# CORS Middleware
# ------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
)


# ------------------------------------------------------------
# Request Timing & Correlation Middleware
# ------------------------------------------------------------
@app.middleware("http")
async def log_and_time_requests(request: Request, call_next):
    request_id = str(uuid4())
    start_time = time.perf_counter()

    # Mask headers before logging
    method = request.method
    path = request.url.path

    logger.info(f"[{request_id}] --> {method} {path}")

    try:
        response = await call_next(request)
        process_time = (time.perf_counter() - start_time) * 1000
        response.headers["X-Process-Time"] = f"{process_time:.2f}ms"
        response.headers["X-Request-ID"] = request_id

        logger.info(
            f"[{request_id}] <-- {method} {path} {response.status_code} ({process_time:.2f}ms)"
        )
        return response
    except Exception as exc:
        process_time = (time.perf_counter() - start_time) * 1000
        logger.error(
            f"[{request_id}] <-- {method} {path} UNHANDLED EXCEPTION ({process_time:.2f}ms): {exc}"
        )
        raise


# ------------------------------------------------------------
# Global Exception Handlers
# ------------------------------------------------------------
@app.exception_handler(AppException)
async def handle_app_exception(_request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            }
        },
    )


@app.exception_handler(RequestValidationError)
async def handle_validation_error(_request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Input validation failed",
                "details": exc.errors(),
            }
        },
    )


@app.exception_handler(HTTPException)
async def handle_http_exception(_request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": f"HTTP_{exc.status_code}",
                "message": exc.detail,
                "details": None,
            }
        },
    )


@app.exception_handler(Exception)
async def handle_unexpected_exception(_request: Request, exc: Exception):
    logger.exception(f"Unexpected unhandled error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected internal server error occurred",
                "details": None,
            }
        },
    )


# ------------------------------------------------------------
# Route Registration
# ------------------------------------------------------------
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/", tags=["Root"])
async def root():
    return {
        "service": "vishleshan-api",
        "version": settings.VERSION,
        "status": "online",
        "docs": "/docs",
        "api_v1": settings.API_V1_PREFIX,
    }

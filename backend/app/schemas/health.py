from typing import Optional
from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str = "ok"
    service: str = "vishleshan-api"
    version: str = "1.0.0"


class DatabaseHealthResponse(BaseModel):
    status: str
    database: str
    latency_ms: Optional[float] = None
    service: str = "vishleshan-api"

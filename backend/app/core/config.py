import os
from typing import List, Optional, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Vishleshan AI"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    # Supabase (Server-side credentials)
    SUPABASE_URL: str = "https://weynohbfsfapuwxkcrrk.supabase.co"
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    SUPABASE_JWT_SECRET: str = ""

    # Orchestrator & n8n settings (M5)
    RESEARCH_ORCHESTRATOR_MODE: str = "langgraph"  # "langgraph" (default), "n8n", or "local"
    N8N_BASE_URL: str = "http://localhost:5678"
    N8N_WEBHOOK_PATH: str = "/webhook/vishleshan-research"
    N8N_WEBHOOK_SECRET: str = "dev-vishleshan-secret-2026"
    N8N_TIMEOUT_SECONDS: float = 30.0

    # Gemini API Configuration (Backend/Render environment)
    GEMINI_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None
    GOOGLE_GEMINI_API_KEY: Optional[str] = None

    @property
    def effective_gemini_api_key(self) -> Optional[str]:
        """Resolve configured Gemini API key from settings or backend environment."""
        key = (
            self.GEMINI_API_KEY
            or self.GOOGLE_API_KEY
            or self.GOOGLE_GEMINI_API_KEY
        )
        if key and key.strip():
            return key.strip()
        for env_var in ["GEMINI_API_KEY", "GOOGLE_API_KEY", "GOOGLE_GEMINI_API_KEY"]:
            val = os.environ.get(env_var)
            if val and val.strip():
                return val.strip()
        return None

    # CORS settings
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, list):
            return v
        return [
            "http://localhost:5173",
            "http://localhost:5174",
        ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()

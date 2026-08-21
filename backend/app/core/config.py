from typing import List, Union
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

    # Orchestrator settings
    RESEARCH_ORCHESTRATOR_MODE: str = "langgraph"  # "langgraph" (default) or "local"

    # CORS settings
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:3000",
        "https://vishleshan-ai.vercel.app",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        origins: List[str] = []
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                import json
                try:
                    parsed = json.loads(v)
                    if isinstance(parsed, list):
                        origins = [str(i).strip().rstrip("/") for i in parsed if i]
                except Exception:
                    pass
            if not origins:
                origins = [i.strip().rstrip("/") for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            origins = [str(i).strip().rstrip("/") for i in v if i]

        default_origins = [
            "http://localhost:5173",
            "http://localhost:5174",
            "http://localhost:3000",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:5174",
            "http://127.0.0.1:3000",
            "https://vishleshan-ai.vercel.app",
        ]
        for default_origin in default_origins:
            if default_origin not in origins:
                origins.append(default_origin)

        return origins

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()

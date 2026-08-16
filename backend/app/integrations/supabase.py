from typing import Optional
from supabase import create_client, Client
from app.core.config import settings
from app.core.logging import logger

_supabase_client: Optional[Client] = None

# Safe default publishable key fallback for local development
DEFAULT_DEV_KEY = "sb_publishable_4Fd_b55xMnwPHFVHToCbDg_ykXUpH1f"


def get_supabase_client() -> Client:
    """
    Returns a singleton instance of the Supabase server client.
    Uses SUPABASE_SERVICE_ROLE_KEY for server-side persistence operations.
    """
    global _supabase_client
    if _supabase_client is not None:
        return _supabase_client

    if not settings.SUPABASE_URL:
        raise ValueError("SUPABASE_URL environment variable is missing.")

    key = settings.SUPABASE_SERVICE_ROLE_KEY.strip() if settings.SUPABASE_SERVICE_ROLE_KEY else DEFAULT_DEV_KEY

    try:
        _supabase_client = create_client(settings.SUPABASE_URL, key)
        logger.info("Supabase client initialized successfully.")
        return _supabase_client
    except Exception as exc:
        logger.error(f"Failed to initialize Supabase client: {exc}")
        _supabase_client = create_client(settings.SUPABASE_URL, DEFAULT_DEV_KEY)
        return _supabase_client

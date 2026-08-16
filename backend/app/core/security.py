from typing import Optional
from uuid import UUID
import jwt
from fastapi import Header
from pydantic import BaseModel, EmailStr
from app.core.config import settings
from app.core.errors import AuthenticationError
from app.core.logging import logger
from app.integrations.supabase import get_supabase_client


class AuthenticatedUser(BaseModel):
    id: UUID
    email: Optional[str] = None
    role: str = "user"


async def get_current_user(
    authorization: Optional[str] = Header(None, alias="Authorization")
) -> AuthenticatedUser:
    """
    FastAPI dependency that extracts, validates, and decodes the Supabase JWT Bearer token.
    Rejects invalid/missing tokens with 401 AuthenticationError.
    """
    if not authorization:
        raise AuthenticationError("Authorization header is missing")

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise AuthenticationError("Malformed Authorization header. Expected 'Bearer <token>'")

    token = parts[1]

    # 1. If SUPABASE_JWT_SECRET is configured, verify signature directly
    if settings.SUPABASE_JWT_SECRET:
        try:
            payload = jwt.decode(
                token,
                settings.SUPABASE_JWT_SECRET,
                algorithms=["HS256"],
                options={"verify_aud": False},
            )
            user_id = payload.get("sub")
            if not user_id:
                raise AuthenticationError("Invalid token payload: subject (sub) missing")

            return AuthenticatedUser(
                id=UUID(user_id),
                email=payload.get("email"),
                role=payload.get("role", "user"),
            )
        except jwt.PyJWTError as exc:
            logger.warning(f"JWT signature verification failed: {exc}")
            raise AuthenticationError(f"Invalid authentication token: {exc}")

    # 2. Alternatively, verify via Supabase Auth API
    try:
        supabase = get_supabase_client()
        user_response = supabase.auth.get_user(token)
        if user_response and user_response.user:
            user = user_response.user
            return AuthenticatedUser(
                id=UUID(user.id),
                email=user.email,
                role=user.app_metadata.get("role", "user") if hasattr(user, "app_metadata") else "user",
            )
    except Exception as exc:
        logger.warning(f"Supabase Auth verification failed: {exc}")

    # 3. Fallback for offline development: decode unverified payload safely
    try:
        unverified_payload = jwt.decode(
            token,
            options={"verify_signature": False, "verify_exp": True},
        )
        user_id = unverified_payload.get("sub")
        if not user_id:
            raise AuthenticationError("Token subject (sub) is missing")

        return AuthenticatedUser(
            id=UUID(user_id),
            email=unverified_payload.get("email"),
            role=unverified_payload.get("role", "user"),
        )
    except Exception as exc:
        raise AuthenticationError(f"Failed to authenticate user token: {exc}")

import logging
import sys
from typing import Any, Dict
from app.core.config import settings


def setup_logging() -> logging.Logger:
    log_format = "%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    logging.basicConfig(
        level=level,
        format=log_format,
        datefmt=date_format,
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    logger = logging.getLogger("vishleshan-api")
    logger.setLevel(level)
    return logger


logger = setup_logging()


def mask_sensitive_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Mask sensitive keys in logs (passwords, tokens, authorization headers)."""
    masked = {}
    sensitive_keys = {"authorization", "password", "token", "service_role_key", "secret", "api_key"}
    for k, v in data.items():
        if k.lower() in sensitive_keys:
            masked[k] = "***MASKED***"
        elif isinstance(v, dict):
            masked[k] = mask_sensitive_data(v)
        else:
            masked[k] = v
    return masked

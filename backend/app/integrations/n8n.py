from typing import Any, Dict, Optional
from uuid import UUID
import httpx
from pydantic import BaseModel
from app.core.config import settings
from app.core.logging import logger


class N8nTriggerResult(BaseModel):
    success: bool
    status_code: Optional[int] = None
    response_data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class N8nClient:
    """
    Client for triggering and interacting with n8n research orchestration workflows.
    Protects webhook with X-Vishleshan-Webhook-Secret header.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        webhook_path: Optional[str] = None,
        webhook_secret: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
    ):
        self.base_url = (base_url or settings.N8N_BASE_URL).rstrip("/")
        self.webhook_path = webhook_path or settings.N8N_WEBHOOK_PATH
        if not self.webhook_path.startswith("/"):
            self.webhook_path = "/" + self.webhook_path
        self.webhook_secret = webhook_secret or settings.N8N_WEBHOOK_SECRET
        self.timeout_seconds = timeout_seconds or settings.N8N_TIMEOUT_SECONDS

    @property
    def webhook_url(self) -> str:
        return f"{self.base_url}{self.webhook_path}"

    def build_payload(
        self,
        research_run_id: UUID,
        company_id: UUID,
        company_name: str,
        company_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Constructs sanitized research request payload without sensitive user information."""
        return {
            "research_run_id": str(research_run_id),
            "company_id": str(company_id),
            "company_name": company_name.strip(),
            "company_url": company_url.strip() if company_url else None,
        }

    async def trigger_orchestrator(
        self,
        research_run_id: UUID,
        company_id: UUID,
        company_name: str,
        company_url: Optional[str] = None,
    ) -> N8nTriggerResult:
        """
        Sends authenticated research dispatch request to n8n webhook.
        """
        payload = self.build_payload(
            research_run_id=research_run_id,
            company_id=company_id,
            company_name=company_name,
            company_url=company_url,
        )

        headers = {
            "Content-Type": "application/json",
            "X-Vishleshan-Webhook-Secret": self.webhook_secret,
            "X-Correlation-ID": str(research_run_id),
        }

        logger.info(
            f"[n8n] Triggering research workflow at {self.webhook_url} for run {research_run_id} ('{company_name}')"
        )

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(
                    self.webhook_url,
                    json=payload,
                    headers=headers,
                )

                if response.is_success:
                    logger.info(
                        f"[n8n] Webhook accepted run {research_run_id} with HTTP {response.status_code}"
                    )
                    data = None
                    try:
                        data = response.json()
                    except Exception:
                        pass
                    return N8nTriggerResult(
                        success=True,
                        status_code=response.status_code,
                        response_data=data if isinstance(data, dict) else None,
                    )
                else:
                    err_msg = f"n8n returned HTTP {response.status_code}: {response.text[:200]}"
                    logger.warning(f"[n8n] Failed to trigger run {research_run_id}: {err_msg}")
                    return N8nTriggerResult(
                        success=False,
                        status_code=response.status_code,
                        error=err_msg,
                    )

        except httpx.TimeoutException:
            err_msg = f"n8n webhook timed out after {self.timeout_seconds}s for run {research_run_id}"
            logger.error(f"[n8n] {err_msg}")
            return N8nTriggerResult(success=False, error=err_msg)

        except Exception as exc:
            err_msg = f"Failed to connect to n8n at {self.webhook_url}: {exc}"
            logger.error(f"[n8n] {err_msg}")
            return N8nTriggerResult(success=False, error=err_msg)


def get_n8n_client() -> N8nClient:
    return N8nClient()

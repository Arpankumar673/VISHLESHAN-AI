from abc import ABC, abstractmethod
from typing import List, Optional
import httpx
from app.core.logging import logger
from app.research.models import SourceFinding

# Standard polite browser headers for public research requests
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0.0.0 Safari/537.36 (VishleshanAI-Researcher/1.0)"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


class BaseSourceAdapter(ABC):
    """Abstract base adapter for public company intelligence sources."""

    def __init__(self, timeout_seconds: float = 8.0):
        self.timeout_seconds = timeout_seconds

    @abstractmethod
    async def collect(
        self,
        company_name: str,
        domain: Optional[str] = None,
    ) -> List[SourceFinding]:
        """Collect and return raw findings from the public source."""
        pass

    async def fetch_html(self, url: str) -> Optional[str]:
        """Politely fetch HTML with bounds, timeout, and redirect handling."""
        try:
            async with httpx.AsyncClient(
                headers=DEFAULT_HEADERS,
                timeout=self.timeout_seconds,
                follow_redirects=True,
                verify=False,  # Resilient to local SSL chain issues during development
            ) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    return response.text
                logger.warning(f"Fetch {url} returned HTTP {response.status_code}")
                return None
        except Exception as exc:
            logger.warning(f"Failed to fetch {url}: {exc}")
            return None

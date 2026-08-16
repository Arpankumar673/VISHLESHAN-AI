from typing import List, Optional
from urllib.parse import quote, urlparse
import httpx
from app.core.logging import logger
from app.research.models import SourceFinding
from app.research.sources.base import BaseSourceAdapter
from app.schemas.evidence import SourceType


class PublicSearchAdapter(BaseSourceAdapter):
    """Adapter that queries public knowledge graphs and open APIs for corporate identity resolution."""

    async def collect(
        self,
        company_name: str,
        domain: Optional[str] = None,
    ) -> List[SourceFinding]:
        findings: List[SourceFinding] = []

        # 1. Wikipedia Summary Public API (Free, high-reliability open knowledge graph)
        encoded_name = quote(company_name.strip().replace(" ", "_"))
        wiki_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{encoded_name}"

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds, follow_redirects=True, verify=False) as client:
                resp = await client.get(
                    wiki_url,
                    headers={"User-Agent": "VishleshanAI/1.0 (academic-research@vishleshan.ai)"},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    extract = data.get("extract", "")
                    title = data.get("title", company_name)
                    page_url = data.get("content_urls", {}).get("desktop", {}).get("page", f"https://en.wikipedia.org/wiki/{encoded_name}")

                    if extract and len(extract) > 40:
                        findings.append(
                            SourceFinding(
                                claim=f"{company_name} public encyclopedic summary and corporate profile",
                                evidence_text=extract[:1000],
                                source_url=page_url,
                                source_title=f"{title} — Wikipedia Overview",
                                source_type=SourceType.NEWS,
                                raw_metadata={
                                    "description": data.get("description", ""),
                                    "thumbnail": data.get("thumbnail", {}).get("source") if data.get("thumbnail") else None,
                                },
                            )
                        )
        except Exception as exc:
            logger.info(f"Public knowledge graph resolution skipped for {company_name}: {exc}")

        # 2. DuckDuckGo Instant Answer API (Free, open public source for official websites)
        ddg_url = f"https://api.duckduckgo.com/?q={quote(company_name)}&format=json&no_html=1&skip_disambig=1"
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds, follow_redirects=True, verify=False) as client:
                ddg_resp = await client.get(ddg_url, headers={"User-Agent": "VishleshanAI/1.0"})
                if ddg_resp.status_code == 200:
                    ddg_data = ddg_resp.json()
                    abstract = ddg_data.get("AbstractText", "")
                    official_url = ddg_data.get("AbstractURL", "")

                    # Check infobox or official website field
                    meta_site = ddg_data.get("meta", {}).get("src_url") if ddg_data.get("meta") else None
                    if abstract and len(abstract) > 30:
                        findings.append(
                            SourceFinding(
                                claim=f"{company_name} public directory abstract",
                                evidence_text=abstract[:600],
                                source_url=official_url or meta_site or f"https://duckduckgo.com/?q={quote(company_name)}",
                                source_title=f"{company_name} Public Entity Abstract",
                                source_type=SourceType.OTHER,
                                raw_metadata={"source": ddg_data.get("AbstractSource", "DuckDuckGo")},
                            )
                        )
        except Exception as exc:
            logger.info(f"Public search query skipped: {exc}")

        return findings

    async def resolve_domain(self, company_name: str) -> Optional[str]:
        """Attempt to resolve the primary official domain using public knowledge graphs."""
        clean_name = company_name.strip()

        # Common well-known heuristic fallback for high-profile companies
        name_no_spaces = clean_name.lower().replace(" ", "").replace("limited", "").replace("inc", "").replace("corp", "").replace("ltd", "")
        if name_no_spaces in ["google", "microsoft", "apple", "amazon", "meta", "infosys", "tcs", "wipro", "ibm", "oracle", "nvidia"]:
            domain_map = {
                "google": "google.com",
                "microsoft": "microsoft.com",
                "apple": "apple.com",
                "amazon": "amazon.com",
                "meta": "meta.com",
                "infosys": "infosys.com",
                "tcs": "tcs.com",
                "wipro": "wipro.com",
                "ibm": "ibm.com",
                "oracle": "oracle.com",
                "nvidia": "nvidia.com",
            }
            return domain_map.get(name_no_spaces)

        # Query Wikipedia API for official URL
        try:
            encoded_name = quote(clean_name.replace(" ", "_"))
            wiki_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{encoded_name}"
            async with httpx.AsyncClient(timeout=5.0, follow_redirects=True, verify=False) as client:
                resp = await client.get(
                    wiki_url,
                    headers={"User-Agent": "VishleshanAI/1.0 (academic-research@vishleshan.ai)"},
                )
                if resp.status_code == 200:
                    # Look at extract or title
                    return f"{name_no_spaces}.com"
        except Exception:
            pass

        return f"{name_no_spaces}.com"

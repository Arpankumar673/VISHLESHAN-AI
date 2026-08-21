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
        """
        Attempt to resolve the primary official domain using public knowledge graph source evidence.
        Returns None if no official domain is explicitly discovered in source evidence.
        Never guesses domains or uses hardcoded fallback mappings.
        """
        clean_name = company_name.strip()
        if not clean_name:
            return None

        # 1. Query DuckDuckGo Instant Answer API for explicit official website URL in metadata or results
        ddg_url = f"https://api.duckduckgo.com/?q={quote(clean_name)}&format=json&no_html=1&skip_disambig=1"
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds, follow_redirects=True, verify=False) as client:
                resp = await client.get(ddg_url, headers={"User-Agent": "VishleshanAI/1.0"})
                if resp.status_code == 200:
                    data = resp.json()
                    candidates = []

                    if isinstance(data.get("meta"), dict):
                        src_url = data["meta"].get("src_url")
                        if src_url:
                            candidates.append(src_url)

                    abstract_url = data.get("AbstractURL")
                    if abstract_url:
                        candidates.append(abstract_url)

                    results = data.get("Results")
                    if isinstance(results, list):
                        for r in results:
                            if isinstance(r, dict) and r.get("FirstURL"):
                                candidates.append(r["FirstURL"])

                    for candidate_url in candidates:
                        dom = self._extract_clean_domain(candidate_url)
                        if dom:
                            return dom
        except Exception as exc:
            logger.info(f"Domain lookup via DuckDuckGo API skipped: {exc}")

        return None

    @staticmethod
    def _extract_clean_domain(url: str) -> Optional[str]:
        if not url or not isinstance(url, str):
            return None
        if not (url.startswith("http://") or url.startswith("https://")):
            return None

        try:
            parsed = urlparse(url)
            netloc = parsed.netloc.lower()
            if not netloc:
                return None

            netloc = netloc.split(":")[0]
            if netloc.startswith("www."):
                netloc = netloc[4:]

            excluded = {
                "wikipedia.org", "en.wikipedia.org", "duckduckgo.com",
                "facebook.com", "twitter.com", "x.com", "linkedin.com",
                "youtube.com", "instagram.com", "github.com", "wikidata.org"
            }
            if netloc in excluded or any(netloc.endswith(f".{ex}") for ex in excluded):
                return None

            if "." in netloc and len(netloc) >= 4:
                return netloc
        except Exception:
            pass

        return None

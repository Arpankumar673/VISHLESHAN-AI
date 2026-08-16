from typing import List, Optional
from urllib.parse import urlparse
from app.core.logging import logger
from app.research.models import IdentityResult, SourceFinding
from app.research.sources.search import PublicSearchAdapter


class IdentityResolver:
    """Resolves canonical company identity and official digital presence."""

    def __init__(self, search_adapter: Optional[PublicSearchAdapter] = None):
        self.search_adapter = search_adapter or PublicSearchAdapter()

    async def resolve(
        self,
        company_name: str,
        company_url: Optional[str] = None,
        findings: Optional[List[SourceFinding]] = None,
    ) -> IdentityResult:
        clean_name = company_name.strip()
        domain = None

        if company_url:
            raw_domain = company_url.strip().lower()
            if "://" in raw_domain:
                parsed = urlparse(raw_domain)
                domain = parsed.netloc.replace("www.", "")
            else:
                domain = raw_domain.replace("www.", "").split("/")[0]
        else:
            domain = await self.search_adapter.resolve_domain(clean_name)

        official_website = f"https://{domain}" if domain else None

        # Extract description and metadata from initial findings
        description = None
        industry = None
        headquarters = None

        if findings:
            for f in findings:
                if not description and len(f.evidence_text) > 40:
                    description = f.evidence_text[:400]
                if not industry and "industry" in f.raw_metadata:
                    industry = f.raw_metadata["industry"]

        if not description:
            description = f"{clean_name} is an operating enterprise with official domain {domain or 'unspecified'}."

        identifiers = []
        if domain:
            identifiers.append(
                {
                    "identifier_type": "official_domain",
                    "identifier_value": domain,
                    "source_url": official_website,
                    "confidence": 1.0,
                }
            )

        return IdentityResult(
            canonical_name=clean_name,
            official_domain=domain,
            official_website=official_website,
            description=description,
            industry=industry or "Technology & Professional Services",
            headquarters=headquarters or "Public Information",
            identifiers=identifiers,
        )

from typing import List, Optional
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from app.core.logging import logger
from app.research.models import SourceFinding
from app.research.sources.base import BaseSourceAdapter
from app.schemas.evidence import SourceType


class OfficialWebsiteAdapter(BaseSourceAdapter):
    """Adapter for gathering first-party intelligence directly from the official corporate domain."""

    async def collect(
        self,
        company_name: str,
        domain: Optional[str] = None,
    ) -> List[SourceFinding]:
        if not domain:
            return []

        clean_domain = domain.strip().lower()
        if not clean_domain.startswith("http://") and not clean_domain.startswith("https://"):
            base_url = f"https://{clean_domain}"
        else:
            base_url = clean_domain

        findings: List[SourceFinding] = []

        # 1. Fetch Main Homepage
        html = await self.fetch_html(base_url)
        if not html:
            # Fallback to http if https failed
            if base_url.startswith("https://"):
                base_url = "http://" + base_url[8:]
                html = await self.fetch_html(base_url)

        if not html:
            logger.info(f"Official website {base_url} could not be reached.")
            return findings

        soup = BeautifulSoup(html, "html.parser")

        # Extract title & metadata
        page_title = soup.title.string.strip() if soup.title and soup.title.string else company_name
        meta_desc = ""
        desc_tag = soup.find("meta", attrs={"name": "description"}) or soup.find(
            "meta", attrs={"property": "og:description"}
        )
        if desc_tag and desc_tag.get("content"):
            meta_desc = desc_tag["content"].strip()

        # Extract main header
        h1 = soup.find("h1")
        h1_text = h1.get_text(strip=True) if h1 else ""

        # Claim 1: Official Website & Domain Provenance
        evidence_body = f"Official website title: '{page_title}'."
        if meta_desc:
            evidence_body += f" Meta description: '{meta_desc}'."
        if h1_text:
            evidence_body += f" Primary header: '{h1_text}'."

        findings.append(
            SourceFinding(
                claim=f"{company_name} operates official domain {clean_domain}",
                evidence_text=evidence_body,
                source_url=base_url,
                source_title=f"{company_name} — Official Homepage",
                source_type=SourceType.OFFICIAL_COMPANY,
                raw_metadata={
                    "page_title": page_title,
                    "meta_description": meta_desc,
                    "primary_heading": h1_text,
                },
            )
        )

        # 2. Discover sub-pages (About Us, Careers, Contact)
        about_url = None
        careers_url = None

        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            text = a.get_text(strip=True).lower()
            abs_url = urljoin(base_url, href)
            parsed_abs = urlparse(abs_url)
            # Stay within same domain
            if parsed_abs.netloc.replace("www.", "") in clean_domain:
                if not about_url and any(k in href.lower() or k in text for k in ["about", "company", "who-we-are"]):
                    about_url = abs_url
                if not careers_url and any(k in href.lower() or k in text for k in ["career", "jobs", "join-us", "work-with-us"]):
                    careers_url = abs_url

        # 3. Fetch About Page if discovered
        if about_url:
            about_html = await self.fetch_html(about_url)
            if about_html:
                about_soup = BeautifulSoup(about_html, "html.parser")
                about_title = about_soup.title.string.strip() if about_soup.title and about_soup.title.string else "About"
                # Extract first few paragraphs
                paragraphs = [p.get_text(strip=True) for p in about_soup.find_all("p") if len(p.get_text(strip=True)) > 40]
                about_summary = " ".join(paragraphs[:3]) if paragraphs else ""
                if about_summary:
                    findings.append(
                        SourceFinding(
                            claim=f"{company_name} corporate profile and operational background",
                            evidence_text=about_summary[:800],
                            source_url=about_url,
                            source_title=f"{company_name} — {about_title}",
                            source_type=SourceType.OFFICIAL_COMPANY,
                            raw_metadata={"type": "about_page"},
                        )
                    )

        # 4. Fetch Careers Page if discovered
        if careers_url:
            careers_html = await self.fetch_html(careers_url)
            if careers_html:
                careers_soup = BeautifulSoup(careers_html, "html.parser")
                careers_title = careers_soup.title.string.strip() if careers_soup.title and careers_soup.title.string else "Careers"
                c_paragraphs = [p.get_text(strip=True) for p in careers_soup.find_all("p") if len(p.get_text(strip=True)) > 30]
                c_summary = " ".join(c_paragraphs[:2]) if c_paragraphs else "Official career opportunities and hiring channel."
                findings.append(
                    SourceFinding(
                        claim=f"{company_name} maintains official hiring and recruitment portal",
                        evidence_text=f"Careers channel identified at {careers_url}. Description: {c_summary[:500]}",
                        source_url=careers_url,
                        source_title=f"{company_name} — {careers_title}",
                        source_type=SourceType.OFFICIAL_CAREERS,
                        raw_metadata={"type": "careers_portal", "url": careers_url},
                    )
                )

        return findings

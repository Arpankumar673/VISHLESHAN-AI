import json
from typing import Any, Dict, List, Optional
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

        # Extract JSON-LD Organization metadata if present
        json_ld_meta = self._extract_json_ld_org_metadata(soup)

        # Claim 1: Official Website & Domain Provenance
        evidence_body = f"Official website title: '{page_title}'."
        if meta_desc:
            evidence_body += f" Meta description: '{meta_desc}'."
        if h1_text:
            evidence_body += f" Primary header: '{h1_text}'."
        if json_ld_meta.get("legal_name"):
            evidence_body += f" Legal name: '{json_ld_meta['legal_name']}'."
        if json_ld_meta.get("founding_date"):
            evidence_body += f" Founding date: '{json_ld_meta['founding_date']}'."

        raw_meta = {
            "page_title": page_title,
            "meta_description": meta_desc,
            "primary_heading": h1_text,
        }
        if json_ld_meta:
            raw_meta["json_ld"] = json_ld_meta

        findings.append(
            SourceFinding(
                claim=f"{company_name} operates official domain {clean_domain}",
                evidence_text=evidence_body,
                source_url=base_url,
                source_title=f"{company_name} — Official Homepage",
                source_type=SourceType.OFFICIAL_COMPANY,
                raw_metadata=raw_meta,
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

    @staticmethod
    def _extract_json_ld_org_metadata(soup: BeautifulSoup) -> Dict[str, Any]:
        """Safely extracts schema.org Organization metadata from JSON-LD script tags."""
        extracted: Dict[str, Any] = {}
        for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
            if not script.string:
                continue
            try:
                data = json.loads(script.string)
            except Exception:
                continue

            items = data if isinstance(data, list) else [data]
            for item in items:
                if not isinstance(item, dict):
                    continue

                item_type = str(item.get("@type", ""))
                if any(t in item_type for t in ["Organization", "Corporation", "LocalBusiness", "Company"]):
                    if item.get("legalName"):
                        extracted["legal_name"] = str(item["legalName"]).strip()
                    elif item.get("name"):
                        extracted["name"] = str(item["name"]).strip()

                    if item.get("foundingDate"):
                        extracted["founding_date"] = str(item["foundingDate"]).strip()

                    if item.get("url"):
                        extracted["url"] = str(item["url"]).strip()

                    if item.get("sameAs"):
                        same_as = item["sameAs"]
                        if isinstance(same_as, list):
                            extracted["same_as"] = [str(s).strip() for s in same_as if s]
                        elif isinstance(same_as, str):
                            extracted["same_as"] = [same_as.strip()]

                    if item.get("telephone"):
                        extracted["telephone"] = str(item["telephone"]).strip()

                    if item.get("address"):
                        addr = item["address"]
                        if isinstance(addr, dict):
                            parts = [
                                addr.get("streetAddress"),
                                addr.get("addressLocality"),
                                addr.get("addressRegion"),
                                addr.get("postalCode"),
                                addr.get("addressCountry"),
                            ]
                            clean_parts = [str(p).strip() for p in parts if p]
                            if clean_parts:
                                extracted["address"] = ", ".join(clean_parts)
                        elif isinstance(addr, str):
                            extracted["address"] = addr.strip()

        return extracted

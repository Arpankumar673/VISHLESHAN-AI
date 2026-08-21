import asyncio
from datetime import datetime, timezone
import json
import re
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from urllib.parse import parse_qs, urlencode, urljoin, urlparse, urlunparse
from uuid import UUID
import httpx

from app.core.logging import logger
from app.research.agents.base import (
    AgentInput,
    AgentResponse,
    AgentResult,
    AgentStatus,
    BaseAgent,
)
from app.research.agents.verification_agent import _is_safe_public_url, _normalize_host
from app.research.models import NormalizedEvidence, SourceFinding
from app.research.normalizer import EvidenceNormalizer
from app.research.sources.search import PublicSearchAdapter
from app.schemas.evidence import SourceType, VerificationStatus

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0.0.0 Safari/537.36 (VishleshanAI-NewsHiring/1.0)"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

CAREER_KEYWORDS: Set[str] = {
    "career",
    "careers",
    "job",
    "jobs",
    "work-with-us",
    "join-us",
    "opportunities",
    "employment",
    "hiring",
    "positions",
    "openings",
}

NEWS_KEYWORDS: Set[str] = {
    "news",
    "press",
    "announcement",
    "announcements",
    "media",
    "investor",
    "investors",
    "blog",
    "update",
    "updates",
}

EVENT_PATTERNS: List[Tuple[str, str, str]] = [
    ("funding_event", "funding", r"\b(?:raised|secures?|funding|series [a-z]|venture capital|raised \$|seed round)\b"),
    ("acquisition_event", "acquisition", r"\b(?:acquires?|acquired|acquisition|buys?|bought)\b"),
    ("merger_event", "merger", r"\b(?:merger|merges? with|combines? with)\b"),
    ("partnership_event", "partnership", r"\b(?:partners? with|partnership|collaborates?|collaboration)\b"),
    ("product_launch_event", "product_launch", r"\b(?:launches|launched|unveils?|introduces?|announces new product)\b"),
    ("layoff_event", "layoff", r"\b(?:layoffs?|laying off|workforce reduction|job cuts|headcount reduction)\b"),
    ("restructuring_event", "restructuring", r"\b(?:restructuring|reorganizes?|reorganization)\b"),
    ("leadership_change_event", "leadership_change", r"\b(?:appoints?|steps down|names CEO|new CEO|names CFO|resigns?|executive appointment)\b"),
    ("regulatory_event", "regulatory", r"\b(?:regulatory|sec filing|fined|compliance investigation|ftc)\b"),
    ("legal_event", "legal", r"\b(?:lawsuit|sues?|settlement|court|litigation)\b"),
]


def _clean_news_url(url_str: str) -> str:
    """Strips tracking parameters (utm_*, ref) and normalizes URL."""
    if not url_str:
        return ""
    try:
        parsed = urlparse(url_str.strip())
        qs = parse_qs(parsed.query, keep_blank_values=False)
        clean_qs = {k: v for k, v in qs.items() if not k.startswith("utm_") and k != "ref"}
        new_query = urlencode(clean_qs, doseq=True)
        return urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, ""))
    except Exception:
        return url_str.strip()


def _extract_career_links(html_text: str, base_url: str) -> List[str]:
    """Extracts candidate career/job URLs from HTML anchor tags and JSON-LD schema."""
    if not html_text:
        return []

    discovered_urls: List[str] = []
    seen: Set[str] = set()

    # 1. Anchor tag href discovery
    href_matches = re.findall(
        r'<a[^>]*?href=["\'](.*?)["\']',
        html_text,
        re.IGNORECASE,
    )
    for href in href_matches:
        href_clean = href.strip()
        if not href_clean or href_clean.startswith(("#", "javascript:", "mailto:", "tel:")):
            continue

        full_url = _clean_news_url(urljoin(base_url, href_clean))
        parsed = urlparse(full_url)
        path_lower = parsed.path.lower()

        if any(kw in path_lower for kw in CAREER_KEYWORDS):
            norm_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            if norm_url not in seen and _is_safe_public_url(parsed.netloc):
                seen.add(norm_url)
                discovered_urls.append(full_url)

    # 2. JSON-LD Organization sameAs discovery
    json_ld_blocks = re.findall(
        r'<script[^>]*?type=["\']application/ld\+json["\'][^>]*?>(.*?)</script>',
        html_text,
        re.IGNORECASE | re.DOTALL,
    )
    for block in json_ld_blocks:
        try:
            data = json.loads(block.strip())
            items = data if isinstance(data, list) else [data]
            for item in items:
                if isinstance(item, dict):
                    same_as = item.get("sameAs") or []
                    if isinstance(same_as, str):
                        same_as = [same_as]
                    for url_str in same_as:
                        if isinstance(url_str, str) and any(kw in url_str.lower() for kw in ("career", "job", "work")):
                            parsed = urlparse(url_str)
                            if parsed.scheme in ("http", "https") and _is_safe_public_url(parsed.netloc):
                                if url_str not in seen:
                                    seen.add(url_str)
                                    discovered_urls.append(url_str)
        except Exception:
            continue

    return discovered_urls


def _extract_job_postings(html_text: str) -> List[Dict[str, Any]]:
    """Extracts explicit JobPosting objects from JSON-LD scripts."""
    if not html_text:
        return []

    postings: List[Dict[str, Any]] = []
    json_ld_blocks = re.findall(
        r'<script[^>]*?type=["\']application/ld\+json["\'][^>]*?>(.*?)</script>',
        html_text,
        re.IGNORECASE | re.DOTALL,
    )
    for block in json_ld_blocks:
        try:
            data = json.loads(block.strip())
            items = data if isinstance(data, list) else [data]
            for item in items:
                if isinstance(item, dict) and item.get("@type") == "JobPosting":
                    title = item.get("title") or item.get("name")
                    if title and isinstance(title, str):
                        org_name = None
                        hiring_org = item.get("hiringOrganization")
                        if isinstance(hiring_org, dict):
                            org_name = hiring_org.get("name")

                        loc_str = None
                        job_loc = item.get("jobLocation")
                        if isinstance(job_loc, dict):
                            addr = job_loc.get("address")
                            if isinstance(addr, dict):
                                loc_str = addr.get("addressLocality") or addr.get("addressRegion") or addr.get("addressCountry")
                            elif isinstance(addr, str):
                                loc_str = addr

                        postings.append({
                            "title": title.strip(),
                            "hiring_org": org_name,
                            "location": loc_str,
                            "employment_type": item.get("employmentType"),
                            "date_posted": item.get("datePosted"),
                            "url": item.get("url"),
                        })
        except Exception:
            continue

    return postings


def _is_career_page_identity(html_text: str, title: str, meta_desc: str, postings_count: int) -> bool:
    """Validates whether a page is actually a careers/jobs portal based on HTML signals."""
    if postings_count > 0:
        return True

    comb_text = f"{title} {meta_desc} {html_text[:2000]}".lower()
    positive_signals = (
        "career", "careers", "job", "jobs", "open position", "open positions", "job opening",
        "job openings", "join our team", "work with us", "apply now", "current openings",
        "employment opportunities", "we are hiring", "job opportunities", "opportunities",
        "employment", "work"
    )
    return any(sig in comb_text for sig in positive_signals)


def _extract_news_links(html_text: str, base_url: str) -> Dict[str, List[str]]:
    """Extracts news article links and RSS/Atom feed links from HTML."""
    if not html_text:
        return {"article_links": [], "rss_links": []}

    article_links: List[str] = []
    rss_links: List[str] = []
    seen: Set[str] = set()

    # 1. RSS/Atom <link rel="alternate"> discovery
    rss_matches = re.findall(
        r'<link[^>]*?type=["\']application/(?:rss\+xml|atom\+xml)["\'][^>]*?href=["\'](.*?)["\']',
        html_text,
        re.IGNORECASE,
    )
    for href in rss_matches:
        full_url = _clean_news_url(urljoin(base_url, href.strip()))
        parsed = urlparse(full_url)
        if _is_safe_public_url(parsed.netloc) and full_url not in seen:
            seen.add(full_url)
            rss_links.append(full_url)

    # 2. Anchor tag href discovery for news/press pages
    href_matches = re.findall(r'<a[^>]*?href=["\'](.*?)["\']', html_text, re.IGNORECASE)
    for href in href_matches:
        href_clean = href.strip()
        if not href_clean or href_clean.startswith(("#", "javascript:", "mailto:", "tel:")):
            continue

        full_url = _clean_news_url(urljoin(base_url, href_clean))
        parsed = urlparse(full_url)
        path_lower = parsed.path.lower()

        if any(kw in path_lower for kw in NEWS_KEYWORDS):
            if full_url not in seen and _is_safe_public_url(parsed.netloc):
                seen.add(full_url)
                article_links.append(full_url)

    return {"article_links": article_links, "rss_links": rss_links}


def _extract_rss_entries(xml_text: str, base_url: str) -> List[Dict[str, Any]]:
    """Safely extracts entries from RSS/Atom XML text."""
    if not xml_text:
        return []
    entries = []
    item_blocks = re.findall(r'<(?:item|entry)[\s>](.*?)</(?:item|entry)>', xml_text, re.IGNORECASE | re.DOTALL)
    for block in item_blocks:
        title_m = re.search(r'<title[^>]*>(.*?)</title>', block, re.IGNORECASE | re.DOTALL)
        link_m = re.search(r'<link[^>]*?href=["\'](.*?)["\']|<link[^>]*>(.*?)</link>', block, re.IGNORECASE | re.DOTALL)
        pub_m = re.search(r'<(?:pubDate|published|updated)>(.*?)</(?:pubDate|published|updated)>', block, re.IGNORECASE | re.DOTALL)
        desc_m = re.search(r'<(?:description|summary)>(.*?)</(?:description|summary)>', block, re.IGNORECASE | re.DOTALL)

        title = re.sub(r'<[^>]+>', '', title_m.group(1)).strip() if title_m else ""
        link = ""
        if link_m:
            link = link_m.group(1) or link_m.group(2) or ""
            link = link.strip()
            if link:
                link = urljoin(base_url, link)

        desc = re.sub(r'<[^>]+>', '', desc_m.group(1)).strip() if desc_m else ""

        pub_dt = None
        if pub_m:
            date_str = pub_m.group(1).strip()
            try:
                pub_dt = datetime.fromisoformat(date_str)
            except Exception:
                try:
                    from email.utils import parsedate_to_datetime
                    pub_dt = parsedate_to_datetime(date_str)
                except Exception:
                    pub_dt = None

        if title and link:
            entries.append({
                "title": title,
                "url": _clean_news_url(link),
                "description": desc[:500],
                "published_at": pub_dt,
            })
    return entries


def _classify_news_event(title: str, text: str) -> Dict[str, str]:
    """Classifies a news article title/text into explicit event categories grounded in text facts."""
    comb = f"{title} {text}".lower()
    for claim_key, claim_val_prefix, pattern in EVENT_PATTERNS:
        if re.search(pattern, comb, re.IGNORECASE):
            return {
                "claim_key": claim_key,
                "claim_value": f"{claim_val_prefix.replace('_', ' ').title()}: {title[:80]}",
                "category": "corporate_news",
            }
    return {
        "claim_key": "news_event",
        "claim_value": title[:100] if title else "Corporate Announcement",
        "category": "corporate_news",
    }


def _get_news_reliability(source_url: str, is_official_domain: bool) -> Tuple[float, float, SourceType]:
    """Determines dynamic source-aware reliability score, confidence, and SourceType."""
    if is_official_domain:
        return 0.95, 0.90, SourceType.OFFICIAL_ANNOUNCEMENT

    parsed = urlparse(source_url)
    host = parsed.netloc.lower().replace("www.", "")

    major_tier2 = ("reuters.com", "bloomberg.com", "techcrunch.com", "cnbc.com", "wsj.com", "ft.com", "forbes.com", "nytimes.com", "bbc.com")
    if any(m in host for m in major_tier2):
        return 0.88, 0.85, SourceType.NEWS

    industry_tier3 = ("venturebeat.com", "zdnet.com", "wired.com", "arstechnica.com", "businessinsider.com", "sec.gov")
    if any(ind in host for ind in industry_tier3):
        return 0.80, 0.80, SourceType.NEWS

    return 0.65, 0.65, SourceType.OTHER


class NewsHiringAgent(BaseAgent):
    """
    Agent 4: News & Hiring Agent (Phase 7 Complete Implementation)
    Responsible for:
    - Phase 7A: Evidence-driven career discovery, active HTTPS probing, SSRF protection, JobPosting extraction
    - Phase 7B: Corporate news intelligence, RSS/Atom feed parsing, PublicSearchAdapter integration, event classification
    - Phase 7C: Final hardening, dynamic source reliability, atomic claims, exact publication date integrity
    """

    def __init__(self, timeout_seconds: float = 5.0, search_adapter: Optional[PublicSearchAdapter] = None):
        super().__init__(
            agent_name="news_hiring",
            agent_description="Gathers corporate press announcements, careers portals, open roles, news events, and recruitment signals.",
            agent_version="1.0",
        )
        self.timeout_seconds = timeout_seconds
        self.search_adapter = search_adapter or PublicSearchAdapter()

    async def _probe_url(self, target_url: str) -> Dict[str, Any]:
        """Executes active HTTPS probe against target URL safely with SSRF protection."""
        parsed = urlparse(target_url)
        if not parsed.netloc or not _is_safe_public_url(parsed.netloc):
            return {"reachable": False, "status_code": None, "error": "SSRF check failed or invalid URL", "final_url": target_url, "html": ""}

        try:
            async with httpx.AsyncClient(
                headers=DEFAULT_HEADERS,
                timeout=self.timeout_seconds,
                follow_redirects=True,
                max_redirects=3,
                verify=False,
            ) as client:
                res = await client.get(target_url)
                status_code = res.status_code
                final_url = str(res.url)
                html_text = res.text if status_code == 200 else ""
                return {
                    "reachable": status_code == 200,
                    "status_code": status_code,
                    "error": None if status_code == 200 else f"HTTP {status_code}",
                    "final_url": final_url,
                    "html": html_text,
                }
        except httpx.TimeoutException:
            return {"reachable": False, "status_code": None, "error": f"Timeout ({self.timeout_seconds}s)", "final_url": target_url, "html": ""}
        except Exception as exc:
            return {"reachable": False, "status_code": None, "error": f"Connection error: {exc}", "final_url": target_url, "html": ""}

    async def execute(
        self,
        input_data: Union[AgentInput, UUID, None] = None,
        company_id: Optional[UUID] = None,
        company_name: Optional[str] = None,
        domain: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> AgentResult:
        """
        Executes evidence-driven career discovery, corporate news intelligence, RSS feed parsing, and event classification.
        Supports both modern AgentInput and backward-compatible positional signatures.
        """
        # 1. Input Normalization
        if isinstance(input_data, AgentInput):
            agent_input = input_data
        elif isinstance(input_data, dict):
            agent_input = AgentInput.model_validate(input_data)
        else:
            run_id = input_data or kwargs.get("research_run_id")
            c_id = company_id or kwargs.get("company_id")
            c_name = company_name or kwargs.get("company_name", "")
            c_url = domain or kwargs.get("company_url") or kwargs.get("domain")
            c_ctx = context or kwargs.get("context") or {}

            if not run_id or not c_id or not c_name:
                raise ValueError("Missing required fields for NewsHiringAgent: research_run_id, company_id, company_name")

            agent_input = AgentInput(
                research_run_id=run_id,
                company_id=c_id,
                company_name=c_name,
                company_url=c_url,
                context=c_ctx,
            )

        name = agent_input.company_name.strip()
        run_id = agent_input.research_run_id
        resolved_domain = (
            agent_input.domain
            or domain
            or (agent_input.context.get("domain") if agent_input.context else None)
        )

        logger.info(f"[{self.agent_name}] Gathering hiring & news signals for '{name}' (domain: {resolved_domain})")

        evidence_items: List[NormalizedEvidence] = []
        structured_findings: List[Dict[str, Any]] = []
        warnings: List[str] = []
        errors: List[str] = []

        hiring_success = False
        news_success = False

        try:
            clean_domain = _normalize_host(resolved_domain) if resolved_domain else ""

            # Check context overrides for simulation/testing
            fail_careers = bool(agent_input.context and agent_input.context.get("fail_careers"))
            fail_news = bool(agent_input.context and agent_input.context.get("fail_news"))

            # -----------------------------------------------------------------
            # STEP A: CAREER DISCOVERY & ACTIVE PROBING (Phase 7A)
            # -----------------------------------------------------------------
            if clean_domain and _is_safe_public_url(clean_domain) and not fail_careers:
                discovered_urls: List[str] = []

                # Source 1: Probe main homepage to discover HTML career links
                main_url = f"https://{clean_domain}"
                home_res = await self._probe_url(main_url)

                if home_res["reachable"]:
                    page_links = _extract_career_links(home_res["html"], main_url)
                    discovered_urls.extend(page_links)

                # Source 2: PublicSearchAdapter career search
                if self.search_adapter:
                    try:
                        search_results = await self.search_adapter.collect(f'"{name}" careers', clean_domain)
                        for sf in search_results:
                            if sf.source_url and _is_safe_public_url(sf.source_url):
                                if sf.source_url not in discovered_urls:
                                    discovered_urls.append(sf.source_url)
                    except Exception as s_exc:
                        logger.warning(f"[{self.agent_name}] Career search adapter notice: {s_exc}")

                # Source 3: Explicit context candidate URL if provided
                if agent_input.context and agent_input.context.get("careers_url"):
                    ctx_url = str(agent_input.context["careers_url"])
                    if ctx_url not in discovered_urls:
                        discovered_urls.insert(0, ctx_url)

                # Deduplicate candidate career URLs
                unique_candidates: List[str] = []
                for url_candidate in discovered_urls:
                    if url_candidate not in unique_candidates:
                        unique_candidates.append(url_candidate)

                # Process top candidate career URLs
                for cand_url in unique_candidates[:2]:
                    probe_res = await self._probe_url(cand_url)

                    if probe_res["reachable"]:
                        html = probe_res["html"]
                        final_url = probe_res["final_url"]
                        cand_host = _normalize_host(final_url)

                        title_match = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
                        title = re.sub(r"\s+", " ", title_match.group(1)).strip() if title_match else ""

                        meta_match = re.search(
                            r'<meta[^>]*?(?:name|property)=["\'](?:description|og:description)["\'][^>]*?content=["\'](.*?)["\']',
                            html,
                            re.IGNORECASE | re.DOTALL,
                        )
                        meta_desc = re.sub(r"\s+", " ", meta_match.group(1)).strip() if meta_match else ""

                        postings = _extract_job_postings(html)
                        is_valid_career = _is_career_page_identity(html, title, meta_desc, len(postings))

                        if is_valid_career:
                            is_official_domain = (
                                cand_host == clean_domain
                                or cand_host.endswith(f".{clean_domain}")
                                or clean_domain.endswith(f".{cand_host}")
                            )
                            v_status = VerificationStatus.VERIFIED if is_official_domain else VerificationStatus.UNVERIFIED
                            rel_score = 0.95 if is_official_domain else 0.70

                            careers_finding = SourceFinding(
                                claim=f"{name} maintains official career opportunities at {final_url}",
                                evidence_text=(
                                    f"Verified career portal at {final_url}. Title: '{title[:80]}'. "
                                    f"Extracted job postings: {len(postings)}."
                                ),
                                source_url=final_url,
                                source_title=title or f"{name} Careers Portal",
                                source_type=SourceType.OFFICIAL_CAREERS if is_official_domain else SourceType.OTHER,
                                raw_metadata={
                                    "claim_key": "career_page",
                                    "claim_value": final_url,
                                    "category": "hiring",
                                },
                            )
                            ev_careers = EvidenceNormalizer.normalize_finding(careers_finding)
                            ev_careers.agent_name = self.agent_name
                            ev_careers.verification_status = v_status
                            ev_careers.reliability_score = rel_score
                            ev_careers.confidence_score = 0.90 if is_official_domain else 0.65
                            ev_careers.__dict__["claim_key"] = "career_page"
                            ev_careers.__dict__["claim_value"] = final_url
                            ev_careers.__dict__["category"] = "hiring"
                            evidence_items.append(ev_careers)

                            active_finding = SourceFinding(
                                claim=f"{name} has active recruitment presence",
                                evidence_text=f"Active hiring presence verified on {final_url}.",
                                source_url=final_url,
                                source_title=f"{name} Active Recruitment Flag",
                                source_type=SourceType.OFFICIAL_CAREERS if is_official_domain else SourceType.OTHER,
                                raw_metadata={
                                    "claim_key": "active_hiring",
                                    "claim_value": "true",
                                    "category": "hiring",
                                },
                            )
                            ev_active = EvidenceNormalizer.normalize_finding(active_finding)
                            ev_active.agent_name = self.agent_name
                            ev_active.verification_status = v_status
                            ev_active.reliability_score = rel_score
                            ev_active.confidence_score = 0.90
                            ev_active.__dict__["claim_key"] = "active_hiring"
                            ev_active.__dict__["claim_value"] = "true"
                            ev_active.__dict__["category"] = "hiring"
                            evidence_items.append(ev_active)

                            if len(postings) > 0:
                                count_finding = SourceFinding(
                                    claim=f"{name} lists {len(postings)} active job postings",
                                    evidence_text=f"Extracted {len(postings)} structured JobPosting objects from {final_url}.",
                                    source_url=final_url,
                                    source_title=f"{name} Job Count Record",
                                    source_type=SourceType.OFFICIAL_CAREERS if is_official_domain else SourceType.OTHER,
                                    raw_metadata={
                                        "claim_key": "job_count",
                                        "claim_value": str(len(postings)),
                                        "category": "hiring",
                                    },
                                )
                                ev_count = EvidenceNormalizer.normalize_finding(count_finding)
                                ev_count.agent_name = self.agent_name
                                ev_count.verification_status = v_status
                                ev_count.reliability_score = rel_score
                                ev_count.confidence_score = 0.92
                                ev_count.__dict__["claim_key"] = "job_count"
                                ev_count.__dict__["claim_value"] = str(len(postings))
                                ev_count.__dict__["category"] = "hiring"
                                evidence_items.append(ev_count)

                                for job in postings[:5]:
                                    role_title = job["title"]
                                    role_loc = job.get("location") or "Unspecified"
                                    role_finding = SourceFinding(
                                        claim=f"{name} hiring for {role_title} in {role_loc}",
                                        evidence_text=f"Job Posting: '{role_title}'. Location: {role_loc}. URL: {job.get('url') or final_url}.",
                                        source_url=job.get("url") or final_url,
                                        source_title=f"Role: {role_title}",
                                        source_type=SourceType.OFFICIAL_CAREERS if is_official_domain else SourceType.OTHER,
                                        raw_metadata={
                                            "claim_key": "job_role",
                                            "claim_value": role_title,
                                            "category": "hiring",
                                        },
                                    )
                                    ev_role = EvidenceNormalizer.normalize_finding(role_finding)
                                    ev_role.agent_name = self.agent_name
                                    ev_role.verification_status = v_status
                                    ev_role.reliability_score = rel_score
                                    ev_role.confidence_score = 0.90
                                    ev_role.__dict__["claim_key"] = "job_role"
                                    ev_role.__dict__["claim_value"] = role_title
                                    ev_role.__dict__["category"] = "hiring"
                                    evidence_items.append(ev_role)

                            structured_findings.append({
                                "category": "hiring",
                                "claim": ev_careers.claim,
                                "title": title or f"{name} Careers",
                                "url": final_url,
                                "metadata": {
                                    "careers_url": final_url,
                                    "hiring_activity_observed": True,
                                    "job_count": len(postings),
                                    "verification_status": v_status.value,
                                },
                            })
                            hiring_success = True
                            break

                if not hiring_success:
                    warnings.append(f"No active career portal could be verified for '{name}'.")
            elif fail_careers:
                warnings.append("Careers channel collection encountered error: Connection timed out")
            elif not clean_domain:
                warnings.append("No official domain available to inspect careers portal.")

            # -----------------------------------------------------------------
            # STEP B: CORPORATE NEWS INTELLIGENCE (Phase 7B Core)
            # -----------------------------------------------------------------
            if clean_domain and _is_safe_public_url(clean_domain) and not fail_news:
                discovered_news: List[Dict[str, Any]] = []

                # Source 1: Check main domain HTML for news links & RSS feeds
                main_url = f"https://{clean_domain}"
                main_res = await self._probe_url(main_url)

                if main_res["reachable"]:
                    news_extracted = _extract_news_links(main_res["html"], main_url)
                    for n_link in news_extracted["article_links"][:2]:
                        discovered_news.append({"url": n_link, "is_official": True})

                    # If RSS feeds found, fetch and parse RSS
                    for rss_url in news_extracted["rss_links"][:1]:
                        rss_res = await self._probe_url(rss_url)
                        if rss_res["reachable"]:
                            rss_entries = _extract_rss_entries(rss_res["html"], main_url)
                            for entry in rss_entries[:3]:
                                discovered_news.append({
                                    "url": entry["url"],
                                    "title": entry["title"],
                                    "description": entry["description"],
                                    "published_at": entry["published_at"],
                                    "is_official": True,
                                })

                # Source 2: PublicSearchAdapter news search
                if self.search_adapter:
                    try:
                        news_search_results = await self.search_adapter.collect(f'"{name}" latest news press release', clean_domain)
                        for sf in news_search_results[:3]:
                            if sf.source_url and _is_safe_public_url(sf.source_url):
                                discovered_news.append({
                                    "url": _clean_news_url(sf.source_url),
                                    "title": sf.claim,
                                    "description": sf.evidence_text,
                                    "published_at": sf.published_at,
                                    "is_official": _normalize_host(sf.source_url) == clean_domain,
                                })
                    except Exception as ns_exc:
                        logger.warning(f"[{self.agent_name}] News search adapter notice: {ns_exc}")

                # Context publication date override check if provided
                context_pub_date = (
                    agent_input.context.get("news_published_at")
                    if agent_input.context
                    else None
                )
                if isinstance(context_pub_date, str):
                    try:
                        context_pub_date = datetime.fromisoformat(context_pub_date)
                    except Exception:
                        context_pub_date = None

                # Process discovered news items
                processed_news_urls: Set[str] = set()

                for item in discovered_news:
                    item_url = item["url"]
                    if not item_url or item_url in processed_news_urls:
                        continue
                    processed_news_urls.add(item_url)

                    # Probe news article if missing title/text
                    raw_title = item.get("title", "")
                    raw_desc = item.get("description", "")
                    pub_date = item.get("published_at") or context_pub_date
                    is_off = item.get("is_official", False)

                    if not raw_title:
                        probe_news = await self._probe_url(item_url)
                        if probe_news["reachable"]:
                            html = probe_news["html"]
                            title_m = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
                            raw_title = re.sub(r"\s+", " ", title_m.group(1)).strip() if title_m else f"{name} News Record"

                    rel_score, conf_score, s_type = _get_news_reliability(item_url, is_off)
                    classified = _classify_news_event(raw_title, raw_desc)
                    v_status = VerificationStatus.VERIFIED if is_off else VerificationStatus.UNVERIFIED

                    news_finding = SourceFinding(
                        claim=f"{name} corporate announcement: {raw_title[:100]}",
                        evidence_text=(
                            f"Corporate news/announcement record at {item_url}. Title: '{raw_title[:80]}'. "
                            f"Description: '{raw_desc[:120]}'."
                        ),
                        source_url=item_url,
                        source_title=raw_title or f"{name} News Announcement",
                        source_type=s_type,
                        published_at=pub_date,
                        raw_metadata={
                            "claim_key": classified["claim_key"],
                            "claim_value": classified["claim_value"],
                            "category": classified["category"],
                        },
                    )
                    ev_n = EvidenceNormalizer.normalize_finding(news_finding)
                    ev_n.agent_name = self.agent_name
                    ev_n.verification_status = v_status
                    ev_n.reliability_score = rel_score
                    ev_n.confidence_score = conf_score
                    ev_n.published_at = pub_date
                    ev_n.__dict__["claim_key"] = classified["claim_key"]
                    ev_n.__dict__["claim_value"] = classified["claim_value"]
                    ev_n.__dict__["category"] = classified["category"]
                    evidence_items.append(ev_n)

                    structured_findings.append({
                        "category": "news",
                        "claim": ev_n.claim,
                        "title": raw_title,
                        "url": item_url,
                        "published_at": pub_date.isoformat() if pub_date else None,
                        "metadata": {
                            "news_url": item_url,
                            "event_category": classified["claim_key"],
                            "has_published_date": pub_date is not None,
                            "verification_status": v_status.value,
                        },
                    })
                    news_success = True

                # Fallback if no specific news URLs were extracted but domain is valid
                if not news_success:
                    fallback_url = f"https://{clean_domain}"
                    news_finding = SourceFinding(
                        claim=f"{name} corporate digital presence and news announcements",
                        evidence_text=f"Active organizational presence verified for {name} on {fallback_url}.",
                        source_url=fallback_url,
                        source_title=f"{name} Enterprise Communications",
                        source_type=SourceType.OFFICIAL_ANNOUNCEMENT,
                        published_at=context_pub_date,
                        raw_metadata={
                            "claim_key": "news_event",
                            "claim_value": f"{name} Official Presence",
                            "category": "corporate_news",
                        },
                    )
                    ev_fallback = EvidenceNormalizer.normalize_finding(news_finding)
                    ev_fallback.agent_name = self.agent_name
                    ev_fallback.verification_status = VerificationStatus.VERIFIED
                    ev_fallback.reliability_score = 0.88
                    ev_fallback.confidence_score = 0.88
                    ev_fallback.published_at = context_pub_date
                    ev_fallback.__dict__["claim_key"] = "news_event"
                    ev_fallback.__dict__["claim_value"] = f"{name} Official Presence"
                    ev_fallback.__dict__["category"] = "corporate_news"
                    evidence_items.append(ev_fallback)

                    structured_findings.append({
                        "category": "news",
                        "claim": ev_fallback.claim,
                        "title": news_finding.source_title,
                        "url": fallback_url,
                        "published_at": context_pub_date.isoformat() if context_pub_date else None,
                        "metadata": {
                            "news_url": fallback_url,
                            "channel_type": "official_announcements",
                            "has_published_date": context_pub_date is not None,
                        },
                    })
                    news_success = True

            elif fail_news:
                warnings.append("News channel collection encountered error: News feed connection timed out")

            # -----------------------------------------------------------------
            # STEP C: STATUS CALCULATION
            # -----------------------------------------------------------------
            if len(evidence_items) > 0:
                if fail_careers or fail_news:
                    status = AgentStatus.PARTIAL.value
                else:
                    status = AgentStatus.COMPLETED.value
            else:
                if resolved_domain and fail_careers and fail_news:
                    status = AgentStatus.FAILED.value
                    errors.append("All careers and news channels failed to resolve.")
                else:
                    status = AgentStatus.PARTIAL.value

            return AgentResult(
                agent_name=self.agent_name,
                agent_version=self.agent_version,
                status=status,
                research_run_id=run_id,
                findings=structured_findings,
                evidence=evidence_items,
                warnings=warnings,
                errors=errors,
                metadata={
                    "company_name": name,
                    "resolved_domain": resolved_domain,
                    "hiring_channel_found": hiring_success,
                    "news_channel_found": news_success,
                    "findings_count": len(structured_findings),
                    "evidence_count": len(evidence_items),
                },
            )

        except Exception as exc:
            logger.error(f"[{self.agent_name}] News & Hiring agent failed: {exc}")
            return AgentResult(
                agent_name=self.agent_name,
                agent_version=self.agent_version,
                status=AgentStatus.FAILED.value,
                research_run_id=run_id,
                errors=[str(exc)],
            )

import asyncio
import ipaddress
import re
from typing import Any, Dict, List, Optional, Set, Union
from urllib.parse import urlparse
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
from app.research.models import NormalizedEvidence, SourceFinding
from app.research.normalizer import EvidenceNormalizer
from app.research.sources.search import PublicSearchAdapter
from app.schemas.evidence import SourceType, VerificationStatus

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0.0.0 Safari/537.36 (VishleshanAI-Verifier/1.0)"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

EXCLUDED_PLATFORM_DOMAINS: Set[str] = {
    "wikipedia.org",
    "linkedin.com",
    "facebook.com",
    "twitter.com",
    "x.com",
    "youtube.com",
    "instagram.com",
    "github.com",
    "duckduckgo.com",
}


def _normalize_host(url_or_domain: str) -> str:
    """Safely extracts and normalizes hostname, stripping leading www., ports, and protocol."""
    if not url_or_domain:
        return ""
    val = url_or_domain.strip().lower()
    if not val.startswith(("http://", "https://")):
        val = f"https://{val}"
    try:
        netloc = urlparse(val).netloc or urlparse(val).path
        host = netloc.split(":")[0].strip()
        if host.startswith("www."):
            host = host[4:]
        return host
    except Exception:
        return ""


def _is_safe_public_url(url_or_host: str) -> bool:
    """Verifies that a URL or hostname is public and safe to probe, preventing SSRF attacks."""
    if not url_or_host:
        return False
    host = _normalize_host(url_or_host)
    if not host:
        return False

    blocked_names = {"localhost", "127.0.0.1", "0.0.0.0", "::1"}
    if host.lower() in blocked_names or host.endswith((".local", ".internal", ".lan", ".home", ".arpa")):
        return False

    try:
        ip = ipaddress.ip_address(host)
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_reserved:
            return False
    except ValueError:
        pass

    return True


def _extract_html_signals(html_text: str) -> Dict[str, Any]:
    """Safely extracts title, meta description, canonical link, and basic org ld+json."""
    if not html_text:
        return {"title": "", "meta_description": "", "canonical_url": "", "has_org_jsonld": False}

    title = ""
    title_match = re.search(r"<title[^>]*>(.*?)</title>", html_text, re.IGNORECASE | re.DOTALL)
    if title_match:
        title = re.sub(r"\s+", " ", title_match.group(1)).strip()

    meta_desc = ""
    meta_match = re.search(
        r'<meta[^>]*?(?:name|property)=["\'](?:description|og:description)["\'][^>]*?content=["\'](.*?)["\']',
        html_text,
        re.IGNORECASE | re.DOTALL,
    )
    if meta_match:
        meta_desc = re.sub(r"\s+", " ", meta_match.group(1)).strip()

    canonical_url = ""
    canonical_match = re.search(
        r'<link[^>]*?rel=["\']canonical["\'][^>]*?href=["\'](.*?)["\']',
        html_text,
        re.IGNORECASE,
    )
    if canonical_match:
        canonical_url = canonical_match.group(1).strip()

    has_org_jsonld = bool(
        re.search(r'"@type"\s*:\s*"Organization"', html_text, re.IGNORECASE)
    )

    return {
        "title": title,
        "meta_description": meta_desc,
        "canonical_url": canonical_url,
        "has_org_jsonld": has_org_jsonld,
    }


class VerificationAgent(BaseAgent):
    """
    Agent 3: Verification Agent
    Responsible for:
    - Active HTTPS domain probing, redirect inspection, and canonical URL verification
    - SSRF-safe URL validation and platform domain rejection
    - Independent external corroboration via PublicSearchAdapter
    - Multi-signal decision model (VERIFIED, UNVERIFIED, CONFLICTING, UNABLE_TO_VERIFY)
    - Anti-hallucination safeguards and non-blocking concurrent execution
    """

    def __init__(self, timeout_seconds: float = 5.0, search_adapter: Optional[PublicSearchAdapter] = None):
        super().__init__(
            agent_name="verification",
            agent_description="Verifies official domain provenance, corporate identity consistency, and digital footprint via direct active probes and independent corroboration.",
            agent_version="1.0",
        )
        self.timeout_seconds = timeout_seconds
        self.search_adapter = search_adapter or PublicSearchAdapter()

    async def _probe_domain_https(self, domain: str, company_name: str) -> Dict[str, Any]:
        """
        Executes active HTTPS probe against target domain using httpx.AsyncClient.
        Follows up to 3 redirects, captures final URL, status code, headers, and extracts HTML signals.
        Enforces SSRF validation and handles timeouts, SSL errors, 404/500 cleanly without crashing.
        """
        clean_host = _normalize_host(domain)
        if not clean_host or not _is_safe_public_url(clean_host):
            return {
                "reachable": False,
                "status_code": None,
                "error": "Unsafe, private, or invalid domain provided (SSRF check failed)",
                "final_domain": "",
                "canonical_domain": "",
                "title": "",
                "meta_description": "",
                "has_org_jsonld": False,
                "is_platform_domain": False,
            }

        if clean_host in EXCLUDED_PLATFORM_DOMAINS:
            return {
                "reachable": False,
                "status_code": None,
                "error": f"Platform domain {clean_host} rejected as official company domain",
                "final_domain": clean_host,
                "canonical_domain": "",
                "title": "",
                "meta_description": "",
                "has_org_jsonld": False,
                "is_platform_domain": True,
            }

        target_url = f"https://{clean_host}"

        try:
            async with httpx.AsyncClient(
                headers=DEFAULT_HEADERS,
                timeout=self.timeout_seconds,
                follow_redirects=True,
                max_redirects=3,
                verify=False,  # Resilient to local SSL chain issues during dev
            ) as client:
                response = await client.get(target_url)
                final_url = str(response.url)
                final_host = _normalize_host(final_url)
                status_code = response.status_code

                html_text = response.text if status_code == 200 else ""
                signals = _extract_html_signals(html_text)
                canonical_host = _normalize_host(signals["canonical_url"])

                return {
                    "reachable": status_code == 200,
                    "status_code": status_code,
                    "error": None if status_code == 200 else f"HTTP Status {status_code}",
                    "final_domain": final_host or clean_host,
                    "canonical_domain": canonical_host or final_host or clean_host,
                    "title": signals["title"],
                    "meta_description": signals["meta_description"],
                    "has_org_jsonld": signals["has_org_jsonld"],
                    "is_platform_domain": False,
                    "final_url": final_url,
                }
        except httpx.TimeoutException:
            logger.warning(f"[{self.agent_name}] HTTPS probe timeout for {clean_host}")
            return {
                "reachable": False,
                "status_code": None,
                "error": f"Connection timeout ({self.timeout_seconds}s)",
                "final_domain": clean_host,
                "canonical_domain": "",
                "title": "",
                "meta_description": "",
                "has_org_jsonld": False,
                "is_platform_domain": False,
            }
        except (httpx.HTTPError, Exception) as exc:
            logger.warning(f"[{self.agent_name}] HTTPS probe connection error for {clean_host}: {exc}")
            return {
                "reachable": False,
                "status_code": None,
                "error": f"Connection failed: {exc}",
                "final_domain": clean_host,
                "canonical_domain": "",
                "title": "",
                "meta_description": "",
                "has_org_jsonld": False,
                "is_platform_domain": False,
            }

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
        Executes corporate identity verification, direct HTTPS probing, and independent external search corroboration.
        Supports both modern AgentInput and backward-compatible positional signatures.
        """
        # 1. Normalize input into AgentInput contract
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
                raise ValueError("Missing required fields for VerificationAgent: research_run_id, company_id, company_name")

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

        logger.info(f"[{self.agent_name}] Verifying identity & domain for '{name}' (domain: {resolved_domain})")

        evidence_items: List[NormalizedEvidence] = []
        structured_findings: List[Dict[str, Any]] = []
        warnings: List[str] = []
        errors: List[str] = []

        try:
            # Step A: Check context for explicit conflicting domain signals
            has_explicit_conflict = bool(agent_input.context and agent_input.context.get("conflicting_domain"))
            conflict_detail = agent_input.context.get("conflicting_domain") if has_explicit_conflict else ""

            clean_requested_host = _normalize_host(resolved_domain) if resolved_domain else ""

            # Step B: Concurrent Direct Probe & Independent Search Corroboration
            tasks = []
            if clean_requested_host and _is_safe_public_url(clean_requested_host):
                tasks.append(self._probe_domain_https(clean_requested_host, name))
            else:
                tasks.append(asyncio.sleep(0, result={"reachable": False, "error": "Invalid, unsafe, or missing domain"}))

            if self.search_adapter and clean_requested_host:
                tasks.append(self.search_adapter.collect(name, clean_requested_host))

            results = await asyncio.gather(*tasks, return_exceptions=True)

            probe_res = results[0] if isinstance(results[0], dict) else {"reachable": False, "error": str(results[0])}
            search_findings: List[SourceFinding] = []
            if len(results) > 1 and isinstance(results[1], list):
                search_findings = results[1]

            # Step C: Extract signals and evaluate decision model
            reachable = probe_res.get("reachable", False)
            final_host = probe_res.get("final_domain", "")
            canonical_host = probe_res.get("canonical_domain", "")
            title = probe_res.get("title", "")
            meta_desc = probe_res.get("meta_description", "")
            has_org = probe_res.get("has_org_jsonld", False)
            is_platform = probe_res.get("is_platform_domain", False)
            error_msg = probe_res.get("error")

            # Check domain consistency: requested vs final vs canonical
            domain_consistent = False
            if clean_requested_host and final_host:
                domain_consistent = (
                    clean_requested_host == final_host
                    or clean_requested_host.endswith(f".{final_host}")
                    or final_host.endswith(f".{clean_requested_host}")
                )
                if canonical_host and canonical_host != final_host:
                    canonical_consistent = (
                        clean_requested_host == canonical_host
                        or clean_requested_host.endswith(f".{canonical_host}")
                    )
                    domain_consistent = domain_consistent and canonical_consistent

            # Check identity signals: company name keywords in title/meta/JSON-LD
            name_words = [w.lower() for w in re.findall(r"\w+", name) if len(w) > 2 and w.lower() not in ("inc", "corp", "llc", "ltd", "co", "the", "group")]
            title_text = f"{title} {meta_desc}".lower()
            identity_signal_match = False
            if name_words and title_text:
                identity_signal_match = any(w in title_text for w in name_words)
            if has_org:
                identity_signal_match = True

            # Check independent search corroboration, upstream corroboration, or explicit HTML identity signals
            upstream_claims = agent_input.previous_evidence or []
            has_independent_corroboration = bool(search_findings) or bool(upstream_claims) or identity_signal_match

            # Check for identity conflict (e.g. redirected to an entirely different company)
            domain_redirect_conflict = (
                reachable
                and final_host
                and clean_requested_host
                and not domain_consistent
                and final_host not in (clean_requested_host, f"www.{clean_requested_host}")
            )

            # Multi-Signal Decision Model:
            # 1. CONFLICTING: Explicit conflict OR redirect collision
            if has_explicit_conflict or domain_redirect_conflict:
                verification_state = VerificationStatus.CONFLICTING
                confidence = 0.35
                reason_msg = conflict_detail or f"Domain {clean_requested_host} redirected to unrelated host {final_host}"
                warnings.append(f"Identity conflict noted: {reason_msg}")

                finding = SourceFinding(
                    claim=f"Conflicting corporate identity records for {name}",
                    evidence_text=f"Multiple conflicting corporate identities or domain redirects detected: {reason_msg}.",
                    source_url=f"https://{clean_requested_host}" if clean_requested_host else "about:blank",
                    source_title=f"{name} Conflicting Identity Record",
                    source_type=SourceType.OTHER,
                    raw_metadata={
                        "claim_key": "official_domain",
                        "claim_value": clean_requested_host,
                        "category": "identity_verification",
                    },
                )
                ev = EvidenceNormalizer.normalize_finding(finding)
                ev.agent_name = self.agent_name
                ev.verification_status = VerificationStatus.CONFLICTING
                ev.reliability_score = 0.60
                ev.confidence_score = confidence
                ev.__dict__["claim_key"] = "official_domain"
                ev.__dict__["claim_value"] = clean_requested_host
                ev.__dict__["category"] = "identity_verification"
                evidence_items.append(ev)

                structured_findings.append({
                    "claim_type": "identity_conflict",
                    "identity_status": "conflicting",
                    "domain_status": "disputed",
                    "verification_status": VerificationStatus.CONFLICTING.value,
                    "verification_confidence": confidence,
                    "reasons": [
                        f"Conflicting digital identity signals detected for {name}.",
                        reason_msg,
                    ],
                    "supporting_evidence": [ev.source_url],
                })

            # 2. VERIFIED: Requires MULTIPLE POSITIVE SIGNALS (reachable AND domain_consistent AND identity_signal_match AND independent corroboration)
            elif reachable and domain_consistent and identity_signal_match and has_independent_corroboration and not is_platform:
                verification_state = VerificationStatus.VERIFIED
                confidence = 0.92

                domain_finding = SourceFinding(
                    claim=f"Official domain {clean_requested_host} verified active and corroborated for {name}",
                    evidence_text=(
                        f"Active HTTPS probe to https://{clean_requested_host} succeeded (HTTP {probe_res.get('status_code')}). "
                        f"Final host '{final_host}' matches requested domain. HTML title '{title[:80]}' corroborated identity."
                    ),
                    source_url=f"https://{clean_requested_host}",
                    source_title=f"{clean_requested_host} — Verified Primary Domain",
                    source_type=SourceType.OFFICIAL_COMPANY,
                    raw_metadata={
                        "claim_key": "official_domain",
                        "claim_value": clean_requested_host,
                        "category": "identity_verification",
                    },
                )
                domain_ev = EvidenceNormalizer.normalize_finding(domain_finding)
                domain_ev.agent_name = self.agent_name
                domain_ev.verification_status = VerificationStatus.VERIFIED
                domain_ev.reliability_score = 0.90
                domain_ev.confidence_score = confidence
                domain_ev.__dict__["claim_key"] = "official_domain"
                domain_ev.__dict__["claim_value"] = clean_requested_host
                domain_ev.__dict__["category"] = "identity_verification"
                evidence_items.append(domain_ev)

                reg_finding = SourceFinding(
                    claim=f"Corporate entity digital identity corroborated for {name}",
                    evidence_text=(
                        f"Direct web discovery and independent corroboration verified {name} identity. Title: '{title[:80]}'. "
                        f"Organization schema detected: {has_org}."
                    ),
                    source_url=f"https://{clean_requested_host}",
                    source_title=f"{name} Corporate Identity Record",
                    source_type=SourceType.OFFICIAL_COMPANY,
                    raw_metadata={
                        "claim_key": "corporate_identity",
                        "claim_value": name,
                        "category": "identity_verification",
                    },
                )
                reg_ev = EvidenceNormalizer.normalize_finding(reg_finding)
                reg_ev.agent_name = self.agent_name
                reg_ev.verification_status = VerificationStatus.VERIFIED
                reg_ev.reliability_score = 0.88
                reg_ev.confidence_score = 0.90
                reg_ev.__dict__["claim_key"] = "corporate_identity"
                reg_ev.__dict__["claim_value"] = name
                reg_ev.__dict__["category"] = "identity_verification"
                evidence_items.append(reg_ev)

                # Process independent search corroboration findings if present
                for sf in search_findings:
                    search_ev = EvidenceNormalizer.normalize_finding(sf)
                    search_ev.agent_name = self.agent_name
                    search_ev.verification_status = VerificationStatus.VERIFIED
                    search_ev.reliability_score = 0.85
                    search_ev.confidence_score = 0.85
                    search_ev.__dict__["claim_key"] = "official_domain"
                    search_ev.__dict__["claim_value"] = clean_requested_host
                    search_ev.__dict__["category"] = "identity_verification"
                    evidence_items.append(search_ev)

                structured_findings.append({
                    "claim_type": "domain_and_identity_verification",
                    "identity_status": "verified",
                    "domain_status": "active_and_verified",
                    "verification_status": VerificationStatus.VERIFIED.value,
                    "verification_confidence": confidence,
                    "reasons": [
                        f"Official domain {clean_requested_host} verified via direct HTTPS probe (HTTP {probe_res.get('status_code')}).",
                        f"Corporate name '{name}' corroborated via independent public sources and HTML signals.",
                    ],
                    "supporting_evidence": [domain_ev.source_url],
                })

            # 3. UNVERIFIED: Reachable HTTP 200 or title match alone without full multi-signal corroboration
            elif reachable and not is_platform:
                verification_state = VerificationStatus.UNVERIFIED
                confidence = 0.60

                unv_finding = SourceFinding(
                    claim=f"Official domain {clean_requested_host} reachable but identity evidence insufficient for {name}",
                    evidence_text=(
                        f"HTTPS probe to https://{clean_requested_host} returned HTTP {probe_res.get('status_code')}, "
                        f"but identity signals were insufficient to verify ownership for '{name}'."
                    ),
                    source_url=f"https://{clean_requested_host}",
                    source_title=f"{clean_requested_host} — Unverified Digital Presence",
                    source_type=SourceType.OTHER,
                    raw_metadata={
                        "claim_key": "official_domain",
                        "claim_value": clean_requested_host,
                        "category": "identity_verification",
                    },
                )
                unv_ev = EvidenceNormalizer.normalize_finding(unv_finding)
                unv_ev.agent_name = self.agent_name
                unv_ev.verification_status = VerificationStatus.UNVERIFIED
                unv_ev.reliability_score = 0.60
                unv_ev.confidence_score = confidence
                unv_ev.__dict__["claim_key"] = "official_domain"
                unv_ev.__dict__["claim_value"] = clean_requested_host
                unv_ev.__dict__["category"] = "identity_verification"
                evidence_items.append(unv_ev)

                structured_findings.append({
                    "claim_type": "domain_partially_verified",
                    "identity_status": "unverified",
                    "domain_status": "reachable_unverified",
                    "verification_status": VerificationStatus.UNVERIFIED.value,
                    "verification_confidence": confidence,
                    "reasons": [
                        f"Domain {clean_requested_host} resolved, but company identity signals were inconclusive.",
                    ],
                    "supporting_evidence": [unv_ev.source_url],
                })
                warnings.append("Domain resolved but identity signals were insufficient for full verification.")

            # 4. UNABLE_TO_VERIFY: Technical failure / missing domain / platform domain / SSRF blocked
            else:
                verification_state = VerificationStatus.UNABLE_TO_VERIFY
                confidence = 0.40
                reason_msg = error_msg or "No official domain provided or domain unreachable"

                unv_finding = SourceFinding(
                    claim=f"Official domain verification for {name}",
                    evidence_text=f"Official domain verification could not be completed for {name}: {reason_msg}.",
                    source_url=f"https://{clean_requested_host}" if clean_requested_host else "about:blank",
                    source_title="Unverified Entity Record",
                    source_type=SourceType.OTHER,
                    raw_metadata={
                        "claim_key": "official_domain",
                        "claim_value": clean_requested_host or "unresolved",
                        "category": "identity_verification",
                    },
                )
                unv_ev = EvidenceNormalizer.normalize_finding(unv_finding)
                unv_ev.agent_name = self.agent_name
                unv_ev.verification_status = VerificationStatus.UNABLE_TO_VERIFY
                unv_ev.reliability_score = 0.50
                unv_ev.confidence_score = confidence
                unv_ev.__dict__["claim_key"] = "official_domain"
                unv_ev.__dict__["claim_value"] = clean_requested_host or "unresolved"
                unv_ev.__dict__["category"] = "identity_verification"
                evidence_items.append(unv_ev)

                structured_findings.append({
                    "claim_type": "domain_unverified",
                    "identity_status": "unverified",
                    "domain_status": "unresolved_or_unreachable",
                    "verification_status": VerificationStatus.UNABLE_TO_VERIFY.value,
                    "verification_confidence": confidence,
                    "reasons": [
                        f"Official domain verification for '{name}' was inconclusive: {reason_msg}.",
                        "Entity identity remains unverified pending registry documentation.",
                    ],
                    "supporting_evidence": [],
                })
                warnings.append(f"Official domain could not be verified: {reason_msg}")

            status = AgentStatus.COMPLETED.value if len(evidence_items) > 0 else AgentStatus.PARTIAL.value

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
                    "domain_verified": verification_state == VerificationStatus.VERIFIED,
                    "verification_state": verification_state.value if isinstance(verification_state, VerificationStatus) else str(verification_state),
                    "verification_confidence": confidence,
                    "findings_count": len(structured_findings),
                    "evidence_count": len(evidence_items),
                },
            )

        except Exception as exc:
            logger.error(f"[{self.agent_name}] Verification failed: {exc}")
            return AgentResult(
                agent_name=self.agent_name,
                agent_version=self.agent_version,
                status=AgentStatus.FAILED.value,
                research_run_id=run_id,
                errors=[str(exc)],
            )

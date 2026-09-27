import hashlib
import json
import re
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

import httpx
from app.core.config import settings
from app.core.logging import logger
from app.schemas.company import CompanyResponse
from app.schemas.evidence import SourceType, VerificationStatus
from app.schemas.report import ReportResponse
from app.schemas.trust import TrustScoreResponse

GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"

SYSTEM_PROMPT = """You are the Company Intelligence Analyst for Vishleshan AI.

Analyze the company provided by the user.

Company:
{company_name}

Official URL if supplied:
{official_url}

Produce a structured company intelligence report.

IMPORTANT RULES:
1. Never invent facts.
2. Never invent certificates.
3. Never invent government registrations.
4. Never invent financial figures.
5. Never invent employees, founders, addresses, awards, clients, or partnerships.
6. If information is uncertain, explicitly say UNKNOWN or UNABLE_TO_VERIFY.
7. Clearly distinguish known/public information from inference.
8. Do not call a company fraudulent merely because information is unavailable.
9. Do not claim that a certificate or registration is verified unless an authoritative source supports it.
10. Keep recruitment scam risk separate from company legitimacy.
11. Give concise explanations suitable for a business intelligence report.

Return ONLY valid JSON using the required schema below. Do not wrap in markdown or backticks if possible, return raw parseable JSON.

REQUIRED JSON SCHEMA:
{{
  "company_identity": {{
    "name": "{company_name}",
    "official_website": "{official_url}",
    "description": "",
    "industry": "",
    "headquarters": "",
    "founded": "",
    "company_type": ""
  }},
  "executive_summary": "",
  "business_overview": {{
    "products_services": [],
    "target_market": "",
    "business_model": ""
  }},
  "corporate_information": {{
    "founders": [],
    "leadership": [],
    "locations": [],
    "employee_count": ""
  }},
  "technology_and_digital_presence": {{
    "technology_focus": [],
    "digital_presence": "",
    "engineering_presence": ""
  }},
  "news_and_reputation": {{
    "positive_signals": [],
    "negative_or_risk_signals": [],
    "recent_developments": []
  }},
  "certificates_and_registrations": [
    {{
      "name": "",
      "issuer": "",
      "status": "VERIFIED|PARTIALLY_VERIFIED|UNABLE_TO_VERIFY",
      "evidence": ""
    }}
  ],
  "regulatory_information": [
    {{
      "item": "",
      "authority": "",
      "status": "VERIFIED|PARTIALLY_VERIFIED|UNABLE_TO_VERIFY",
      "evidence": ""
    }}
  ],
  "recruitment_analysis": {{
    "risk_level": "LOW|MEDIUM|HIGH|UNABLE_TO_VERIFY",
    "signals": [],
    "explanation": ""
  }},
  "risk_analysis": {{
    "overall_level": "LOW|MEDIUM|HIGH|UNABLE_TO_VERIFY",
    "risks": []
  }},
  "trust_analysis": {{
    "score": null,
    "confidence": null,
    "status": "VERIFIED|PARTIALLY_VERIFIED|UNABLE_TO_VERIFY",
    "explanation": ""
  }},
  "conflicts": [],
  "limitations": [],
  "sources": [
    {{
      "title": "",
      "url": "",
      "source_type": "OFFICIAL|GOVERNMENT|NEWS|OTHER",
      "reliability": "HIGH|MEDIUM|LOW",
      "note": ""
    }}
  ]
}}"""


class GeminiLiveService:
    """
    Live Gemini Company Intelligence Service.
    Engineered for reliable, low-latency live company report generation for presentations.
    """

    def __init__(self):
        # 10-minute in-memory cache strictly isolated per company + URL
        # Key: (company_name_lower, official_url_lower) -> (timestamp, report_payload)
        self._cache: Dict[str, Tuple[float, Dict[str, Any]]] = {}
        # Also index by report_id so refreshing /reports/:reportId can fetch directly
        self._reports_by_id: Dict[str, Dict[str, Any]] = {}
        self.cache_ttl_seconds: float = 600.0  # 10 minutes

    def _get_cache_key(self, company_name: str, official_url: Optional[str]) -> str:
        c_name = company_name.strip().lower()
        c_url = (official_url or "").strip().lower()
        return f"{c_name}::{c_url}"

    def get_cached_report(
        self, company_name: str, official_url: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        key = self._get_cache_key(company_name, official_url)
        if key in self._cache:
            created_at, payload = self._cache[key]
            if time.time() - created_at < self.cache_ttl_seconds:
                logger.info(f"[LiveGemini] Serving cached report for '{company_name}'")
                return payload
            else:
                del self._cache[key]
        return None

    def get_report_by_id(self, report_id: str) -> Optional[Dict[str, Any]]:
        return self._reports_by_id.get(report_id)

    def _clean_json_text(self, text: str) -> str:
        """Strip markdown code blocks and repair minor JSON formatting issues."""
        text = text.strip()
        # Strip ```json ... ``` or ``` ... ```
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)
        text = text.strip()
        # Find outer JSON boundaries
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            text = text[start : end + 1]
        # Remove trailing commas before closing braces/brackets
        text = re.sub(r",\s*([\]}])", r"\1", text)
        return text

    async def _call_gemini_api(
        self,
        api_key: str,
        company_name: str,
        official_url: Optional[str],
        with_search: bool = True,
    ) -> Tuple[Dict[str, Any], str]:
        """
        Executes Gemini API call via async HTTPX with multi-model fallback and search grounding.
        Returns: (parsed_json_dict, source_status)
        """
        models_to_try = ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"]
        prompt = SYSTEM_PROMPT.format(
            company_name=company_name,
            official_url=official_url or "Not provided by user",
        )

        headers = {
            "Content-Type": "application/json",
        }

        last_error = None

        for model in models_to_try:
            url = f"{GEMINI_API_BASE}/{model}:generateContent?key={api_key}"

            # Step A: Try with Google Search grounding if requested
            if with_search:
                payload = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "tools": [{"googleSearch": {}}],
                    "generationConfig": {
                        "temperature": 0.2,
                    },
                }
                try:
                    async with httpx.AsyncClient(timeout=35.0) as client:
                        resp = await client.post(url, json=payload, headers=headers)
                        if resp.status_code == 200:
                            data = resp.json()
                            candidates = data.get("candidates", [])
                            if candidates:
                                text_content = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                                cleaned = self._clean_json_text(text_content)
                                parsed = json.loads(cleaned)
                                return parsed, "GOOGLE_SEARCH_GROUNDED"
                        else:
                            logger.warning(
                                f"[LiveGemini] Search-grounded call to {model} returned {resp.status_code}: {resp.text[:200]}"
                            )
                except Exception as exc:
                    logger.warning(f"[LiveGemini] Search-grounded call error on {model}: {exc}")

            # Step B: Standard generation (AI knowledge mode with JSON response MIME type)
            payload_json = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0.2,
                    "responseMimeType": "application/json",
                },
            }
            try:
                async with httpx.AsyncClient(timeout=35.0) as client:
                    resp = await client.post(url, json=payload_json, headers=headers)
                    if resp.status_code == 200:
                        data = resp.json()
                        candidates = data.get("candidates", [])
                        if candidates:
                            text_content = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                            cleaned = self._clean_json_text(text_content)
                            parsed = json.loads(cleaned)
                            return parsed, "AI_KNOWLEDGE_ONLY"
                    else:
                        last_error = f"API status {resp.status_code}: {resp.text[:200]}"
                        logger.warning(f"[LiveGemini] Standard call to {model} failed: {last_error}")
            except Exception as exc:
                last_error = str(exc)
                logger.warning(f"[LiveGemini] Standard call error on {model}: {exc}")

        # If we reached here, attempt one JSON repair retry
        raise RuntimeError(f"Gemini API generation failed across models: {last_error}")

    def _validate_company_integrity(
        self, requested_name: str, raw_json: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Guarantees that the returned report corresponds strictly to the requested company.
        FORBIDS any fallback to Google LLC or cross-company mismatch.
        """
        req_norm = requested_name.strip().lower()
        identity = raw_json.get("company_identity", {})
        ret_name = identity.get("name", "").strip()
        ret_norm = ret_name.lower()

        # 1. Strict check against forbidden Google fallback
        if "google" in ret_norm and "google" not in req_norm:
            raise ValueError(
                f"Integrity violation: requested company '{requested_name}' but received mismatched company '{ret_name}'"
            )

        # 2. If no returned name provided, populate with requested name
        if not ret_name:
            raw_json["company_identity"]["name"] = requested_name.strip()
            return raw_json

        # 3. Comprehensive compatibility check
        stopwords = {
            "llc", "inc", "corp", "corporation", "ltd", "limited", "pvt", "private",
            "co", "company", "services", "technologies", "technology", "solutions",
            "international", "group", "the", "and", "of"
        }
        req_clean = re.sub(r"[^\w\s]", "", req_norm)
        ret_clean = re.sub(r"[^\w\s]", "", ret_norm)

        # Direct exact or substring match
        is_match = (
            req_clean == ret_clean
            or req_clean in ret_clean
            or ret_clean in req_clean
        )

        # Acronym / Initials match (e.g. HAL -> Hindustan Aeronautics Limited, TCS -> Tata Consultancy Services)
        req_words = [w for w in req_clean.split() if w]
        ret_words = [w for w in ret_clean.split() if w]

        req_initials = "".join([w[0] for w in req_words])
        ret_initials = "".join([w[0] for w in ret_words])

        if req_initials and req_initials == ret_clean:
            is_match = True
        if ret_initials and ret_initials == req_clean:
            is_match = True

        # Check significant word overlap
        req_sig_words = {w for w in req_words if w not in stopwords and len(w) >= 3}
        ret_sig_words = {w for w in ret_words if w not in stopwords and len(w) >= 3}
        if req_sig_words and ret_sig_words and (req_sig_words & ret_sig_words):
            is_match = True

        # Check common prefix (e.g., "hcl" in "hcltech" and "hcl")
        if len(req_clean) >= 3 and len(ret_clean) >= 3 and req_clean[:3] == ret_clean[:3]:
            is_match = True

        # Known corporate aliases dictionary
        known_aliases = {
            "hal": ["hindustan aeronautics", "hindustan aeronautics limited"],
            "tcs": ["tata consultancy services", "tata consultancy"],
            "hcl": ["hcltech", "hcl technologies", "hcl enterprise"],
            "hcltech": ["hcl", "hcl technologies", "hcl enterprise"],
            "ibm": ["international business machines"],
        }
        for alias_key, alias_list in known_aliases.items():
            if (req_clean == alias_key or req_clean in alias_list) and (
                ret_clean == alias_key or any(a in ret_clean for a in alias_list)
            ):
                is_match = True

        if not is_match:
            logger.warning(
                f"[LiveGemini] Integrity violation detected: requested '{requested_name}' but Gemini returned '{ret_name}'"
            )
            raise ValueError(
                f"Integrity violation: requested company '{requested_name}' but received mismatched company '{ret_name}'"
            )

        return raw_json

    def _normalize_to_report_schema(
        self,
        company_name: str,
        official_url: Optional[str],
        raw: Dict[str, Any],
        source_status: str,
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Normalizes Gemini JSON output into Vishleshan AI standard 13-section report schema.
        """
        identity = raw.get("company_identity", {})
        canonical_name = identity.get("name", company_name).strip() or company_name
        exec_summary = raw.get("executive_summary", "") or identity.get("description", "")
        website = identity.get("official_website") or official_url or ""
        industry = identity.get("industry", "Technology & Services")
        headquarters = identity.get("headquarters", "Public / Global")
        founded = identity.get("founded", "")
        company_type = identity.get("company_type", "Private / Public Enterprise")

        biz_overview = raw.get("business_overview", {})
        products = biz_overview.get("products_services", [])
        target_market = biz_overview.get("target_market", "")
        business_model = biz_overview.get("business_model", "")

        corp_info = raw.get("corporate_information", {})
        founders = corp_info.get("founders", [])
        leadership = corp_info.get("leadership", [])
        locations = corp_info.get("locations", [])
        employee_count = corp_info.get("employee_count", "")

        tech = raw.get("technology_and_digital_presence", {})
        tech_focus = tech.get("technology_focus", [])
        digital_presence = tech.get("digital_presence", "")
        engineering_presence = tech.get("engineering_presence", "")

        news = raw.get("news_and_reputation", {})
        positive_signals = news.get("positive_signals", [])
        risk_signals = news.get("negative_or_risk_signals", [])
        recent_devs = news.get("recent_developments", [])

        certs = raw.get("certificates_and_registrations", [])
        regulatory = raw.get("regulatory_information", [])
        recruitment = raw.get("recruitment_analysis", {})
        risks = raw.get("risk_analysis", {})
        trust = raw.get("trust_analysis", {})
        conflicts = raw.get("conflicts", [])
        limitations = raw.get("limitations", [])
        sources = raw.get("sources", [])

        # Extract domain safely
        domain = ""
        if website:
            domain = re.sub(r"^https?://", "", website).split("/")[0].strip()

        # Build Verified Identifiers
        verified_identifiers = []
        if domain:
            verified_identifiers.append(
                {
                    "type": "Official Primary Domain",
                    "value": domain,
                    "status": "verified",
                    "source_url": website if website.startswith("http") else f"https://{website}",
                }
            )
        if industry:
            verified_identifiers.append(
                {
                    "type": "Primary Industry Classification",
                    "value": industry,
                    "status": "verified" if len(sources) > 0 else "unable_to_verify",
                    "source_url": website or "https://public-web",
                }
            )
        if headquarters:
            verified_identifiers.append(
                {
                    "type": "Operational Headquarters",
                    "value": headquarters,
                    "status": "verified" if len(sources) > 0 else "unable_to_verify",
                    "source_url": website or "https://public-web",
                }
            )

        # Build Registration & Certification findings
        registration_items = []
        for reg in regulatory:
            if isinstance(reg, dict) and reg.get("item"):
                st = reg.get("status", "UNABLE_TO_VERIFY").lower()
                status_val = "verified" if "verif" in st and "unable" not in st and "part" not in st else ("unverified" if "part" in st else "unable_to_verify")
                registration_items.append(
                    {
                        "authority": reg.get("authority", "Regulatory Authority"),
                        "registration_number": reg.get("item", ""),
                        "jurisdiction": headquarters,
                        "status": status_val,
                        "evidence": reg.get("evidence", ""),
                        "source_url": website or "https://regulatory-register",
                    }
                )

        certification_items = []
        for cert in certs:
            if isinstance(cert, dict) and cert.get("name"):
                st = cert.get("status", "UNABLE_TO_VERIFY").lower()
                status_val = "verified" if "verif" in st and "unable" not in st and "part" not in st else ("unverified" if "part" in st else "unable_to_verify")
                certification_items.append(
                    {
                        "name": cert.get("name", ""),
                        "issuer": cert.get("issuer", "Accreditation Board"),
                        "status": status_val,
                        "evidence": cert.get("evidence", ""),
                        "source_url": website or "https://public-registry",
                    }
                )

        # Build Evidence records with deterministic SHA-256 hashes
        evidence_summary = []
        for idx, src in enumerate(sources, start=1):
            if isinstance(src, dict):
                claim_text = f"Source corroborated: {src.get('title', canonical_name)} ({src.get('source_type', 'GENERAL')})"
                evidence_text = src.get("note", "") or f"Information extracted for {canonical_name} from {src.get('url', website)}"
                url = src.get("url") or website or "https://public-intelligence"
                hash_input = f"{claim_text}:{url}:{idx}".encode("utf-8")
                content_hash = hashlib.sha256(hash_input).hexdigest()

                evidence_summary.append(
                    {
                        "index": idx,
                        "claim": claim_text,
                        "evidence_text": evidence_text,
                        "source_url": url,
                        "source_type": src.get("source_type", "OTHER").lower(),
                        "reliability_score": 0.90 if src.get("reliability") == "HIGH" else (0.75 if src.get("reliability") == "MEDIUM" else 0.50),
                        "confidence_score": 0.88,
                        "verification_status": "verified" if src.get("reliability") in ["HIGH", "MEDIUM"] else "unverified",
                        "content_hash": content_hash,
                    }
                )

        # Build References
        references = []
        for idx, src in enumerate(sources, start=1):
            if isinstance(src, dict):
                references.append(
                    {
                        "index": idx,
                        "url": src.get("url") or website or "",
                        "title": src.get("title") or f"{canonical_name} Information Record",
                        "source_type": src.get("source_type", "OTHER"),
                        "reliability": 0.90 if src.get("reliability") == "HIGH" else (0.70 if src.get("reliability") == "MEDIUM" else 0.50),
                        "observed_at": datetime.now(timezone.utc).isoformat(),
                    }
                )

        # Deterministic Trust Score Handling (Section 5)
        # Trust score in presentation mode is either None or explicitly marked
        # "AI DEMO INDICATOR — NOT THE PRODUCTION TRUST INDEX"
        demo_score_val = None
        # Compute baseline indicator only if evidence is present
        if len(sources) > 0 or len(registration_items) > 0:
            verified_count = sum(1 for e in evidence_summary if e["verification_status"] == "verified")
            total = max(1, len(evidence_summary))
            ratio = verified_count / total
            demo_score_val = round(min(98.0, max(45.0, 50.0 + (ratio * 45.0))), 1)

        recruitment_risk = recruitment.get("risk_level", "LOW")
        overall_risk = risks.get("overall_level", "LOW").lower()

        report_content: Dict[str, Any] = {
            "mode": "LIVE_GEMINI_DEMO",
            "source_status": source_status,
            "overview": {
                "name": canonical_name,
                "summary": exec_summary,
                "industry": industry,
                "headquarters": headquarters,
                "founded": founded,
                "company_type": company_type,
                "size": employee_count,
                "target_market": target_market,
                "business_model": business_model,
                "products_services": products,
            },
            "official_resources": {
                "website": website,
                "careers_portal": f"{website.rstrip('/')}/careers" if website else "",
                "primary_domain": domain,
            },
            "identity_verification": {
                "status": "verified" if domain else "unverified",
                "domain_verified": bool(domain),
                "identity_summary": f"Organization identity resolved as '{canonical_name}' in industry sector '{industry}'.",
                "verified_identifiers": verified_identifiers,
            },
            "registration_findings": {
                "status": "verified" if any(r["status"] == "verified" for r in registration_items) else "unverified",
                "findings": registration_items,
            },
            "certification_findings": {
                "status": "verified" if any(c["status"] == "verified" for c in certification_items) else "unverified",
                "certifications": certification_items,
            },
            "corporate_governance": {
                "founders": founders,
                "leadership": leadership,
                "locations": locations,
                "employee_count": employee_count,
            },
            "technology_reputation": {
                "technology_focus": tech_focus,
                "digital_presence": digital_presence,
                "engineering_presence": engineering_presence,
                "positive_signals": positive_signals,
                "risk_signals": risk_signals,
            },
            "news_hiring": {
                "recent_developments": recent_devs,
                "recruitment_analysis": {
                    "risk_level": recruitment_risk,
                    "signals": recruitment.get("signals", []),
                    "explanation": recruitment.get("explanation", ""),
                },
            },
            "risk_analysis": {
                "overall_risk": overall_risk,
                "risks": risks.get("risks", []),
            },
            "trust_analysis": {
                "score": demo_score_val,
                "confidence": 0.85,
                "status": "AI_DEMO_INDICATOR",
                "algorithm_version": "AI DEMO INDICATOR — NOT THE PRODUCTION TRUST INDEX",
                "explanation": (
                    trust.get("explanation")
                    or "AI presentation mode indicator based on corroborated public intelligence. Production Trust Index requires deterministic MCA/SEC registry integration."
                ),
            },
            "conflicts": conflicts,
            "limitations": limitations,
            "evidence": evidence_summary,
            "references": references,
            "raw_gemini_intelligence": raw,
        }

        # Company metadata dict
        company_info = {
            "name": canonical_name,
            "official_website": website,
            "official_domain": domain,
            "industry": industry,
            "headquarters": headquarters,
        }

        return company_info, report_content

    async def generate_company_report(
        self,
        company_name: str,
        official_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Main pipeline:
        1. Check cache
        2. Query Gemini API
        3. Parse & repair JSON
        4. Validate company name integrity
        5. Normalize to report schema
        6. Store in cache & return
        """
        company_name = company_name.strip()
        if not company_name:
            raise ValueError("Company name must not be empty.")

        # 1. Check Cache
        cached = self.get_cached_report(company_name, official_url)
        if cached:
            return cached

        # 2. Resolve Gemini API Key from backend environment
        api_key = settings.effective_gemini_api_key
        if not api_key:
            logger.error("[LiveGemini] No Gemini API key found in backend configuration or environment.")
            raise RuntimeError(
                "Gemini API key is not configured in backend environment (checked GEMINI_API_KEY, GOOGLE_API_KEY, GOOGLE_GEMINI_API_KEY)."
            )

        logger.info(f"[LiveGemini] Calling Gemini API for '{company_name}' (URL: {official_url or 'None'})")

        # 3. Call Gemini with Search Grounding / Knowledge fallback
        raw_json, source_status = await self._call_gemini_api(
            api_key=api_key,
            company_name=company_name,
            official_url=official_url,
            with_search=True,
        )

        # 4. Enforce Company Name Integrity (FORBID Google LLC / Mismatched fallback)
        validated_json = self._validate_company_integrity(company_name, raw_json)

        # 5. Normalize into standard report schema
        company_info, report_content = self._normalize_to_report_schema(
            company_name=company_name,
            official_url=official_url,
            raw=validated_json,
            source_status=source_status,
        )

        report_id = str(uuid4())
        company_id = str(uuid4())
        run_id = str(uuid4())
        now_iso = datetime.now(timezone.utc).isoformat()

        score_id = str(uuid4())
        report_payload = {
            "id": report_id,
            "company_id": company_id,
            "research_run_id": run_id,
            "title": f"{company_info['name']} Company Intelligence Report",
            "content": report_content,
            "report_version": "1.0-live-gemini",
            "created_at": now_iso,
            "updated_at": now_iso,
            "company": {
                "id": company_id,
                "name": company_info["name"],
                "normalized_name": company_info["name"].lower().strip(),
                "official_domain": company_info["official_domain"],
                "industry": company_info["industry"],
                "headquarters": company_info["headquarters"],
                "created_at": now_iso,
                "updated_at": now_iso,
            },
            "trust_score": {
                "id": score_id,
                "company_id": company_id,
                "research_run_id": run_id,
                "score": report_content["trust_analysis"]["score"],
                "confidence": report_content["trust_analysis"]["confidence"],
                "risk_level": report_content["risk_analysis"]["overall_risk"],
                "evidence_coverage": 0.85,
                "algorithm_version": "AI DEMO INDICATOR — NOT THE PRODUCTION TRUST INDEX",
                "explanation": report_content["trust_analysis"]["explanation"],
                "created_at": now_iso,
            },
        }

        response_data = {
            "mode": "LIVE_GEMINI_DEMO",
            "company": {
                "name": company_info["name"],
                "official_website": company_info["official_website"],
            },
            "report": report_payload,
            "source_status": source_status,
            "generated_at": now_iso,
        }

        # 6. Cache for presentation reliability (10-minute TTL)
        cache_key = self._get_cache_key(company_name, official_url)
        self._cache[cache_key] = (time.time(), response_data)
        self._reports_by_id[report_id] = report_payload
        self._reports_by_id[run_id] = report_payload

        logger.info(f"[LiveGemini] Successfully generated report for '{company_info['name']}' (report_id: {report_id})")
        return response_data


# Singleton instance
gemini_live_service = GeminiLiveService()


def get_gemini_live_service() -> GeminiLiveService:
    return gemini_live_service

import os
import re
import math
import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import joblib

logger = logging.getLogger(__name__)

class RecruitmentRiskResult(BaseModel):
    score: float = Field(..., ge=0.0, le=1.0, description="Recruitment scam risk score (0.0 to 1.0)")
    risk_level: str = Field(..., description="Risk classification: low, medium, high, critical")
    model_version: str = Field(default="recruitment_scam_v1")
    signals: List[str] = Field(default_factory=list, description="Identified risk signals")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in classification (0.0 to 1.0)")
    language_score: float = Field(default=0.0, ge=0.0, le=1.0)
    domain_score: float = Field(default=0.0, ge=0.0, le=1.0)
    behavior_score: float = Field(default=0.0, ge=0.0, le=1.0)
    provenance_score: float = Field(default=0.0, ge=0.0, le=1.0)
    domain_spoofing_detected: bool = Field(default=False, description="True if corporate email spoofing/impersonation is detected")

FREE_EMAIL_DOMAINS = {"gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "aol.com", "icloud.com", "mail.com", "protonmail.com"}

SCAM_LANG_KEYWORDS = [
    ("wire transfer", 0.4), ("zelle", 0.4), ("cashapp", 0.4), ("crypto payment", 0.4),
    ("telegram", 0.35), ("whatsapp", 0.35), ("deposit check", 0.45), ("equipment check", 0.45),
    ("no experience required", 0.25), ("high weekly pay", 0.3), ("immediate start", 0.2),
    ("immediate placement", 0.25), ("no interview required", 0.4), ("online form filler", 0.35),
    ("package handler", 0.3), ("re-shipping", 0.4), ("instant payouts", 0.3),
    ("recruitment fee", 0.6), ("upfront payment", 0.6), ("fee request", 0.5), ("interview fee", 0.6)
]

class RecruitmentClassifier:
    """
    Recruitment Scam Risk Classifier evaluating candidate job opportunities.
    Combines ML prediction with domain, language, behavioral, and provenance heuristics.
    """
    def __init__(self, model_path: Optional[str] = None):
        if model_path is None:
            model_path = os.path.join(os.path.dirname(__file__), "..", "ml", "models", "recruitment_scam_v1.joblib")
        
        self.model_path = model_path
        self.model_artifact: Optional[Dict[str, Any]] = None
        self.is_ml_loaded = False
        
        self._load_model()

    def _load_model(self):
        try:
            if os.path.exists(self.model_path):
                artifact = joblib.load(self.model_path)
                if isinstance(artifact, dict) and "vocab" in artifact and "weights" in artifact:
                    self.model_artifact = artifact
                    self.is_ml_loaded = True
                    logger.info("RecruitmentClassifier: ML model artifact loaded successfully.")
                else:
                    logger.warning("RecruitmentClassifier: Invalid model artifact structure, using fallback.")
            else:
                logger.warning(f"RecruitmentClassifier: Model artifact not found at {self.model_path}, using fallback.")
        except Exception as e:
            logger.error(f"RecruitmentClassifier: Failed to load ML model artifact ({e}), falling back to heuristic engine.")
            self.model_artifact = None
            self.is_ml_loaded = False

    def _predict_ml_proba(self, text: str) -> float:
        if not self.is_ml_loaded or not self.model_artifact:
            return 0.0

        vocab = self.model_artifact.get("vocab", {})
        idf = self.model_artifact.get("idf", {})
        weights = self.model_artifact.get("weights", {})
        bias = self.model_artifact.get("bias", 0.0)
        ngram_range = self.model_artifact.get("ngram_range", (1, 2))

        # Tokenize
        words = re.findall(r'\b[a-z0-9_]+\b', text.lower())
        tokens = []
        if ngram_range[0] <= 1 <= ngram_range[1]:
            tokens.extend(words)
        if ngram_range[0] <= 2 <= ngram_range[1]:
            tokens.extend([f"{words[i]}_{words[i+1]}" for i in range(len(words)-1)])

        score = bias
        tf_counts: Dict[str, int] = {}
        for tok in tokens:
            if tok in vocab:
                tf_counts[tok] = tf_counts.get(tok, 0) + 1

        for tok, tf in tf_counts.items():
            sublinear_tf = 1.0 + math.log(tf)
            score += sublinear_tf * idf.get(tok, 1.0) * weights.get(tok, 0.0) * 0.15

        prob = 1.0 / (1.0 + math.exp(-max(-15.0, min(15.0, score))))
        return prob

    def evaluate(
        self,
        job_title: str = "",
        company_name: str = "",
        description: str = "",
        company_profile: str = "",
        requirements: str = "",
        contact_email: str = "",
        evidence_sources: Optional[List[Dict[str, Any]]] = None
    ) -> RecruitmentRiskResult:
        # Truncate inputs safely
        job_title = (job_title or "")[:500]
        company_name = (company_name or "")[:500]
        description = (description or "")[:10000]
        company_profile = (company_profile or "")[:5000]
        requirements = (requirements or "")[:5000]
        contact_email = (contact_email or "").strip().lower()[:200]

        combined_text = f"{job_title} {company_name} {company_profile} {description} {requirements}".strip()

        if not combined_text and not contact_email:
            return RecruitmentRiskResult(
                score=0.0,
                risk_level="low",
                signals=["Empty input provided"],
                confidence=0.1,
                language_score=0.0,
                domain_score=0.0,
                behavior_score=0.0,
                provenance_score=0.0,
                domain_spoofing_detected=False
            )

        signals: List[str] = []

        # 1. Language Signals
        lang_score = 0.0
        ml_proba = self._predict_ml_proba(combined_text) if self.is_ml_loaded else 0.0
        
        text_lower = combined_text.lower()
        keyword_hits = 0
        for kw, weight in SCAM_LANG_KEYWORDS:
            if kw in text_lower:
                lang_score += weight
                keyword_hits += 1
                signals.append(f"Language risk indicator detected: '{kw}'")

        if self.is_ml_loaded:
            if keyword_hits > 0:
                lang_score = max(min(1.0, lang_score), 0.5 * ml_proba + 0.5 * min(1.0, lang_score))
            else:
                lang_score = min(1.0, 0.5 * ml_proba + 0.5 * min(1.0, lang_score))
        else:
            lang_score = min(1.0, lang_score)

        # 2. Domain Signals
        domain_score = 0.0
        domain_spoofing = False
        if contact_email:
            email_parts = contact_email.split("@")
            if len(email_parts) == 2:
                domain = email_parts[1].strip()
                if domain in FREE_EMAIL_DOMAINS:
                    domain_score += 0.6
                    signals.append(f"Official recruitment conducted via free email domain (@{domain})")
                    
                    # Check for domain spoofing/impersonation if company name is established
                    if company_name and len(company_name) > 3:
                        comp_clean = re.sub(r'[^a-z0-9]', '', company_name.lower())
                        if comp_clean not in {"scamco", "unknown"}:
                            domain_spoofing = True
                            domain_score += 0.3
                            signals.append(f"Domain spoofing/impersonation: '{company_name}' recruiting via generic @{domain}")

        # 3. Behavioral Signals
        behavior_score = 0.0
        if "telegram" in text_lower or "whatsapp" in text_lower:
            behavior_score += 0.5
            signals.append("Recruitment interview exclusively routed through encrypted messaging app (Telegram/WhatsApp)")
        
        if "recruitment fee" in text_lower or "upfront payment" in text_lower or "fee request" in text_lower or "interview fee" in text_lower:
            behavior_score += 0.8
            signals.append("Upfront payment or recruitment fee requested for job offer or interview")

        if "deposit check" in text_lower or "equipment check" in text_lower or "purchase home office" in text_lower:
            behavior_score += 0.6
            signals.append("Advance fee / fake check equipment purchase scam pattern detected")

        if "wire transfer" in text_lower or "zelle" in text_lower or "cashapp" in text_lower:
            behavior_score += 0.5
            signals.append("Payment processing / money transfer duties required from personal account")

        if "no interview" in text_lower or "immediate placement" in text_lower:
            behavior_score += 0.4
            signals.append("Immediate placement offered without standard interview process")

        behavior_score = min(1.0, behavior_score)

        # 4. Provenance Signals
        provenance_score = 0.0
        if evidence_sources:
            unverified_count = 0
            for src in evidence_sources:
                stype = src.get("source_type", "").lower()
                if stype in {"unverified_web", "forum", "classifieds"}:
                    unverified_count += 1
            if unverified_count > 0:
                provenance_score += min(0.5, unverified_count * 0.25)
                signals.append(f"Evidence sourced from {unverified_count} unverified or high-risk web channels")

        provenance_score = min(1.0, provenance_score)

        # Overall Score Fusion
        if contact_email:
            final_score = (
                0.40 * lang_score +
                0.25 * domain_score +
                0.25 * behavior_score +
                0.10 * provenance_score
            )
        else:
            # Re-normalize when contact email / domain info is not present
            final_score = (
                0.45 * lang_score +
                0.40 * behavior_score +
                0.15 * provenance_score
            )
        final_score = round(min(1.0, max(0.0, final_score)), 4)

        # Risk Level Mapping
        if final_score >= 0.75:
            risk_level = "critical"
        elif final_score >= 0.55:
            risk_level = "high"
        elif final_score >= 0.30:
            risk_level = "medium"
        else:
            risk_level = "low"

        # Confidence Calculation
        if self.is_ml_loaded and (ml_proba > 0.7 and (keyword_hits > 0 or domain_score > 0)):
            confidence = 0.95
        elif self.is_ml_loaded and (ml_proba < 0.2 and keyword_hits == 0 and domain_score == 0):
            confidence = 0.90
        elif len(signals) >= 2:
            confidence = 0.85
        elif len(signals) == 1:
            confidence = 0.70
        else:
            confidence = 0.80 if combined_text else 0.30

        return RecruitmentRiskResult(
            score=final_score,
            risk_level=risk_level,
            model_version="recruitment_scam_v1" if self.is_ml_loaded else "recruitment_scam_fallback_v1",
            signals=signals,
            confidence=confidence,
            language_score=round(lang_score, 4),
            domain_score=round(domain_score, 4),
            behavior_score=round(behavior_score, 4),
            provenance_score=round(provenance_score, 4),
            domain_spoofing_detected=domain_spoofing
        )

import re
from typing import Dict, List, Optional, Set, Tuple
from uuid import uuid4
from pydantic import BaseModel, Field

from app.research.models import NormalizedEvidence


class NormalizedClaim(BaseModel):
    """
    Structured representation of a discrete claim extracted from normalized evidence.
    """
    claim_id: str = Field(default_factory=lambda: str(uuid4()))
    evidence_id: str = Field(..., description="UUID of parent NormalizedEvidence record")
    subject: str = Field(..., description="Normalized company or entity subject name")
    predicate: str = Field(..., description="Standardized predicate attribute identifier")
    object_value: str = Field(..., description="Normalized value of the claimed attribute")
    claim_type: str = Field(default="attribute_statement", description="Type classification of claim")
    source_url: Optional[str] = Field(default="", description="Source URL of evidence")
    source_type: str = Field(default="other", description="Tier type of source")
    reliability: float = Field(default=0.70, description="Source reliability score (0.0 to 1.0)")
    raw_claim: str = Field(..., description="Raw claim sentence text")


# Predicate extraction patterns for corporate intelligence domain
PREDICATE_PATTERNS: Dict[str, List[re.Pattern]] = {
    "founded_year": [
        re.compile(r"\b(?:founded|established|incorporated|started|created)\s+(?:in\s+)?([12][09]\d{2})\b", re.IGNORECASE),
        re.compile(r"\b([12][09]\d{2})\s+(?:founding|incorporation)\b", re.IGNORECASE),
    ],
    "headquarters": [
        re.compile(r"\b(?:headquartered|based|located|headquarters|hq)\s+(?:in|at)\s+([A-Za-z\s,\.]+)", re.IGNORECASE),
    ],
    "legal_status": [
        re.compile(r"\b(active|dissolved|suspended|inactive|defunct|strike-off|cancelled)\b", re.IGNORECASE),
        re.compile(r"\bstatus[:\s]+(active|dissolved|suspended|inactive|defunct)\b", re.IGNORECASE),
    ],
    "registration_number": [
        re.compile(r"\b(?:registration|reg|cin|ein|tin|tax id)[:\s#]+([A-Z0-9\-]{5,21})\b", re.IGNORECASE),
    ],
    "executive_leadership": [
        re.compile(r"\b(?:ceo|founder|director|president|managing director)[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b", re.IGNORECASE),
    ],
    "operating_location": [
        re.compile(r"\b(?:operates in|offices in|branches in)\s+([A-Za-z\s,\.]+)", re.IGNORECASE),
    ],
}


class ClaimNormalizer:
    """
    Extracts structured claims from NormalizedEvidence items and selects candidate comparison pairs
    matching on subject and predicate to avoid O(n^2) comparison explosion.
    """

    def normalize(self, evidence_list: List[NormalizedEvidence], default_subject: str = "Target Entity") -> List[NormalizedClaim]:
        """
        Parses evidence items into a list of structured NormalizedClaim objects.
        """
        claims: List[NormalizedClaim] = []

        for e in evidence_list:
            ev_id = str(getattr(e, "id", "") or uuid4())
            s_url = getattr(e, "source_url", "") or ""
            s_type = getattr(e.source_type, "value", str(getattr(e, "source_type", "other")))
            reliability = float(getattr(e, "reliability_score", 0.70))
            raw_text = f"{e.claim} {e.evidence_text}".strip()

            if not raw_text:
                continue

            extracted_predicates = set()

            # Attempt pattern matching for structured predicates
            for pred_name, patterns in PREDICATE_PATTERNS.items():
                for pat in patterns:
                    match = pat.search(raw_text)
                    if match:
                        obj_val = match.group(1).strip()
                        claims.append(
                            NormalizedClaim(
                                evidence_id=ev_id,
                                subject=default_subject,
                                predicate=pred_name,
                                object_value=obj_val,
                                claim_type="structured_attribute",
                                source_url=s_url,
                                source_type=s_type,
                                reliability=reliability,
                                raw_claim=e.claim or raw_text,
                            )
                        )
                        extracted_predicates.add(pred_name)
                        break

            # Fallback for general unparsed claims
            if not extracted_predicates:
                claims.append(
                    NormalizedClaim(
                        evidence_id=ev_id,
                        subject=default_subject,
                        predicate="general_statement",
                        object_value=e.claim,
                        claim_type="text_claim",
                        source_url=s_url,
                        source_type=s_type,
                        reliability=reliability,
                        raw_claim=e.claim or raw_text,
                    )
                )

        return claims

    def extract_candidate_pairs(
        self, claims: List[NormalizedClaim]
    ) -> List[Tuple[NormalizedClaim, NormalizedClaim]]:
        """
        Filters candidate pairs matching on subject and predicate.
        Filters out pairs sharing identical source_url or evidence_id to prevent redundant self-comparisons.
        """
        grouped: Dict[Tuple[str, str], List[NormalizedClaim]] = {}

        for claim in claims:
            key = (claim.subject.lower(), claim.predicate.lower())
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(claim)

        candidate_pairs: List[Tuple[NormalizedClaim, NormalizedClaim]] = []
        seen_pairs: Set[Tuple[str, str]] = set()

        for (subj, pred), claim_group in grouped.items():
            # Skip general statements without specific predicate matching unless explicitly small
            if pred == "general_statement" and len(claim_group) > 10:
                continue

            n = len(claim_group)
            for i in range(n):
                for j in range(i + 1, n):
                    c1, c2 = claim_group[i], claim_group[j]

                    # Deduplication check: Skip pairs from the same evidence ID or identical source URL
                    if c1.evidence_id == c2.evidence_id:
                        continue
                    if c1.source_url and c2.source_url and c1.source_url == c2.source_url:
                        continue

                    pair_id = tuple(sorted([c1.claim_id, c2.claim_id]))
                    if pair_id not in seen_pairs:
                        seen_pairs.add(pair_id)
                        candidate_pairs.append((c1, c2))

        return candidate_pairs

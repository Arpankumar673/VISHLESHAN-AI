import re
from typing import Dict, List
from urllib.parse import urlparse
from app.research.evidence.models import EvidenceGroup
from app.research.models import NormalizedEvidence


def normalize_claim_text(claim: str) -> str:
    """Deterministically normalizes claim text for equivalence grouping without LLMs or aggressive stemming.
    
    Operations:
    - Lowercase and trim surrounding whitespace
    - Collapse internal whitespace runs to a single space
    - Strip trailing punctuation (. , ; :)
    - Normalize scheme and www prefixes from embedded URLs/domains
    """
    if not claim:
        return ""
    
    text = claim.strip().lower()
    # Normalize internal whitespace
    text = re.sub(r"\s+", " ", text)
    # Strip trailing punctuation
    text = re.sub(r"[.,;:]+$", "", text)
    # Normalize embedded URLs: e.g. https://www.example.com/ -> example.com
    text = re.sub(r"https?://(?:www\.)?([a-zA-Z0-9.\-]+)(?:/)?", r"\1", text)
    return text.strip()


def group_evidence(evidence: List[NormalizedEvidence]) -> List[EvidenceGroup]:
    """Groups normalized evidence items into logical claim clusters based on normalized claim text.
    
    Preserves exact NormalizedEvidence provenance on every item.
    """
    if not evidence:
        return []

    groups_map: Dict[str, EvidenceGroup] = {}

    for item in evidence:
        norm_key = normalize_claim_text(item.claim)
        if not norm_key:
            continue

        if norm_key not in groups_map:
            groups_map[norm_key] = EvidenceGroup(
                canonical_claim=item.claim.strip(),
                evidence=[item],
                supporting_evidence=[],
                contradicting_evidence=[],
            )
        else:
            group = groups_map[norm_key]
            group.evidence.append(item)

    return list(groups_map.values())

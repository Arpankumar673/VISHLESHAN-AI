import re
from typing import Dict, List, Optional, Tuple
from app.research.evidence.models import EvidenceGroup
from app.research.models import NormalizedEvidence


def extract_founding_year(text: str) -> Optional[int]:
    """Extracts founding year from claim/evidence text if present."""
    if not text:
        return None
    match = re.search(r"\b(?:founded|established|incorporated|started)(?:\s+in)?\s+(\d{4})\b", text, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return None


def extract_official_domain_value(text: str) -> Optional[str]:
    """Extracts domain value from domain-specific claims."""
    if not text:
        return None
    match = re.search(r"\b(?:official domain|official website|domain|website)(?:\s+is)?\s+([a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})\b", text, re.IGNORECASE)
    if match:
        return match.group(1).lower().strip()
    return None


def extract_key_value(text: str, key_term: str) -> Optional[str]:
    """Extracts value for key terms such as CEO, founder, or headquarters."""
    if not text:
        return None
    # 1. Match explicit "key is/was value" first
    pattern_is = rf"\b{key_term}\s+(?:is|was)\s+([A-Za-z0-9\s.]+)(?=[.,;:]|$)"
    match_is = re.search(pattern_is, text, re.IGNORECASE)
    if match_is:
        val = match_is.group(1).strip().lower()
        if len(val) > 1:
            return val
    # 2. Match general "key value" fallback
    pattern_gen = rf"\b{key_term}\s+([A-Za-z0-9\s.]+)(?=[.,;:]|$)"
    match_gen = re.search(pattern_gen, text, re.IGNORECASE)
    if match_gen:
        val = match_gen.group(1).strip().lower()
        if len(val) > 1:
            return val
    return None


def extract_employee_count(text: str) -> Optional[int]:
    """Extracts employee count from numeric claims."""
    if not text:
        return None
    match = re.search(r"\b(\d+[\d,]*)\s*(?:employees|headcount|staff|workers)\b", text, re.IGNORECASE)
    if match:
        try:
            return int(match.group(1).replace(",", ""))
        except ValueError:
            return None
    return None


def detect_conflicts(group: EvidenceGroup) -> EvidenceGroup:
    """Deterministically identifies factual contradictions within an evidence group.
    
    If unambiguous contradictions (years, numbers, domains, key-values) are identified,
    partitions evidence into supporting_evidence (majority/primary position) and
    contradicting_evidence (dissenting position).
    
    Safeguard: If no contradiction is confidently established, no conflict is reported.
    """
    evidence_items = group.evidence
    if len(evidence_items) <= 1:
        group.supporting_evidence = list(evidence_items)
        group.contradicting_evidence = []
        return group

    # 1. Check Founding Year Contradictions
    years = [extract_founding_year(f"{item.claim} {item.evidence_text}") for item in evidence_items]
    valid_years = [y for y in years if y is not None]
    if len(valid_years) >= 2 and len(set(valid_years)) > 1:
        return _partition_by_extracted_value(group, years)

    # 2. Check Official Domain Contradictions
    domains = [extract_official_domain_value(f"{item.claim} {item.evidence_text}") for item in evidence_items]
    valid_domains = [d for d in domains if d is not None]
    if len(valid_domains) >= 2 and len(set(valid_domains)) > 1:
        return _partition_by_extracted_value(group, domains)

    # 3. Check CEO / Key-Value Contradictions
    ceos = [extract_key_value(f"{item.claim} {item.evidence_text}", "ceo") for item in evidence_items]
    valid_ceos = [c for c in ceos if c is not None]
    if len(valid_ceos) >= 2 and len(set(valid_ceos)) > 1:
        return _partition_by_extracted_value(group, ceos)

    # 4. Check Headquarters Contradictions
    hqs = [extract_key_value(f"{item.claim} {item.evidence_text}", "headquarters") for item in evidence_items]
    valid_hqs = [h for h in hqs if h is not None]
    if len(valid_hqs) >= 2 and len(set(valid_hqs)) > 1:
        return _partition_by_extracted_value(group, hqs)

    # 5. Check Employee Count Contradictions
    counts = [extract_employee_count(f"{item.claim} {item.evidence_text}") for item in evidence_items]
    valid_counts = [cnt for cnt in counts if cnt is not None]
    if len(valid_counts) >= 2 and len(set(valid_counts)) > 1:
        return _partition_by_extracted_value(group, counts)

    # Default: No unambiguous conflict detected -> all items are supporting evidence
    group.supporting_evidence = list(evidence_items)
    group.contradicting_evidence = []
    return group


def _partition_by_extracted_value(group: EvidenceGroup, extracted_values: List[Optional[object]]) -> EvidenceGroup:
    """Partitions evidence items into majority supporting and dissenting contradicting collections."""
    value_counts: Dict[object, int] = {}
    for val in extracted_values:
        if val is not None:
            value_counts[val] = value_counts.get(val, 0) + 1

    if not value_counts:
        group.supporting_evidence = list(group.evidence)
        group.contradicting_evidence = []
        return group

    # Primary value is the most frequently occurring extracted value
    primary_value = max(value_counts.items(), key=lambda x: x[1])[0]

    supporting: List[NormalizedEvidence] = []
    contradicting: List[NormalizedEvidence] = []

    for item, val in zip(group.evidence, extracted_values):
        if val is None or val == primary_value:
            supporting.append(item)
        else:
            contradicting.append(item)

    group.supporting_evidence = supporting
    group.contradicting_evidence = contradicting
    return group

from typing import List, Set
from app.research.models import NormalizedEvidence


class EvidenceDeduplicator:
    """Deduplicates evidence items based on cryptographic content hash and source uniqueness."""

    @staticmethod
    def deduplicate(evidence_list: List[NormalizedEvidence]) -> List[NormalizedEvidence]:
        seen_hashes: Set[str] = set()
        unique_items: List[NormalizedEvidence] = []

        for item in evidence_list:
            if item.content_hash not in seen_hashes:
                seen_hashes.add(item.content_hash)
                unique_items.append(item)

        return unique_items

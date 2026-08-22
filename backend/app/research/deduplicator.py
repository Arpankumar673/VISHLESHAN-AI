from typing import List, Set
from app.research.models import NormalizedEvidence


class EvidenceDeduplicator:
    """Deduplicates evidence items based on cryptographic content hash and normalized claim signatures."""

    @staticmethod
    def deduplicate(evidence_list: List[NormalizedEvidence]) -> List[NormalizedEvidence]:
        seen_hashes: Set[str] = set()
        seen_claim_signatures: Set[str] = set()
        unique_items: List[NormalizedEvidence] = []

        for item in evidence_list:
            if not item:
                continue

            # Primary cryptographic hash check
            if item.content_hash and item.content_hash in seen_hashes:
                continue

            # Secondary claim signature check (normalizes claim + source_url)
            norm_claim = (item.claim or "").strip().lower()
            norm_url = (item.source_url or "").strip().lower()
            sig = f"{norm_claim}|{norm_url}"

            if sig in seen_claim_signatures:
                continue

            if item.content_hash:
                seen_hashes.add(item.content_hash)
            seen_claim_signatures.add(sig)
            unique_items.append(item)

        return unique_items

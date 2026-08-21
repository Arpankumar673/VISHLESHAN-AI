from typing import Dict, List, Set
from urllib.parse import urlparse
from pydantic import BaseModel, Field
from app.research.models import NormalizedEvidence


class SourceIndependenceResult(BaseModel):
    """Assessment of source independence across a collection of evidence items."""
    total_sources: int = Field(default=0, ge=0)
    independent_sources: int = Field(default=0, ge=0)
    dependent_sources: int = Field(default=0, ge=0)
    source_clusters: List[List[str]] = Field(default_factory=list)
    explanation: str = Field(default="")


def normalize_url_for_independence(url: str) -> str:
    """Normalizes URL for deterministic independence comparison."""
    if not url:
        return ""
    try:
        parsed = urlparse(url.lower().strip())
        domain = parsed.netloc
        if domain.startswith("www."):
            domain = domain[4:]
        path = parsed.path.rstrip("/")
        return f"{domain}{path}"
    except Exception:
        return url.lower().strip()


class DisjointSet:
    """Disjoint Set / Union-Find for deterministic clustering."""
    def __init__(self, n: int):
        self.parent = list(range(n))

    def find(self, i: int) -> int:
        if self.parent[i] == i:
            return i
        self.parent[i] = self.find(self.parent[i])
        return self.parent[i]

    def union(self, i: int, j: int):
        root_i = self.find(i)
        root_j = self.find(j)
        if root_i != root_j:
            self.parent[root_b := min(root_i, root_j)] = max(root_i, root_j)


def assess_source_independence(evidence: List[NormalizedEvidence]) -> SourceIndependenceResult:
    """Deterministically evaluates source independence using content hashes and canonical URLs.
    
    Identifies dependent sources that share identical content hashes or identical canonical URLs.
    """
    total = len(evidence)
    if total == 0:
        return SourceIndependenceResult(
            total_sources=0,
            independent_sources=0,
            dependent_sources=0,
            source_clusters=[],
            explanation="No evidence items provided.",
        )

    dset = DisjointSet(total)
    url_map: Dict[str, int] = {}
    hash_map: Dict[str, int] = {}

    for i, item in enumerate(evidence):
        norm_url = normalize_url_for_independence(item.source_url)
        content_hash = item.content_hash.strip() if item.content_hash else ""

        # Check URL dependence
        if norm_url and norm_url in url_map:
            dset.union(i, url_map[norm_url])
        elif norm_url:
            url_map[norm_url] = i

        # Check content hash dependence
        if content_hash and content_hash in hash_map:
            dset.union(i, hash_map[content_hash])
        elif content_hash:
            hash_map[content_hash] = i

    # Group evidence items by cluster root
    clusters_dict: Dict[int, List[str]] = {}
    for i in range(total):
        root = dset.find(i)
        if root not in clusters_dict:
            clusters_dict[root] = []
        clusters_dict[root].append(evidence[i].source_url)

    source_clusters = list(clusters_dict.values())
    independent_count = len(source_clusters)
    dependent_count = total - independent_count

    if dependent_count == 0:
        explanation = f"All {total} evidence sources are independent based on unique content hashes and canonical URLs."
    else:
        explanation = f"Found {independent_count} independent source clusters across {total} total evidence items ({dependent_count} dependent duplicate sources identified)."

    return SourceIndependenceResult(
        total_sources=total,
        independent_sources=independent_count,
        dependent_sources=dependent_count,
        source_clusters=source_clusters,
        explanation=explanation,
    )

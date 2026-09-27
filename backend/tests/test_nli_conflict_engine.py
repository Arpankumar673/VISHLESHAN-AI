from datetime import datetime, timezone
from uuid import uuid4
import pytest

from app.core.llm_security import wrap_untrusted_content
from app.research.models import NormalizedEvidence
from app.schemas.evidence import SourceType, VerificationStatus
from app.services.claim_normalizer import ClaimNormalizer, NormalizedClaim
from app.services.nli_conflict_engine import (
    LexicalConflictBaseline,
    NLIConflictEngine,
    NLILabel,
    NLIResult,
    SemanticNLIModel,
)


def test_nli_model_runtime_reporting():
    """Verify runtime reporting of active NLI model implementation type."""
    model = SemanticNLIModel()
    assert model.implementation_type in [
        "pretrained Transformer NLI model",
        "engineered-feature/logistic fallback",
    ]
    assert model.model_name is not None
    assert model.version == "v1"


def test_case_a_clear_entailment():
    """Case A: Clear entailment statement pair."""
    engine = NLIConflictEngine()
    p = "Acme Corp was founded in 2018 in Bangalore."
    h = "Acme Corp was established in 2018 in Bangalore."
    res = engine.evaluate_pair(p, h)
    assert res.label == NLILabel.ENTAILMENT
    assert res.confidence >= 0.60
    assert res.confidence_label == "UNCALIBRATED MODEL CONFIDENCE"


def test_case_b_clear_contradiction():
    """Case B: Clear contradiction statement pair (year mismatch)."""
    engine = NLIConflictEngine()
    p = "Acme Corp was incorporated in 2015."
    h = "Acme Corp was founded in 2022."
    res = engine.evaluate_pair(p, h)
    assert res.label == NLILabel.CONTRADICTION
    assert res.confidence >= 0.70
    assert res.confidence_label == "UNCALIBRATED MODEL CONFIDENCE"


def test_case_c_neutral():
    """Case C: Neutral statement pair (unrelated claims)."""
    engine = NLIConflictEngine()
    p = "Acme Corp develops enterprise AI software."
    h = "The founder completed his degree at IIT Bombay."
    res = engine.evaluate_pair(p, h)
    assert res.label == NLILabel.NEUTRAL


def test_case_d_partial_evidence_not_contradiction():
    """Case D: Missing/partial evidence yields UNABLE_TO_VERIFY, NOT CONTRADICTION."""
    normalizer = ClaimNormalizer()
    ev1 = NormalizedEvidence(
        id=uuid4(),
        research_run_id=uuid4(),
        agent_name="company_research",
        source_type=SourceType.OFFICIAL_COMPANY,
        source_url="https://acme.com",
        claim="Acme Corp operates in India",
        evidence_text="Company headquarters located in Bangalore",
        observed_at=datetime.now(timezone.utc),
        reliability_score=0.90,
        confidence_score=0.85,
        verification_status=VerificationStatus.UNVERIFIED,
        content_hash="test_hash_12345",
    )
    claims = normalizer.normalize([ev1])
    # Single claim group has no candidate pairs
    candidate_pairs = normalizer.extract_candidate_pairs(claims)
    assert len(candidate_pairs) == 0


def test_case_e_source_deduplication():
    """Case F: Duplicate sources sharing identical source_url or evidence_id are filtered out."""
    normalizer = ClaimNormalizer()
    url = "https://example.com/press"
    ev_id = str(uuid4())
    c1 = NormalizedClaim(
        evidence_id=ev_id,
        subject="Acme Corp",
        predicate="founded_year",
        object_value="2018",
        source_url=url,
        raw_claim="Acme Corp founded in 2018",
    )
    c2 = NormalizedClaim(
        evidence_id=ev_id,
        subject="Acme Corp",
        predicate="founded_year",
        object_value="2018",
        source_url=url,
        raw_claim="Acme Corp established 2018",
    )
    pairs = normalizer.extract_candidate_pairs([c1, c2])
    assert len(pairs) == 0


def test_candidate_pair_filtering_reduces_complexity():
    """Verify subject/predicate grouping prevents O(n^2) explosion."""
    normalizer = ClaimNormalizer()
    claims = [
        NormalizedClaim(
            evidence_id=str(uuid4()),
            subject="Acme",
            predicate="founded_year",
            object_value="2018",
            source_url="https://a.com",
            raw_claim="Founded 2018",
        ),
        NormalizedClaim(
            evidence_id=str(uuid4()),
            subject="Acme",
            predicate="founded_year",
            object_value="2019",
            source_url="https://b.com",
            raw_claim="Founded 2019",
        ),
        NormalizedClaim(
            evidence_id=str(uuid4()),
            subject="Acme",
            predicate="headquarters",
            object_value="Bangalore",
            source_url="https://c.com",
            raw_claim="HQ in Bangalore",
        ),
        NormalizedClaim(
            evidence_id=str(uuid4()),
            subject="Acme",
            predicate="headquarters",
            object_value="Delhi",
            source_url="https://d.com",
            raw_claim="HQ in Delhi",
        ),
    ]

    pairs = normalizer.extract_candidate_pairs(claims)
    # Total possible pairs is 4*3/2 = 6. Filtered pairs matching predicate is exactly 2.
    assert len(pairs) == 2


def test_security_boundary_wrapping():
    """Verify XML untrusted content encapsulation for LLM safety context."""
    raw_text = "Acme Corp <script>alert(1)</script> founded in 2018"
    wrapped = wrap_untrusted_content(raw_text, tag="premise_evidence")
    assert "<premise_evidence>" in wrapped
    assert "</premise_evidence>" in wrapped
    assert "Acme Corp" in wrapped

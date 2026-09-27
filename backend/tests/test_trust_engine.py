from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import uuid4
import pytest
from fastapi.testclient import TestClient

from app.core.limiter import limiter
from app.core.llm_security import wrap_untrusted_content
from app.core.security import AuthenticatedUser, get_current_user
from app.main import app
from app.research.agents.verification_agent import _is_safe_public_url
from app.research.models import NormalizedEvidence
from app.schemas.evidence import SourceType, VerificationStatus
from app.schemas.trust import (
    ConflictLevel,
    TrustVerificationStatus,
)
from app.services.rag_service import RAGService
from app.services.research_service import get_research_service
from app.services.trust_engine import (
    TRUST_MODEL_VERSION,
    TRUST_WEIGHTS,
    TrustEngine,
    validate_trust_config,
)

client = TestClient(app)
test_user_id = uuid4()


def make_test_ev(
    claim: str,
    evidence_text: str = "Verified observational evidence.",
    source_url: str = "https://example.com",
    source_title: str = "Evidence Source",
    source_type: SourceType = SourceType.OFFICIAL_COMPANY,
    reliability_score: float = 0.85,
    confidence_score: float = 0.85,
    verification_status: VerificationStatus = VerificationStatus.UNVERIFIED,
    agent_name: str = "test_agent",
    published_at: Optional[datetime] = None,
    content_hash: Optional[str] = None,
) -> NormalizedEvidence:
    return NormalizedEvidence(
        claim=claim,
        evidence_text=evidence_text,
        source_url=source_url,
        source_title=source_title,
        source_type=source_type,
        published_at=published_at,
        observed_at=datetime.now(timezone.utc),
        reliability_score=reliability_score,
        confidence_score=confidence_score,
        verification_status=verification_status,
        agent_name=agent_name,
        content_hash=content_hash or f"hash_{abs(hash(claim + source_url))}",
    )


class MockResearchServiceForTrust:
    async def start_research(self, user_id, company_name, company_url=None):
        from app.schemas.research import ResearchStatus, StartResearchResponse
        return StartResearchResponse(
            research_run_id=uuid4(),
            company_id=uuid4(),
            status=ResearchStatus.QUEUED,
        )


@pytest.fixture(autouse=True)
def override_test_dependencies():
    app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(
        id=test_user_id, email="trust_test@example.com", role="authenticated"
    )
    app.dependency_overrides[get_research_service] = lambda: MockResearchServiceForTrust()
    limiter.reset()
    yield
    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(get_research_service, None)
    limiter.reset()


# -----------------------------------------------------------------------------
# 1. Weight Validation & Configuration Tests
# -----------------------------------------------------------------------------

def test_trust_config_valid():
    validate_trust_config(TRUST_WEIGHTS, TRUST_MODEL_VERSION)
    assert sum(TRUST_WEIGHTS.values()) == 1.0
    assert TRUST_MODEL_VERSION == "v1"


def test_trust_config_invalid_sum():
    bad_weights = {"identity": 0.50, "technical_provenance": 0.20, "regulatory": 0.25, "evidence": 0.20, "risk": 0.15}
    with pytest.raises(ValueError, match="Trust model weights must sum to 1.0"):
        validate_trust_config(bad_weights, "v1")


def test_trust_config_negative_weight():
    bad_weights = {"identity": -0.10, "technical_provenance": 0.30, "regulatory": 0.25, "evidence": 0.40, "risk": 0.15}
    with pytest.raises(ValueError, match="must be a non-negative number"):
        validate_trust_config(bad_weights, "v1")


def test_trust_config_missing_dimension():
    bad_weights = {"identity": 0.50, "technical_provenance": 0.50}
    with pytest.raises(ValueError, match="Missing required trust model dimensions"):
        validate_trust_config(bad_weights, "v1")


def test_trust_config_missing_version():
    with pytest.raises(ValueError, match="TRUST_MODEL_VERSION must be a non-empty string"):
        validate_trust_config(TRUST_WEIGHTS, "")


# -----------------------------------------------------------------------------
# 2. Engine Determinism Tests
# -----------------------------------------------------------------------------

def test_trust_engine_determinism():
    engine = TrustEngine()
    evidence = [
        make_test_ev(
            claim="HackIndia operates official domain hackindia.org",
            evidence_text="Verified HTTPS TLS domain.",
            source_url="https://hackindia.org",
            source_title="Official Portal",
            source_type=SourceType.OFFICIAL_COMPANY,
            reliability_score=0.95,
            confidence_score=0.90,
            verification_status=VerificationStatus.VERIFIED,
            agent_name="company_research",
            content_hash="hash_1",
        )
    ]

    res1 = engine.compute_trust_index(evidence, "HackIndia", "hackindia.org")
    res2 = engine.compute_trust_index(evidence, "HackIndia", "hackindia.org")

    assert res1.trust_index == res2.trust_index
    assert res1.confidence == res2.confidence
    assert res1.verification_status == res2.verification_status
    assert res1.model_version == res2.model_version


# -----------------------------------------------------------------------------
# 3. Entity Identity Dimension Tests
# -----------------------------------------------------------------------------

def test_entity_identity_strong():
    engine = TrustEngine()
    evidence = [
        make_test_ev(
            claim="HackIndia operates official domain hackindia.org",
            evidence_text="Official legal entity name extracted from JSON-LD schema.",
            source_url="https://hackindia.org",
            source_title="Official Site",
            source_type=SourceType.OFFICIAL_COMPANY,
            reliability_score=0.95,
            verification_status=VerificationStatus.VERIFIED,
            agent_name="company_research",
            content_hash="hash_id1",
        )
    ]
    dim = engine.calculate_entity_identity_dimension(evidence, "HackIndia", "hackindia.org")
    assert dim.score >= 85.0
    assert dim.verification_status == TrustVerificationStatus.VERIFIED


def test_entity_identity_missing():
    engine = TrustEngine()
    dim = engine.calculate_entity_identity_dimension([], "Unknown Corp", None)
    assert dim.score == 50.0
    assert dim.verification_status == TrustVerificationStatus.UNABLE_TO_VERIFY
    assert dim.confidence <= 0.40


def test_entity_identity_conflicts():
    engine = TrustEngine()
    evidence = [
        make_test_ev(
            claim="Claimed domain belongs to an unrelated entity",
            evidence_text="Domain ownership mismatch.",
            source_url="https://other.com",
            source_title="Other Site",
            source_type=SourceType.OFFICIAL_COMPANY,
            reliability_score=0.80,
            verification_status=VerificationStatus.CONFLICTING,
            agent_name="company_research",
            content_hash="hash_id_conflict",
        )
    ]
    dim = engine.calculate_entity_identity_dimension(evidence, "Target Co", "target.com")
    assert dim.verification_status == TrustVerificationStatus.CONFLICTING
    assert dim.score == 55.0


# -----------------------------------------------------------------------------
# 4. Technical / Domain Provenance Dimension Tests
# -----------------------------------------------------------------------------

def test_technical_provenance_observed_https():
    engine = TrustEngine()
    evidence = [
        make_test_ev(
            claim="HTTPS is available for the observed domain hackindia.org",
            evidence_text="Domain implements standard modern web encryption (HTTPS/TLS).",
            source_url="https://hackindia.org",
            source_title="Web Infrastructure",
            source_type=SourceType.OFFICIAL_COMPANY,
            reliability_score=0.90,
            verification_status=VerificationStatus.VERIFIED,
            agent_name="technology_reputation",
            content_hash="hash_tech1",
        )
    ]
    dim = engine.calculate_technical_provenance_dimension(evidence, "hackindia.org")
    assert dim.score == 90.0
    assert dim.verification_status == TrustVerificationStatus.VERIFIED


def test_technical_provenance_missing_evidence():
    engine = TrustEngine()
    dim = engine.calculate_technical_provenance_dimension([], "example.com")
    # Missing evidence must NOT become an implicit high score!
    assert dim.score == 50.0
    assert dim.verification_status == TrustVerificationStatus.UNABLE_TO_VERIFY
    assert dim.confidence == 0.30


# -----------------------------------------------------------------------------
# 5. Regulatory / Compliance Dimension Tests
# -----------------------------------------------------------------------------

def test_regulatory_verified():
    engine = TrustEngine()
    evidence = [
        make_test_ev(
            claim="Corporate registration active on Ministry of Corporate Affairs",
            evidence_text="Government registry record verified.",
            source_url="https://mca.gov.in",
            source_title="MCA Filing",
            source_type=SourceType.GOVERNMENT,
            reliability_score=0.98,
            verification_status=VerificationStatus.VERIFIED,
            agent_name="verification",
            content_hash="hash_reg1",
        )
    ]
    dim = engine.calculate_regulatory_dimension(evidence)
    assert dim.score >= 90.0
    assert dim.verification_status == TrustVerificationStatus.VERIFIED


def test_regulatory_unavailable_never_classified_as_fraud():
    engine = TrustEngine()
    dim = engine.calculate_regulatory_dimension([])
    # Missing public registry evidence MUST be UNABLE_TO_VERIFY, NOT fraud
    assert dim.verification_status == TrustVerificationStatus.UNABLE_TO_VERIFY
    assert dim.score == 50.0
    assert dim.confidence == 0.40


def test_regulatory_conflicting():
    engine = TrustEngine()
    evidence = [
        make_test_ev(
            claim="Government registry filing status conflicted",
            evidence_text="Official registry filing returned conflicting record.",
            source_url="https://mca.gov.in",
            source_title="MCA Filing",
            source_type=SourceType.GOVERNMENT,
            reliability_score=0.80,
            verification_status=VerificationStatus.CONFLICTING,
            agent_name="verification",
            content_hash="hash_reg_conflict",
        )
    ]
    dim = engine.calculate_regulatory_dimension(evidence)
    assert dim.verification_status == TrustVerificationStatus.CONFLICTING
    assert dim.score == 40.0


# -----------------------------------------------------------------------------
# 6. Evidence Reliability & Fusion Tests
# -----------------------------------------------------------------------------

def test_evidence_fusion_same_source_deduplication():
    engine = TrustEngine()
    # 5 duplicate evidence items copying the exact same report
    dup_evidence = [
        make_test_ev(
            claim="Duplicate claim",
            evidence_text="Same copy text",
            source_url="https://blog.com/copy",
            source_type=SourceType.BLOG,
            reliability_score=0.50,
            verification_status=VerificationStatus.UNVERIFIED,
            content_hash="same_hash_123",
        )
        for _ in range(5)
    ]

    dim = engine.calculate_evidence_fusion_dimension(dup_evidence)
    # 5 duplicate copies of the same hash MUST be deduplicated to 1 unique item
    assert dim.details["unique_deduplicated"] == 1
    assert dim.details["corroboration_bonus"] == 0.0


def test_evidence_fusion_freshness_decay():
    engine = TrustEngine()
    old_date = datetime.now(timezone.utc) - timedelta(days=1000)

    old_evidence = [
        make_test_ev(
            claim="Old announcement",
            evidence_text="Published long ago",
            source_url="https://news.com/old",
            source_type=SourceType.NEWS,
            published_at=old_date,
            reliability_score=0.80,
            verification_status=VerificationStatus.UNVERIFIED,
            content_hash="old_hash_1",
        )
    ]

    factor = engine._calculate_freshness_factor(old_date, None, "news")
    assert factor <= 0.60
    dim = engine.calculate_evidence_fusion_dimension(old_evidence)
    assert dim.confidence <= 0.85



# -----------------------------------------------------------------------------
# 7. Risk Adjustment Tests
# -----------------------------------------------------------------------------

def test_risk_adjustment_recruitment_scam_separation():
    engine = TrustEngine()
    evidence = [
        make_test_ev(
            claim="Unverified recruitment fee request reported",
            evidence_text="WhatsApp message requested upfront payment for job interview.",
            source_url="https://forum.com/review",
            source_type=SourceType.FORUM,
            reliability_score=0.60,
            verification_status=VerificationStatus.UNVERIFIED,
            agent_name="risk_analysis",
            content_hash="hash_scam1",
        )
    ]

    dim = engine.calculate_risk_adjustment_dimension(evidence)
    # recruitment_scam_risk must be flagged high, but company_legitimacy_penalty remains 0.0 unless domain spoofing is proven
    assert dim.details["recruitment_scam_risk"] >= 0.80
    assert dim.details["legitimacy_penalty"] == 0.0


def test_risk_adjustment_company_legitimacy_penalty():
    engine = TrustEngine()
    evidence = [
        make_test_ev(
            claim="Unverified domain spoofing detected",
            evidence_text="Domain spoofing risk.",
            source_url="https://fake.com",
            source_type=SourceType.OTHER,
            reliability_score=0.50,
            verification_status=VerificationStatus.UNVERIFIED,
            agent_name="risk_analysis",
            content_hash="hash_spoof1",
        )
    ]

    dim = engine.calculate_risk_adjustment_dimension(evidence)
    assert dim.details["legitimacy_penalty"] == 25.0
    assert dim.score == 62.5


# -----------------------------------------------------------------------------
# 8. Conflict Model & Verification Status Tests
# -----------------------------------------------------------------------------

def test_conflict_model_severities():
    engine = TrustEngine()

    # No conflict
    summary_no = engine.evaluate_conflicts([])
    assert summary_no.conflict_level == ConflictLevel.NO_CONFLICT
    assert summary_no.confidence_penalty == 0.0

    # Minor conflict (1 item)
    minor_item = make_test_ev(
        claim="Minor conflict claim",
        evidence_text="Text",
        source_url="https://site.com",
        source_type=SourceType.OTHER,
        verification_status=VerificationStatus.CONFLICTING,
    )
    summary_minor = engine.evaluate_conflicts([minor_item])
    assert summary_minor.conflict_level == ConflictLevel.MINOR_CONFLICT
    assert summary_minor.confidence_penalty == 0.10

    # Major conflict (>=3 items)
    major_items = [
        make_test_ev(
            claim=f"Major conflict claim {i}",
            evidence_text="Text",
            source_url=f"https://site{i}.com",
            source_type=SourceType.OTHER,
            verification_status=VerificationStatus.CONFLICTING,
        )
        for i in range(3)
    ]
    summary_major = engine.evaluate_conflicts(major_items)
    assert summary_major.conflict_level == ConflictLevel.MAJOR_CONFLICT
    assert summary_major.confidence_penalty == 0.25


# -----------------------------------------------------------------------------
# 9. Score & Confidence Bounds Tests
# -----------------------------------------------------------------------------

def test_trust_index_bounds():
    engine = TrustEngine()
    # Test extreme empty evidence
    res_empty = engine.compute_trust_index([], "Empty Corp", None)
    assert 0.0 <= res_empty.trust_index <= 100.0
    assert 0.0 <= res_empty.confidence <= 1.0

    # Test extreme high evidence
    high_evidence = [
        make_test_ev(
            claim="Perfect government registration record",
            evidence_text="Verified.",
            source_url="https://gov.in",
            source_type=SourceType.GOVERNMENT,
            reliability_score=1.0,
            confidence_score=1.0,
            verification_status=VerificationStatus.VERIFIED,
        )
    ]
    res_high = engine.compute_trust_index(high_evidence, "Perfect Corp", "perfect.gov.in")
    assert 0.0 <= res_high.trust_index <= 100.0
    assert 0.0 <= res_high.confidence <= 1.0


# -----------------------------------------------------------------------------
# 10. Security Controls Regression Tests (Phase 3 Controls Preserved)
# -----------------------------------------------------------------------------

def test_phase3_security_controls_preserved():
    # Rate Limiting test on /research
    payload = {"company_name": "Security Test Co", "company_url": "https://sec.com"}
    responses = [client.post("/api/v1/research", json=payload) for _ in range(6)]
    assert responses[-1].status_code == 429

    # SSRF Protection test
    assert _is_safe_public_url("127.0.0.1") is False
    assert _is_safe_public_url("hackindia.org") is True

    # Prompt Injection helper test
    wrapped = wrap_untrusted_content("Adversarial payload")
    assert "<untrusted_web_content>" in wrapped

    # RAG Isolation test
    rag_service = RAGService()
    c_a = uuid4()
    chunks = rag_service.retrieve_similar_chunks(c_a, "Is the entity verified?", top_k=5)
    assert isinstance(chunks, list)


# -----------------------------------------------------------------------------
# 11. Phase 4 Acceptance Specific Verification Tests
# -----------------------------------------------------------------------------

def test_evidence_provenance_uuids():
    engine = TrustEngine()
    ev1 = make_test_ev(
        claim="Operates official domain hackindia.org",
        source_url="https://hackindia.org/",
        source_type=SourceType.OFFICIAL_COMPANY,
        verification_status=VerificationStatus.VERIFIED,
    )
    ev2 = make_test_ev(
        claim="HTTPS 200 OK verified on main domain",
        source_url="https://hackindia.org/",
        source_type=SourceType.OFFICIAL_COMPANY,
        verification_status=VerificationStatus.VERIFIED,
    )
    result = engine.compute_trust_index([ev1, ev2], "HackIndia", "hackindia.org")

    assert len(result.evidence_references) > 0
    for ref in result.evidence_references:
        assert "evidence_id" in ref
        assert ref["evidence_id"] != ""
        assert ref["evidence_id"] != "None"
        # Validate it's a valid UUID string
        uuid_obj = uuid4().__class__(ref["evidence_id"])
        assert str(uuid_obj) == ref["evidence_id"]

    for dim in result.dimension_scores.values():
        for eid in dim.evidence_ids:
            assert eid != ""
            assert str(uuid4().__class__(eid)) == eid


def test_technical_observability_consistency():
    engine = TrustEngine()

    # Case A: Explicit HTTPS / HTTP 200 OK evidence observed
    ev_tech = make_test_ev(
        claim="Website responds with HTTP 200 OK via HTTPS",
        evidence_text="TLS 1.3 encryption active",
        source_url="https://hackindia.org/",
        source_type=SourceType.OFFICIAL_COMPANY,
        agent_name="technology_reputation",
    )
    dim_tech_obs = engine.calculate_technical_provenance_dimension([ev_tech], "hackindia.org")
    assert dim_tech_obs.details["https_observed"] is True
    assert dim_tech_obs.details["dns_active"] is True
    assert dim_tech_obs.verification_status == TrustVerificationStatus.VERIFIED

    # Case B: No technical evidence collected
    dim_tech_empty = engine.calculate_technical_provenance_dimension([], "hackindia.org")
    assert dim_tech_empty.details["https_observed"] is False
    assert dim_tech_empty.details["dns_active"] is False
    assert dim_tech_empty.verification_status == TrustVerificationStatus.UNABLE_TO_VERIFY
    assert dim_tech_empty.score == 50.0
    assert dim_tech_empty.confidence == 0.30


def test_trust_index_timestamps():
    engine = TrustEngine()
    ev = make_test_ev(claim="Test domain claim", source_url="https://test.com")
    result = engine.compute_trust_index([ev], "Test Corp", "test.com")

    assert hasattr(result, "computed_at")
    assert hasattr(result, "updated_at")
    assert isinstance(result.computed_at, str)
    assert isinstance(result.updated_at, str)
    assert "T" in result.computed_at
    assert "T" in result.updated_at


def test_risk_wording_accuracy():
    engine = TrustEngine()
    ev = make_test_ev(claim="Official company registration", source_type=SourceType.GOVERNMENT)
    result = engine.compute_trust_index([ev], "Clean Corp", "cleancorp.com")

    assert result.dimension_scores["risk"].score == 100.0
    risk_expl = result.risk_adjustment.explanation
    assert "no configured penalties" in risk_expl.lower() or "no elevated corporate risk" in risk_expl.lower()
    assert "deterministic rule-based assessment" in risk_expl.lower()
    assert "ml classifier not yet active" in risk_expl.lower()


def test_company_and_run_isolation():
    from uuid import UUID, uuid4
    from app.repositories.company_repository import CompanyRepository
    from app.repositories.evidence_repository import EvidenceRepository
    from app.repositories.research_repository import ResearchRepository

    comp_repo = CompanyRepository()
    run_repo = ResearchRepository()
    repo = EvidenceRepository()


    name1_rand = uuid4().hex[:6]
    name2_rand = uuid4().hex[:6]

    try:
        comp1 = comp_repo.create(name=f"Iso Test Co 1 {name1_rand}", normalized_name=f"iso test co 1 {name1_rand}", official_domain="iso1.com")
        comp2 = comp_repo.create(name=f"Iso Test Co 2 {name2_rand}", normalized_name=f"iso test co 2 {name2_rand}", official_domain="iso2.com")
    except Exception as exc:
        if "row-level security" in str(exc).lower() or "42501" in str(exc):
            pytest.skip(f"Supabase RLS active without service key: {exc}")
        raise exc

    c_id_1 = UUID(comp1["id"])
    c_id_2 = UUID(comp2["id"])

    valid_user_res = run_repo.supabase.table("research_runs").select("user_id").limit(1).execute()
    dummy_user = UUID(valid_user_res.data[0]["user_id"]) if valid_user_res.data else test_user_id
    run1 = run_repo.create(user_id=dummy_user, company_id=c_id_1, status="completed")
    run2 = run_repo.create(user_id=dummy_user, company_id=c_id_2, status="completed")



    run_id_1 = UUID(run1["id"])
    run_id_2 = UUID(run2["id"])

    ev1 = repo.create(
        company_id=c_id_1,
        research_run_id=run_id_1,
        claim="Company 1 evidence",
        evidence_text="Text 1",
        source_url="https://comp1.com",
    )
    ev2 = repo.create(
        company_id=c_id_2,
        research_run_id=run_id_2,
        claim="Company 2 evidence",
        evidence_text="Text 2",
        source_url="https://comp2.com",
    )

    c1_list = repo.list_by_company_id(c_id_1)
    c2_list = repo.list_by_company_id(c_id_2)

    assert any(e["id"] == ev1["id"] for e in c1_list)
    assert not any(e["id"] == ev2["id"] for e in c1_list)
    assert any(e["id"] == ev2["id"] for e in c2_list)
    assert not any(e["id"] == ev1["id"] for e in c2_list)




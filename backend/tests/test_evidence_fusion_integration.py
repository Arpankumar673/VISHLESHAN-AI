from datetime import datetime, timezone
from uuid import uuid4
import pytest
from app.research.agents.base import AgentInput, AgentResult
from app.research.agents.evidence_trust_agent import EvidenceTrustAgent
from app.research.evidence.models import FusedClaim, FusedClaimStatus, FusionResult
from app.research.models import NormalizedEvidence
from app.research.normalizer import EvidenceNormalizer
from app.schemas.evidence import SourceType, VerificationStatus


def make_evidence(
    claim: str,
    url: str = "https://example.com",
    reliability: float = 0.90,
    text: str = None,
) -> NormalizedEvidence:
    txt = text or f"Evidence text for {claim}"
    return NormalizedEvidence(
        claim=claim,
        evidence_text=txt,
        source_url=url,
        source_title="Source Title",
        source_type=SourceType.OFFICIAL_COMPANY,
        observed_at=datetime.now(timezone.utc),
        reliability_score=reliability,
        confidence_score=0.95,
        verification_status=VerificationStatus.VERIFIED,
        agent_name="company_research_v1",
        content_hash=EvidenceNormalizer.compute_hash(claim, url, txt),
    )


# ------------------------------------------------------------
# 1. Fusion receives normalized evidence & deduplicates duplicates
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_integration_deduplication_and_fusion():
    agent = EvidenceTrustAgent()
    run_id = uuid4()
    company_id = uuid4()

    ev1 = make_evidence("Google LLC operates search", url="https://google.com/about")
    ev2_dup = make_evidence("Google LLC operates search", url="https://google.com/about")  # Identical content hash

    inp = AgentInput(
        research_run_id=run_id,
        company_id=company_id,
        company_name="Google LLC",
        previous_evidence=[ev1, ev2_dup],
    )

    result = await agent.run(inp)

    assert result.status == "completed"
    assert len(result.evidence) == 1  # 1 unique evidence item after deduplication
    assert "fusion_result" in result.metadata
    fusion_dict = result.metadata["fusion_result"]
    assert fusion_dict["total_input_evidence"] == 1
    assert fusion_dict["total_claim_groups"] == 1


# ------------------------------------------------------------
# 2. Claims grouped, independence calculated & FusedClaim produced
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_integration_claim_grouping_and_independence():
    agent = EvidenceTrustAgent()
    run_id = uuid4()
    company_id = uuid4()

    ev1 = make_evidence("Microsoft operates Azure cloud", url="https://azure.microsoft.com")
    ev2 = make_evidence("Microsoft operates Azure cloud", url="https://news.microsoft.com")
    ev3 = make_evidence("Microsoft is headquartered in Redmond", url="https://microsoft.com/about")

    inp = AgentInput(
        research_run_id=run_id,
        company_id=company_id,
        company_name="Microsoft",
        previous_evidence=[ev1, ev2, ev3],
    )

    result = await agent.run(inp)

    fusion_data = result.metadata["fusion_result"]
    assert fusion_data["total_claim_groups"] == 2  # 2 distinct claims
    fused_claims = [FusedClaim.model_validate(c) for c in fusion_data["fused_claims"]]

    azure_claim = next(c for c in fused_claims if "Azure" in c.canonical_claim)
    assert azure_claim.independent_source_count == 2
    assert azure_claim.status == FusedClaimStatus.SUPPORTED
    assert azure_claim.fused_confidence > 0.70


# ------------------------------------------------------------
# 3. Conflict detection and contradiction handling in integration
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_integration_conflict_detection_and_scoring():
    agent = EvidenceTrustAgent()
    run_id = uuid4()
    company_id = uuid4()

    ev_supp = make_evidence("Acme Corp founding year", url="https://acme.com", text="Acme Corp was founded in 2018")
    ev_contra = make_evidence("Acme Corp founding year", url="https://unverified-news.com", text="Acme Corp was founded in 2020")

    inp = AgentInput(
        research_run_id=run_id,
        company_id=company_id,
        company_name="Acme Corp",
        previous_evidence=[ev_supp, ev_contra],
    )

    result = await agent.run(inp)

    fusion_data = result.metadata["fusion_result"]
    assert fusion_data["conflicted_claims"] == 1
    fused_claims = [FusedClaim.model_validate(c) for c in fusion_data["fused_claims"]]
    assert fused_claims[0].status == FusedClaimStatus.CONFLICTED
    assert fused_claims[0].contradiction_score == 0.50
    assert len(fused_claims[0].supporting_evidence) == 1
    assert len(fused_claims[0].contradicting_evidence) == 1


# ------------------------------------------------------------
# 4. Provenance survives the complete pipeline
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_integration_provenance_preservation():
    agent = EvidenceTrustAgent()
    run_id = uuid4()
    company_id = uuid4()

    ev = make_evidence("Apple designs custom M-series chips", url="https://apple.com/m3")
    original_hash = ev.content_hash

    inp = AgentInput(
        research_run_id=run_id,
        company_id=company_id,
        company_name="Apple",
        previous_evidence=[ev],
    )

    result = await agent.run(inp)

    assert result.evidence[0].content_hash == original_hash
    assert result.evidence[0].source_url == "https://apple.com/m3"
    assert result.evidence[0].agent_name == "company_research_v1"

    fusion_data = result.metadata["fusion_result"]
    fused_claim = FusedClaim.model_validate(fusion_data["fused_claims"][0])
    assert fused_claim.supporting_evidence[0].content_hash == original_hash


# ------------------------------------------------------------
# 5. Empty evidence does not crash
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_integration_empty_evidence_resilience():
    agent = EvidenceTrustAgent()
    run_id = uuid4()
    company_id = uuid4()

    inp = AgentInput(
        research_run_id=run_id,
        company_id=company_id,
        company_name="EmptyCorp",
        previous_evidence=[],
    )

    result = await agent.run(inp)

    assert result.status == "partial"
    assert len(result.evidence) == 0
    assert result.metadata["total_claim_groups"] == 0
    assert result.metadata["avg_fused_confidence"] == 0.5


# ------------------------------------------------------------
# 6. Existing trust score behavior remains compatible
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_integration_existing_trust_score_compatibility():
    agent = EvidenceTrustAgent()
    run_id = uuid4()
    company_id = uuid4()

    ev = make_evidence("Infosys operates IT services", reliability=0.90)

    inp = AgentInput(
        research_run_id=run_id,
        company_id=company_id,
        company_name="Infosys",
        previous_evidence=[ev],
    )

    result = await agent.run(inp)

    # Legacy trust score calculation check
    assert result.metadata["preliminary_trust_score"] == 90.0
    assert result.metadata["preliminary_risk_level"] == "low"
    # New fusion metadata attached alongside
    assert "fusion_result" in result.metadata
    assert "avg_fused_confidence" in result.metadata

from datetime import datetime, timezone
from uuid import uuid4
import pytest
from app.research.agents.base import AgentInput
from app.research.agents.evidence_trust_agent import EvidenceTrustAgent
from app.research.agents.risk_analysis_agent import RiskAnalysisAgent
from app.research.models import NormalizedEvidence
from app.research.normalizer import EvidenceNormalizer
from app.schemas.evidence import SourceType, VerificationStatus


def make_ev(
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
        source_title="Title",
        source_type=SourceType.OFFICIAL_COMPANY,
        observed_at=datetime.now(timezone.utc),
        reliability_score=reliability,
        confidence_score=0.95,
        verification_status=VerificationStatus.VERIFIED,
        agent_name="company_research_v1",
        content_hash=EvidenceNormalizer.compute_hash(claim, url, txt),
    )


# ------------------------------------------------------------
# 1. Zero Conflicts -> Low Risk
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_p4a_zero_conflicts_low_risk():
    agent = RiskAnalysisAgent()
    ev1 = make_ev("Google LLC operates search", url="https://google.com/about")
    inp = AgentInput(
        research_run_id=uuid4(),
        company_id=uuid4(),
        company_name="Google LLC",
        company_url="https://google.com",
        previous_evidence=[ev1],
    )
    result = await agent.run(inp)
    assert result.metadata["overall_risk_level"] == "low"
    assert result.metadata["risk_score"] == 15
    assert result.metadata["conflicted_claims_count"] == 0


# ------------------------------------------------------------
# 2. One Minor Contradiction -> Low/Proportional Risk Penalty (NOT Automatic High Risk)
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_p4a_one_minor_contradiction_not_automatic_high_risk():
    agent = RiskAnalysisAgent()
    ev_supp = make_ev("Acme Corp founding year", url="https://acme.com", text="Acme Corp was founded in 2018")
    ev_contra = make_ev("Acme Corp founding year", url="https://minor-blog.com", text="Acme Corp was founded in 2020")
    inp = AgentInput(
        research_run_id=uuid4(),
        company_id=uuid4(),
        company_name="Acme Corp",
        company_url="https://acme.com",
        previous_evidence=[ev_supp, ev_contra],
    )
    result = await agent.run(inp)
    # 1 supp vs 1 contra -> medium conflict severity (+15 pts -> 30 pts), remaining LOW risk (NOT HIGH)
    assert result.metadata["overall_risk_level"] == "low"
    assert result.metadata["risk_score"] == 30
    assert result.metadata["medium_conflicts_count"] == 1


# ------------------------------------------------------------
# 3. Critical Identity / Domain Contradiction -> Critical Severity (High Risk)
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_p4a_critical_domain_contradiction_high_risk():
    agent = RiskAnalysisAgent()
    ev_supp = make_ev("Official corporate domain", url="https://acme.com", text="Official domain is acme.com")
    ev_contra = make_ev("Official corporate domain", url="https://spoofed-registry.com", text="Official domain is acme-fake.com")
    inp = AgentInput(
        research_run_id=uuid4(),
        company_id=uuid4(),
        company_name="Acme Corp",
        company_url="https://acme.com",
        previous_evidence=[ev_supp, ev_contra],
    )
    result = await agent.run(inp)
    assert result.metadata["overall_risk_level"] == "high"
    assert result.metadata["risk_score"] >= 70
    assert result.metadata["critical_conflicts_count"] >= 1


# ------------------------------------------------------------
# 4. Multiple Independent Contradictions -> Medium/High Risk
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_p4a_multiple_independent_contradictions():
    agent = RiskAnalysisAgent()
    ev1 = make_ev("CEO of BetaCorp", url="https://s1.com", text="CEO is Alice")
    ev2 = make_ev("CEO of BetaCorp", url="https://s2.com", text="CEO is Bob")
    ev3 = make_ev("BetaCorp headquarters", url="https://s3.com", text="Headquarters is New York")
    ev4 = make_ev("BetaCorp headquarters", url="https://s4.com", text="Headquarters is London")

    inp = AgentInput(
        research_run_id=uuid4(),
        company_id=uuid4(),
        company_name="BetaCorp",
        company_url="https://betacorp.com",
        previous_evidence=[ev1, ev2, ev3, ev4],
    )
    result = await agent.run(inp)
    assert result.metadata["conflicted_claims_count"] == 2
    assert result.metadata["high_conflicts_count"] == 2
    assert result.metadata["risk_score"] == 65  # 15 base + 25*2 high conflicts penalty
    assert result.metadata["overall_risk_level"] == "medium"


# ------------------------------------------------------------
# 5. Duplicate Contradictory Evidence Does Not Inflate Contradiction
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_p4a_duplicate_contradictory_evidence_deduplicated():
    agent = RiskAnalysisAgent()
    ev_supp = make_ev("BetaCorp founding year", url="https://s1.com", text="Founded in 2010")
    ev_contra = make_ev("BetaCorp founding year", url="https://s2.com", text="Founded in 2012")
    duplicates = [ev_contra] * 10  # 10 duplicate copies of identical evidence item

    inp = AgentInput(
        research_run_id=uuid4(),
        company_id=uuid4(),
        company_name="BetaCorp",
        company_url="https://betacorp.com",
        previous_evidence=[ev_supp] + duplicates,
    )
    result = await agent.run(inp)
    # Deduplication reduces duplicates to 1 independent item -> 1 conflict
    assert result.metadata["conflicted_claims_count"] == 1
    assert result.metadata["medium_conflicts_count"] == 1
    assert result.metadata["risk_score"] == 30


# ------------------------------------------------------------
# 6 & 7. Strong Supporting vs Weak Contradiction
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_p4a_strong_supporting_vs_weak_contradiction():
    agent = RiskAnalysisAgent()
    ev1 = make_ev("BetaCorp founding year", url="https://s1.com", text="Founded in 2010")
    ev2 = make_ev("BetaCorp founding year", url="https://s2.com", text="Founded in 2010")
    ev3 = make_ev("BetaCorp founding year", url="https://s3.com", text="Founded in 2010")
    ev_weak = make_ev("BetaCorp founding year", url="https://random-forum.com", text="Founded in 2012", reliability=0.20)

    inp = AgentInput(
        research_run_id=uuid4(),
        company_id=uuid4(),
        company_name="BetaCorp",
        company_url="https://betacorp.com",
        previous_evidence=[ev1, ev2, ev3, ev_weak],
    )
    result = await agent.run(inp)
    # 3 supp vs 1 weak contra -> agreement_score = 0.75 >= 0.70 -> minor conflict (+5 pts -> 20 pts)
    assert result.metadata["minor_conflicts_count"] == 1
    assert result.metadata["risk_score"] == 20
    assert result.metadata["overall_risk_level"] == "low"


# ------------------------------------------------------------
# 8. Low Evidence Volume -> Insufficient Evidence Warning
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_p4a_low_evidence_volume():
    agent = RiskAnalysisAgent()
    inp = AgentInput(
        research_run_id=uuid4(),
        company_id=uuid4(),
        company_name="TinyCorp",
        company_url="https://tinycorp.com",
        previous_evidence=[],
    )
    result = await agent.run(inp)
    sufficiency_finding = next(f for f in result.findings if f.get("risk_type") == "evidence_sufficiency")
    assert sufficiency_finding["status"] == "insufficient_evidence"
    assert sufficiency_finding["confidence"] == 0.30


# ------------------------------------------------------------
# 9. Unresolved Identity -> Medium Risk, Low Confidence (NOT Fraud)
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_p4a_unresolved_identity_not_fraud():
    agent = RiskAnalysisAgent()
    inp = AgentInput(
        research_run_id=uuid4(),
        company_id=uuid4(),
        company_name="Unknown Entity",
        company_url=None,  # No domain
        previous_evidence=[],
    )
    result = await agent.run(inp)
    assert result.metadata["overall_risk_level"] == "medium"
    assert result.metadata["risk_score"] == 45
    assert result.metadata["overall_confidence"] == 0.40  # Low confidence, NOT high risk/fraud


# ------------------------------------------------------------
# 10 & 11. Recruitment Spoofing and Domain Provenance
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_p4a_existing_recruitment_and_domain_provenance():
    agent = RiskAnalysisAgent()
    inp = AgentInput(
        research_run_id=uuid4(),
        company_id=uuid4(),
        company_name="Verified Company",
        company_url="https://verified.com",
        previous_evidence=[make_ev("Operating domain verified", url="https://verified.com")],
    )
    result = await agent.run(inp)
    domain_ind = next(i for i in result.metadata["indicators"] if i["indicator_type"] == "domain_provenance")
    hiring_ind = next(i for i in result.metadata["indicators"] if i["indicator_type"] == "recruitment_spoofing_risk")

    assert domain_ind["status"] == "passed"
    assert hiring_ind["status"] == "passed"


# ------------------------------------------------------------
# 12. Fused Metrics Preserved in Metadata
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_p4a_fused_metrics_preserved():
    agent = EvidenceTrustAgent()
    ev = make_ev("Sample claim", url="https://sample.com")
    inp = AgentInput(
        research_run_id=uuid4(),
        company_id=uuid4(),
        company_name="Sample Corp",
        previous_evidence=[ev],
    )
    result = await agent.run(inp)
    assert "fusion_result" in result.metadata
    assert "avg_fused_confidence" in result.metadata
    assert "fused_trust_candidate" in result.metadata
    assert result.metadata["fused_trust_candidate_label"] == "diagnostic_experimental"


# ------------------------------------------------------------
# 13. Existing Trust Score Unchanged
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_p4a_existing_trust_score_unchanged():
    agent = EvidenceTrustAgent()
    ev = make_ev("Test claim", reliability=0.88)
    inp = AgentInput(
        research_run_id=uuid4(),
        company_id=uuid4(),
        company_name="Test Corp",
        previous_evidence=[ev],
    )
    result = await agent.run(inp)
    assert result.metadata["preliminary_trust_score"] == 88.0
    assert result.metadata["preliminary_risk_level"] == "low"


# ------------------------------------------------------------
# 14. Candidate Trust Bounded 20..100
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_p4a_candidate_trust_bounded():
    agent = EvidenceTrustAgent()
    ev = make_ev("Bounds claim")
    inp = AgentInput(
        research_run_id=uuid4(),
        company_id=uuid4(),
        company_name="Bounds Corp",
        previous_evidence=[ev],
    )
    result = await agent.run(inp)
    cand = result.metadata["fused_trust_candidate"]
    assert 20.0 <= cand <= 100.0


# ------------------------------------------------------------
# 15. Risk Score Bounded 0..100
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_p4a_risk_score_bounded():
    agent = RiskAnalysisAgent()
    ev = make_ev("Extreme claim")
    inp = AgentInput(
        research_run_id=uuid4(),
        company_id=uuid4(),
        company_name="Extreme Corp",
        previous_evidence=[ev],
    )
    result = await agent.run(inp)
    score = result.metadata["risk_score"]
    assert 0 <= score <= 100

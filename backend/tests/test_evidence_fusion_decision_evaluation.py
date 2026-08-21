from datetime import datetime, timezone
from uuid import uuid4
import pytest
from app.research.agents.base import AgentInput
from app.research.agents.evidence_trust_agent import EvidenceTrustAgent
from app.research.agents.risk_analysis_agent import RiskAnalysisAgent
from app.research.evidence.grouping import group_evidence
from app.research.evidence.scoring import score_fusion_result
from app.research.models import NormalizedEvidence
from app.research.normalizer import EvidenceNormalizer
from app.schemas.evidence import SourceType, VerificationStatus


def make_ev(
    claim: str,
    url: str = "https://example.com",
    reliability: float = 0.90,
    text: str = None,
    verification: VerificationStatus = VerificationStatus.VERIFIED,
    source_type: SourceType = SourceType.OFFICIAL_COMPANY,
) -> NormalizedEvidence:
    txt = text or f"Evidence text for {claim}"
    return NormalizedEvidence(
        claim=claim,
        evidence_text=txt,
        source_url=url,
        source_title="Title",
        source_type=source_type,
        observed_at=datetime.now(timezone.utc),
        reliability_score=reliability,
        confidence_score=0.95,
        verification_status=verification,
        agent_name="company_research_v1",
        content_hash=EvidenceNormalizer.compute_hash(claim, url, txt),
    )


async def evaluate_scenario(
    company_name: str,
    domain: str,
    evidence_list: list[NormalizedEvidence],
    context: dict = None,
):
    trust_agent = EvidenceTrustAgent()
    risk_agent = RiskAnalysisAgent()

    inp = AgentInput(
        research_run_id=uuid4(),
        company_id=uuid4(),
        company_name=company_name,
        company_url=domain,
        previous_evidence=evidence_list,
        context=context or {},
    )

    trust_res = await trust_agent.run(inp)
    risk_res = await risk_agent.run(inp)

    claim_groups = group_evidence(evidence_list)
    fusion_result = score_fusion_result(claim_groups)

    first_fc = fusion_result.fused_claims[0] if fusion_result.fused_claims else None

    return {
        "preliminary_trust_score": trust_res.metadata.get("preliminary_trust_score"),
        "fused_trust_candidate": trust_res.metadata.get("fused_trust_candidate"),
        "overall_confidence": risk_res.metadata.get("overall_confidence"),
        "risk_score": risk_res.metadata.get("risk_score"),
        "risk_level": risk_res.metadata.get("overall_risk_level"),
        "conflicted_claims_count": fusion_result.conflicted_claims,
        "independent_source_count": first_fc.independent_source_count if first_fc else 0,
        "evidence_strength": round(first_fc.evidence_strength, 2) if first_fc else 0.0,
        "agreement_score": round(first_fc.agreement_score, 2) if first_fc else 0.0,
        "contradiction_score": round(first_fc.contradiction_score, 2) if first_fc else 0.0,
        "explanation": first_fc.explanation if first_fc else "No claims evaluated.",
    }


# ============================================================
# 1. VERIFIED_COMPANY Scenario
# ============================================================
@pytest.mark.asyncio
async def test_scenario_1_verified_company():
    ev1 = make_ev("Google LLC operates search", url="https://google.com/about", reliability=0.95)
    ev2 = make_ev("Google LLC operates search", url="https://alphabet.com/investors", reliability=0.90)
    ev3 = make_ev("Google LLC operates search", url="https://wikipedia.org/wiki/Google", reliability=0.85)

    res = await evaluate_scenario("Google LLC", "https://google.com", [ev1, ev2, ev3])

    assert res["risk_level"] == "low"
    assert res["risk_score"] == 15
    assert res["overall_confidence"] >= 0.85
    assert res["preliminary_trust_score"] >= 85.0
    assert res["conflicted_claims_count"] == 0


# ============================================================
# 2. LOW_EVIDENCE Scenario
# ============================================================
@pytest.mark.asyncio
async def test_scenario_2_low_evidence():
    ev1 = make_ev(
        "TinyCorp operates software",
        url="https://unverified-blog.com",
        reliability=0.40,
        verification=VerificationStatus.UNVERIFIED,
    )

    res = await evaluate_scenario("TinyCorp", None, [ev1])

    assert res["risk_level"] == "medium"  # Missing domain -> 45 risk (NOT HIGH / FRAUD)
    assert res["risk_score"] == 45
    assert res["overall_confidence"] <= 0.45  # Low confidence
    assert res["conflicted_claims_count"] == 0


# ============================================================
# 3. MINOR_CONTRADICTION Scenario
# ============================================================
@pytest.mark.asyncio
async def test_scenario_3_minor_contradiction():
    ev_supp = make_ev("Acme Corp founding year", url="https://acme.com", text="Acme Corp was founded in 2018")
    ev_contra = make_ev("Acme Corp founding year", url="https://minor-blog.com", text="Acme Corp was founded in 2020")

    res = await evaluate_scenario("Acme Corp", "https://acme.com", [ev_supp, ev_contra])

    assert res["risk_level"] == "low"  # 15 base + 15 penalty = 30 (LOW, NOT HIGH)
    assert res["risk_score"] == 30
    assert res["conflicted_claims_count"] == 1


# ============================================================
# 4. MULTIPLE_INDEPENDENT_CONTRADICTIONS Scenario
# ============================================================
@pytest.mark.asyncio
async def test_scenario_4_multiple_independent_contradictions():
    ev1 = make_ev("CEO of BetaCorp", url="https://s1.com", text="CEO is Alice")
    ev2 = make_ev("CEO of BetaCorp", url="https://s2.com", text="CEO is Bob")
    ev3 = make_ev("BetaCorp headquarters", url="https://s3.com", text="Headquarters is New York")
    ev4 = make_ev("BetaCorp headquarters", url="https://s4.com", text="Headquarters is London")

    res = await evaluate_scenario("BetaCorp", "https://betacorp.com", [ev1, ev2, ev3, ev4])

    assert res["conflicted_claims_count"] == 2
    assert res["risk_score"] == 65  # 15 base + 25*2 high conflicts = 65
    assert res["risk_level"] == "medium"


# ============================================================
# 5. DOMAIN_COLLISION Scenario
# ============================================================
@pytest.mark.asyncio
async def test_scenario_5_domain_collision():
    ev_supp = make_ev("Official corporate domain", url="https://acme.com", text="Official domain is acme.com")
    ev_contra = make_ev("Official corporate domain", url="https://spoofed-registry.com", text="Official domain is acme-fake.com")

    res = await evaluate_scenario("Acme Corp", "https://acme.com", [ev_supp, ev_contra])

    assert res["risk_level"] == "high"
    assert res["risk_score"] == 100
    assert res["conflicted_claims_count"] == 1


# ============================================================
# 6. RECRUITMENT_SPOOFING Scenario
# ============================================================
@pytest.mark.asyncio
async def test_scenario_6_recruitment_spoofing():
    ev_spoof = NormalizedEvidence(
        claim="Recruitment domain mismatch",
        evidence_text="Job offers sent from fake-acme-jobs.com",
        source_url="https://fake-acme-jobs.com",
        source_type=SourceType.OTHER,
        observed_at=datetime.now(timezone.utc),
        reliability_score=0.70,
        confidence_score=0.80,
        verification_status=VerificationStatus.CONFLICTING,
        agent_name="news_hiring",
        content_hash="c" * 64,
    )

    res = await evaluate_scenario("Acme Corp", "https://acme.com", [ev_spoof])

    assert res["risk_level"] == "high"
    assert res["risk_score"] == 75


# ============================================================
# 7. STRONG_SUPPORT_WEAK_CONTRADICTION Scenario
# ============================================================
@pytest.mark.asyncio
async def test_scenario_7_strong_support_weak_contradiction():
    ev1 = make_ev("BetaCorp founding year", url="https://s1.com", text="Founded in 2010", reliability=0.90)
    ev2 = make_ev("BetaCorp founding year", url="https://s2.com", text="Founded in 2010", reliability=0.90)
    ev3 = make_ev("BetaCorp founding year", url="https://s3.com", text="Founded in 2010", reliability=0.90)
    ev_weak = make_ev("BetaCorp founding year", url="https://random-forum.com", text="Founded in 2012", reliability=0.20)

    res = await evaluate_scenario("BetaCorp", "https://betacorp.com", [ev1, ev2, ev3, ev_weak])

    assert res["agreement_score"] == 0.75
    assert res["contradiction_score"] == 0.25
    assert res["risk_score"] == 20  # 15 base + 5 minor conflict penalty = 20
    assert res["risk_level"] == "low"


# ============================================================
# 8. WEAK_SUPPORT_STRONG_CONTRADICTION Scenario
# ============================================================
@pytest.mark.asyncio
async def test_scenario_8_weak_support_strong_contradiction():
    ev_weak = make_ev("CEO of BetaCorp", url="https://random-blog.com", text="CEO is Alice", reliability=0.30)
    ev_strong1 = make_ev("CEO of BetaCorp", url="https://sec.gov", text="CEO is Bob", reliability=0.95)
    ev_strong2 = make_ev("CEO of BetaCorp", url="https://betacorp.com/executives", text="CEO is Bob", reliability=0.95)

    res = await evaluate_scenario("BetaCorp", "https://betacorp.com", [ev_weak, ev_strong1, ev_strong2])

    assert res["agreement_score"] == 0.67
    assert res["contradiction_score"] == 0.33
    assert res["risk_score"] == 30  # 15 base + 15 medium conflict penalty = 30
    assert res["risk_level"] == "low"


# ============================================================
# Evaluative Property Tests: Bounds, Monotonicity & Sensitivity
# ============================================================
@pytest.mark.asyncio
async def test_eval_score_bounds():
    agent_trust = EvidenceTrustAgent()
    agent_risk = RiskAnalysisAgent()
    ev = make_ev("Bounds claim")
    inp = AgentInput(research_run_id=uuid4(), company_id=uuid4(), company_name="Test", previous_evidence=[ev])

    t_res = await agent_trust.run(inp)
    r_res = await agent_risk.run(inp)

    assert 20.0 <= t_res.metadata["preliminary_trust_score"] <= 100.0
    assert 20.0 <= t_res.metadata["fused_trust_candidate"] <= 100.0
    assert 0 <= r_res.metadata["risk_score"] <= 100
    assert 0.0 <= r_res.metadata["overall_confidence"] <= 1.0


@pytest.mark.asyncio
async def test_eval_monotonicity_more_support():
    ev1 = make_ev("Claim A", url="https://s1.com", text="Founded 2010")
    ev2 = make_ev("Claim A", url="https://s2.com", text="Founded 2010")

    res1 = await evaluate_scenario("Company", "https://company.com", [ev1])
    res2 = await evaluate_scenario("Company", "https://company.com", [ev1, ev2])

    # Adding independent corroborated supporting evidence must not decrease confidence
    assert res2["overall_confidence"] >= res1["overall_confidence"]
    assert res2["evidence_strength"] >= res1["evidence_strength"]


@pytest.mark.asyncio
async def test_eval_duplicate_resistance():
    ev1 = make_ev("Claim A", url="https://s1.com", text="Founded 2010")
    ev_dup = make_ev("Claim A", url="https://s1.com", text="Founded 2010")  # Exact duplicate

    res1 = await evaluate_scenario("Company", "https://company.com", [ev1])
    res2 = await evaluate_scenario("Company", "https://company.com", [ev1, ev_dup])

    # Duplicates should be deduplicated and not inflate independent source count or trust artificially
    assert res1["independent_source_count"] == res2["independent_source_count"] == 1
    assert res1["preliminary_trust_score"] == res2["preliminary_trust_score"]


@pytest.mark.asyncio
async def test_eval_contradiction_sensitivity():
    ev1 = make_ev("CEO of BetaCorp", url="https://s1.com", text="CEO is Alice")
    ev2 = make_ev("CEO of BetaCorp", url="https://s2.com", text="CEO is Bob")

    res_no_conflict = await evaluate_scenario("BetaCorp", "https://betacorp.com", [ev1])
    res_conflict = await evaluate_scenario("BetaCorp", "https://betacorp.com", [ev1, ev2])

    assert res_conflict["risk_score"] > res_no_conflict["risk_score"]
    assert res_conflict["conflicted_claims_count"] == 1


@pytest.mark.asyncio
async def test_eval_backward_compatibility():
    ev1 = make_ev("Claim 1", reliability=0.88)
    res = await evaluate_scenario("Company", "https://company.com", [ev1])

    assert res["preliminary_trust_score"] == 88.0

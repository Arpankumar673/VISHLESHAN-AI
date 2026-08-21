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


async def evaluate_matrix_scenario(
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
        "agreement_score": round(first_fc.agreement_score, 2) if first_fc else 0.0,
        "contradiction_score": round(first_fc.contradiction_score, 2) if first_fc else 0.0,
        "independent_source_count": first_fc.independent_source_count if first_fc else 0,
    }


# ============================================================
# Scenario A: 1 strong source
# ============================================================
@pytest.mark.asyncio
async def test_matrix_a_one_strong_source():
    ev = make_ev("Google LLC operates search", url="https://google.com/about", reliability=0.95)
    res = await evaluate_matrix_scenario("Google LLC", "https://google.com", [ev])

    assert res["preliminary_trust_score"] == 95.0
    assert res["fused_trust_candidate"] == 86.0
    assert res["agreement_score"] == 1.0
    assert res["contradiction_score"] == 0.0
    assert res["independent_source_count"] == 1


# ============================================================
# Scenario B: 2 independent strong supporting sources
# ============================================================
@pytest.mark.asyncio
async def test_matrix_b_two_independent_strong_supporting():
    ev1 = make_ev("Google LLC operates search", url="https://google.com/about", reliability=0.95)
    ev2 = make_ev("Google LLC operates search", url="https://alphabet.com/investors", reliability=0.90)
    res = await evaluate_matrix_scenario("Google LLC", "https://google.com", [ev1, ev2])

    assert res["preliminary_trust_score"] == 92.5
    assert res["fused_trust_candidate"] == 91.5
    assert res["agreement_score"] == 1.0
    assert res["independent_source_count"] == 2


# ============================================================
# Scenario C: 3 independent strong supporting sources
# ============================================================
@pytest.mark.asyncio
async def test_matrix_c_three_independent_strong_supporting():
    ev1 = make_ev("Google LLC operates search", url="https://google.com/about", reliability=0.95)
    ev2 = make_ev("Google LLC operates search", url="https://alphabet.com/investors", reliability=0.90)
    ev3 = make_ev("Google LLC operates search", url="https://wikipedia.org/wiki/Google", reliability=0.85)
    res = await evaluate_matrix_scenario("Google LLC", "https://google.com", [ev1, ev2, ev3])

    assert res["preliminary_trust_score"] == 90.0
    assert res["fused_trust_candidate"] == 97.0
    assert res["agreement_score"] == 1.0
    assert res["independent_source_count"] == 3


# ============================================================
# Scenario D: 3 strong support + 1 weak contradiction
# ============================================================
@pytest.mark.asyncio
async def test_matrix_d_three_strong_support_one_weak_contradiction():
    ev1 = make_ev("BetaCorp founding year", url="https://s1.com", reliability=0.90, text="Founded in 2010")
    ev2 = make_ev("BetaCorp founding year", url="https://s2.com", reliability=0.90, text="Founded in 2010")
    ev3 = make_ev("BetaCorp founding year", url="https://s3.com", reliability=0.90, text="Founded in 2010")
    ev_weak = make_ev("BetaCorp founding year", url="https://random-forum.com", reliability=0.20, text="Founded in 2012")

    res = await evaluate_matrix_scenario("BetaCorp", "https://betacorp.com", [ev1, ev2, ev3, ev_weak])

    assert res["preliminary_trust_score"] == 72.5
    assert res["fused_trust_candidate"] == 63.7
    assert res["agreement_score"] == 0.75
    assert res["contradiction_score"] == 0.25
    assert res["independent_source_count"] == 4


# ============================================================
# Scenario E: 1 strong support + 1 equally strong contradiction
# ============================================================
@pytest.mark.asyncio
async def test_matrix_e_one_strong_support_one_strong_contradiction():
    ev_supp = make_ev("Acme Corp founding year", url="https://acme.com", reliability=0.90, text="Acme Corp was founded in 2018")
    ev_contra = make_ev("Acme Corp founding year", url="https://minor-blog.com", reliability=0.90, text="Acme Corp was founded in 2020")

    res = await evaluate_matrix_scenario("Acme Corp", "https://acme.com", [ev_supp, ev_contra])

    assert res["preliminary_trust_score"] == 90.0
    assert res["fused_trust_candidate"] == 31.7  # Calibrated score (was collapsed to 20.0 floor!)
    assert res["agreement_score"] == 0.50
    assert res["contradiction_score"] == 0.50
    assert res["independent_source_count"] == 2


# ============================================================
# Scenario F: 2 strong support + 1 strong contradiction
# ============================================================
@pytest.mark.asyncio
async def test_matrix_f_two_strong_support_one_strong_contradiction():
    ev1 = make_ev("CEO of BetaCorp", url="https://s1.com", reliability=0.90, text="CEO is Bob")
    ev2 = make_ev("CEO of BetaCorp", url="https://s2.com", reliability=0.90, text="CEO is Bob")
    ev3 = make_ev("CEO of BetaCorp", url="https://s3.com", reliability=0.90, text="CEO is Alice")

    res = await evaluate_matrix_scenario("BetaCorp", "https://betacorp.com", [ev1, ev2, ev3])

    assert res["preliminary_trust_score"] == 90.0
    assert res["fused_trust_candidate"] == 50.4  # Retains moderate score (was 39.1)
    assert res["agreement_score"] == 0.67
    assert res["contradiction_score"] == 0.33
    assert res["independent_source_count"] == 3


# ============================================================
# Scenario G: 1 weak support + 1 strong contradiction
# ============================================================
@pytest.mark.asyncio
async def test_matrix_g_one_weak_support_one_strong_contradiction():
    ev_weak = make_ev("CEO of BetaCorp", url="https://random-blog.com", reliability=0.30, text="CEO is Alice")
    ev_strong1 = make_ev("CEO of BetaCorp", url="https://sec.gov", reliability=0.95, text="CEO is Bob")
    ev_strong2 = make_ev("CEO of BetaCorp", url="https://betacorp.com/executives", reliability=0.95, text="CEO is Bob")

    res = await evaluate_matrix_scenario("BetaCorp", "https://betacorp.com", [ev_weak, ev_strong1, ev_strong2])

    assert res["preliminary_trust_score"] == 73.3
    assert res["fused_trust_candidate"] == 51.2
    assert res["agreement_score"] == 0.67
    assert res["contradiction_score"] == 0.33
    assert res["independent_source_count"] == 3


# ============================================================
# Scenario H: multiple strong independent contradictions
# ============================================================
@pytest.mark.asyncio
async def test_matrix_h_multiple_strong_independent_contradictions():
    ev1 = make_ev("CEO of BetaCorp", url="https://s1.com", text="CEO is Alice")
    ev2 = make_ev("CEO of BetaCorp", url="https://s2.com", text="CEO is Bob")
    ev3 = make_ev("BetaCorp headquarters", url="https://s3.com", text="Headquarters is New York")
    ev4 = make_ev("BetaCorp headquarters", url="https://s4.com", text="Headquarters is London")

    res = await evaluate_matrix_scenario("BetaCorp", "https://betacorp.com", [ev1, ev2, ev3, ev4])

    assert res["preliminary_trust_score"] == 90.0
    assert res["fused_trust_candidate"] == 31.7
    assert res["agreement_score"] == 0.50
    assert res["contradiction_score"] == 0.50


# ============================================================
# Scenario I: critical domain collision
# ============================================================
@pytest.mark.asyncio
async def test_matrix_i_critical_domain_collision():
    ev_supp = make_ev("Official corporate domain", url="https://acme.com", text="Official domain is acme.com")
    ev_contra = make_ev("Official corporate domain", url="https://spoofed-registry.com", text="Official domain is acme-fake.com")

    res = await evaluate_matrix_scenario("Acme Corp", "https://acme.com", [ev_supp, ev_contra])

    assert res["preliminary_trust_score"] == 90.0
    assert res["fused_trust_candidate"] == 31.7
    assert res["agreement_score"] == 0.50


# ============================================================
# Scenario J: duplicated copies of the same evidence
# ============================================================
@pytest.mark.asyncio
async def test_matrix_j_duplicated_copies():
    ev = make_ev("Claim A", url="https://s1.com", reliability=0.90)
    ev_dup = make_ev("Claim A", url="https://s1.com", reliability=0.90)

    res1 = await evaluate_matrix_scenario("Company", "https://company.com", [ev])
    res2 = await evaluate_matrix_scenario("Company", "https://company.com", [ev, ev_dup])

    assert res1["fused_trust_candidate"] == res2["fused_trust_candidate"] == 84.5
    assert res1["independent_source_count"] == res2["independent_source_count"] == 1


# ============================================================
# Scenario K: all evidence unverified
# ============================================================
@pytest.mark.asyncio
async def test_matrix_k_all_unverified():
    ev1 = make_ev("Unverified Claim", url="https://blog.com", reliability=0.40, verification=VerificationStatus.UNVERIFIED)

    res = await evaluate_matrix_scenario("Company", "https://company.com", [ev1])

    assert res["preliminary_trust_score"] == 40.0
    assert res["fused_trust_candidate"] == 57.0
    assert res["agreement_score"] == 1.0


# ============================================================
# Scenario L: empty evidence
# ============================================================
@pytest.mark.asyncio
async def test_matrix_l_empty_evidence():
    res = await evaluate_matrix_scenario("EmptyCorp", "https://empty.com", [])

    assert res["preliminary_trust_score"] == 50.0  # Default fallback
    assert res["fused_trust_candidate"] == 50.0  # Default fallback
    assert res["independent_source_count"] == 0

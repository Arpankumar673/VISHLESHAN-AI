import asyncio
from uuid import uuid4
from app.research.agents.orchestrator import MultiAgentOrchestrator


async def main():
    orchestrator = MultiAgentOrchestrator()
    test_run_id = uuid4()
    test_company_id = uuid4()

    print(">>> Launching M5 Multi-Agent Orchestration for 'Google' (google.com)...")
    result = await orchestrator.execute_run(
        research_run_id=test_run_id,
        company_id=test_company_id,
        company_name="Google",
        company_url="google.com",
    )

    print(f"\n>>> Multi-Agent Orchestration Run Status: {result.status}")
    print(f">>> Canonical Identity: {result.identity.canonical_name}")
    print(f">>> Official Domain: {result.identity.official_domain}")
    print(f">>> Total Corroborated Evidence Items: {len(result.evidence_items)}")

    # Display evidence collected across specialized agents
    for idx, ev in enumerate(result.evidence_items, 1):
        print(f"\n--- Evidence [{idx}] by [{ev.agent_name}] ---")
        print(f"Claim: {ev.claim}")
        print(f"Source URL: {ev.source_url}")
        print(f"Source Type: {ev.source_type}")
        print(f"Reliability: {ev.reliability_score}")
        print(f"Verification: {ev.verification_status}")
        print(f"SHA-256 Hash: {ev.content_hash}")

    print("\n>>> M5 Multi-Agent Verification Complete!")


if __name__ == "__main__":
    asyncio.run(main())

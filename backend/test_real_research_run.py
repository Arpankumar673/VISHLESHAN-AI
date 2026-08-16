import asyncio
import json
from uuid import uuid4
from app.research.engine import ResearchEngine


async def main():
    engine = ResearchEngine()
    test_run_id = uuid4()
    test_company_id = uuid4()

    print(">>> Executing Real Research Engine for: 'Google' (domain: 'google.com')...")
    result = await engine.run(
        research_run_id=test_run_id,
        company_id=test_company_id,
        company_name="Google",
        company_url="google.com",
    )

    print(f"\n>>> Research Run Status: {result.status}")
    print(f">>> Canonical Name: {result.identity.canonical_name}")
    print(f">>> Official Domain: {result.identity.official_domain}")
    print(f">>> Official Website: {result.identity.official_website}")
    print(f">>> Description: {result.identity.description[:120]}...")
    print(f">>> Total Evidence Collected: {len(result.evidence_items)}")

    for idx, ev in enumerate(result.evidence_items, 1):
        print(f"\n--- Evidence Item {idx} ---")
        print(f"Claim: {ev.claim}")
        print(f"Source URL: {ev.source_url}")
        print(f"Source Title: {ev.source_title}")
        print(f"Source Type: {ev.source_type}")
        print(f"Reliability Score: {ev.reliability_score}")
        print(f"Verification Status: {ev.verification_status}")
        print(f"SHA-256 Hash: {ev.content_hash}")

    print("\n>>> Real Manual Test Complete!")


if __name__ == "__main__":
    asyncio.run(main())

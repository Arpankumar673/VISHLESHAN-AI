import asyncio
import sys
import os

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from uuid import uuid4
from app.services.research_service import ResearchService

async def main():
    service = ResearchService()
    test_user_id = uuid4()
    company_name = "TCS"
    company_url = "tcs.com"

    print(f"Starting research run for {company_name}...")
    res = await service.start_research(
        user_id=test_user_id,
        company_name=company_name,
        company_url=company_url,
    )
    print(f"StartResearch returned: run_id={res.research_run_id}, status={res.status}")

    # Check status via service
    status_res = service.get_research_status(res.research_run_id, test_user_id)
    print(f"GetResearchStatus returned: status={status_res.status}, report_id={status_res.report_id}")

if __name__ == "__main__":
    asyncio.run(main())

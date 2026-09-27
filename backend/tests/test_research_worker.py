from uuid import uuid4
import pytest
from app.workers.research_worker import WorkerSettings, run_research


def test_worker_settings_configuration():
    assert len(WorkerSettings.functions) == 1
    assert WorkerSettings.functions[0] == run_research
    assert WorkerSettings.max_jobs == 10
    assert WorkerSettings.job_timeout == 300
    assert WorkerSettings.max_tries == 3


@pytest.mark.asyncio
async def test_run_research_nonexistent_run_handling():
    ctx = {}
    fake_run_id = str(uuid4())
    res = await run_research(
        ctx=ctx,
        research_run_id_str=fake_run_id,
        company_name="Nonexistent Corp",
    )
    assert res["status"] == "error"
    assert "not found" in res["message"]

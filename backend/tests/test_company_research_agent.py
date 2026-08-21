from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
import pytest
from app.research.agents.base import AgentInput, AgentResponse, AgentResult
from app.research.agents.company_research_agent import CompanyResearchAgent
from app.research.models import NormalizedEvidence, SourceFinding
from app.research.sources.search import PublicSearchAdapter
from app.schemas.evidence import SourceType, VerificationStatus


# ------------------------------------------------------------
# 1. Standard Execution via AgentInput
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_company_research_agent_with_agent_input():
    mock_search = AsyncMock()
    mock_search.collect.return_value = [
        SourceFinding(
            claim="Microsoft Corporation public summary",
            evidence_text="Software corporation.",
            source_url="https://en.wikipedia.org/wiki/Microsoft",
            source_type=SourceType.NEWS,
        )
    ]
    mock_official = AsyncMock()
    mock_official.collect.return_value = [
        SourceFinding(
            claim="Microsoft Corporation operates official domain microsoft.com",
            evidence_text="Official site.",
            source_url="https://microsoft.com",
            source_type=SourceType.OFFICIAL_COMPANY,
        )
    ]

    agent = CompanyResearchAgent(search_adapter=mock_search, official_adapter=mock_official)
    run_id = uuid4()
    company_id = uuid4()

    inp = AgentInput(
        research_run_id=run_id,
        company_id=company_id,
        company_name="Microsoft Corporation",
        company_url="https://www.microsoft.com",
    )

    result = await agent.run(inp)

    assert isinstance(result, AgentResult)
    assert isinstance(result, AgentResponse)  # Backward-compatible check
    assert result.agent_name == "company_research"
    assert result.status in ("completed", "partial")
    assert result.research_run_id == run_id
    assert result.execution_time_ms > 0.0
    assert result.metadata["company_name"] == "Microsoft Corporation"
    assert result.metadata["resolved_domain"] == "microsoft.com"
    assert len(result.evidence) > 0
    assert all(isinstance(e, NormalizedEvidence) for e in result.evidence)
    assert all(len(e.content_hash) == 64 for e in result.evidence)


# ------------------------------------------------------------
# 2. Backward Compatibility with Legacy Positional / Keyword Arguments
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_company_research_agent_legacy_signature():
    mock_search = AsyncMock()
    mock_search.collect.return_value = [
        SourceFinding(
            claim="Apple Inc. public summary",
            evidence_text="Consumer electronics company.",
            source_url="https://en.wikipedia.org/wiki/Apple_Inc.",
            source_type=SourceType.NEWS,
        )
    ]
    mock_official = AsyncMock()
    mock_official.collect.return_value = [
        SourceFinding(
            claim="Apple Inc. operates official domain apple.com",
            evidence_text="Official website.",
            source_url="https://apple.com",
            source_type=SourceType.OFFICIAL_COMPANY,
        )
    ]

    agent = CompanyResearchAgent(search_adapter=mock_search, official_adapter=mock_official)
    run_id = uuid4()
    company_id = uuid4()

    result = await agent.execute(
        research_run_id=run_id,
        company_id=company_id,
        company_name="Apple Inc.",
        domain="apple.com",
    )

    assert isinstance(result, AgentResult)
    assert result.agent_name == "company_research"
    assert result.status in ("completed", "partial")
    assert result.research_run_id == run_id
    assert len(result.evidence) > 0


# ------------------------------------------------------------
# 3. Missing Domain & No Domain Guessing
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_company_research_agent_missing_url_no_guessing():
    agent = CompanyResearchAgent()
    run_id = uuid4()
    company_id = uuid4()

    # URL is completely omitted
    inp = AgentInput(
        research_run_id=run_id,
        company_id=company_id,
        company_name="Random Unlisted Entity",
        company_url=None,
    )

    result = await agent.execute(inp)

    # Domain MUST remain None — never guessed as randomunlistedentity.com
    assert result.metadata["resolved_domain"] is None
    assert any("Official corporate domain for 'Random Unlisted Entity' was not provided" in w for w in result.warnings)


# ------------------------------------------------------------
# 4. Mocked Adapters & Evidence Structuring
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_company_research_agent_structured_findings_and_evidence():
    mock_search = AsyncMock()
    mock_search.collect.return_value = [
        SourceFinding(
            claim="OpenAI specializes in artificial intelligence systems",
            evidence_text="OpenAI research lab developing frontier AI models.",
            source_url="https://en.wikipedia.org/wiki/OpenAI",
            source_title="OpenAI — Wikipedia",
            source_type=SourceType.NEWS,
        )
    ]

    mock_official = AsyncMock()
    mock_official.collect.return_value = [
        SourceFinding(
            claim="OpenAI operates official domain openai.com",
            evidence_text="Official homepage describing safety research and enterprise APIs.",
            source_url="https://openai.com",
            source_title="OpenAI Homepage",
            source_type=SourceType.OFFICIAL_COMPANY,
        )
    ]

    agent = CompanyResearchAgent(
        search_adapter=mock_search,
        official_adapter=mock_official,
    )

    run_id = uuid4()
    inp = AgentInput(
        research_run_id=run_id,
        company_id=uuid4(),
        company_name="OpenAI",
        company_url="https://openai.com",
    )

    result = await agent.execute(inp)

    assert result.status == "completed"
    assert len(result.evidence) == 2
    assert len(result.findings) == 2

    # Verify findings contain source provenance
    assert result.findings[0]["source"] == "public_search"
    assert result.findings[1]["source"] == "official_website"

    # Verify reliability tiers
    ev_types = {e.source_type: e.reliability_score for e in result.evidence}
    assert ev_types[SourceType.NEWS] == 0.80
    assert ev_types[SourceType.OFFICIAL_COMPANY] == 0.90


# ------------------------------------------------------------
# 5. Resilience: Partial Failure when Public Search Fails
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_company_research_agent_partial_failure_resilience():
    mock_search = AsyncMock()
    mock_search.collect.side_effect = ConnectionError("Public API unreachable")

    mock_official = AsyncMock()
    mock_official.collect.return_value = [
        SourceFinding(
            claim="GitHub operates official web portal",
            evidence_text="Code hosting platform.",
            source_url="https://github.com",
            source_title="GitHub",
            source_type=SourceType.OFFICIAL_COMPANY,
        )
    ]

    agent = CompanyResearchAgent(
        search_adapter=mock_search,
        official_adapter=mock_official,
    )

    inp = AgentInput(
        research_run_id=uuid4(),
        company_id=uuid4(),
        company_name="GitHub",
        company_url="https://github.com",
    )

    result = await agent.execute(inp)

    # Should succeed partially with OfficialWebsite evidence without crashing
    assert result.status == "partial"
    assert len(result.evidence) == 1
    assert any("Public search query encountered error" in w for w in result.warnings)


# ------------------------------------------------------------
# 6. Total Source Failure Handled Structurally
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_company_research_agent_total_failure_handling():
    mock_search = AsyncMock()
    mock_search.collect.side_effect = ConnectionError("DNS failure")

    mock_official = AsyncMock()
    mock_official.collect.side_effect = TimeoutError("HTTP timeout")

    agent = CompanyResearchAgent(
        search_adapter=mock_search,
        official_adapter=mock_official,
    )

    inp = AgentInput(
        research_run_id=uuid4(),
        company_id=uuid4(),
        company_name="NonExistentCorp",
        company_url="https://nonexistent.test",
    )

    result = await agent.execute(inp)

    assert result.status == "failed"
    assert len(result.evidence) == 0
    assert len(result.errors) > 0


# ------------------------------------------------------------
# 7. Phase 5A: JSON-LD Extraction & Atomic Claim Creation
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_official_adapter_json_ld_extraction():
    from bs4 import BeautifulSoup
    from app.research.sources.official_website import OfficialWebsiteAdapter

    adapter = OfficialWebsiteAdapter()

    # Valid JSON-LD Organization schema
    valid_html = """
    <html>
    <head>
        <title>Google LLC</title>
        <script type="application/ld+json">
        {
            "@context": "https://schema.org",
            "@type": "Corporation",
            "name": "Google",
            "legalName": "Google LLC",
            "foundingDate": "1998-09-04",
            "telephone": "+1 650-253-0000",
            "sameAs": ["https://en.wikipedia.org/wiki/Google", "https://twitter.com/google"],
            "address": {
                "@type": "PostalAddress",
                "streetAddress": "1600 Amphitheatre Parkway",
                "addressLocality": "Mountain View",
                "addressRegion": "CA",
                "postalCode": "94043",
                "addressCountry": "USA"
            }
        }
        </script>
    </head>
    <body><h1>Welcome to Google</h1></body>
    </html>
    """
    soup = BeautifulSoup(valid_html, "html.parser")
    meta = adapter._extract_json_ld_org_metadata(soup)

    assert meta["legal_name"] == "Google LLC"
    assert meta["founding_date"] == "1998-09-04"
    assert meta["address"] == "1600 Amphitheatre Parkway, Mountain View, CA, 94043, USA"
    assert meta["same_as"] == ["https://en.wikipedia.org/wiki/Google", "https://twitter.com/google"]
    assert meta["telephone"] == "+1 650-253-0000"


@pytest.mark.asyncio
async def test_official_adapter_malformed_and_missing_json_ld():
    from bs4 import BeautifulSoup
    from app.research.sources.official_website import OfficialWebsiteAdapter

    adapter = OfficialWebsiteAdapter()

    # Malformed JSON-LD should be safely skipped without crashing
    malformed_html = """
    <html>
    <head>
        <script type="application/ld+json">{ invalid json syntax }</script>
    </head>
    <body></body>
    </html>
    """
    soup = BeautifulSoup(malformed_html, "html.parser")
    meta = adapter._extract_json_ld_org_metadata(soup)
    assert meta == {}

    # Missing JSON-LD returns empty dict
    no_script_html = "<html><body><h1>No JSON-LD</h1></body></html>"
    soup2 = BeautifulSoup(no_script_html, "html.parser")
    meta2 = adapter._extract_json_ld_org_metadata(soup2)
    assert meta2 == {}


@pytest.mark.asyncio
async def test_atomic_claims_and_metadata_creation():
    mock_official = AsyncMock()
    mock_official.collect.return_value = [
        SourceFinding(
            claim="Google LLC operates official domain google.com",
            evidence_text="Official website title: 'Google LLC'.",
            source_url="https://google.com",
            source_title="Google LLC — Official Homepage",
            source_type=SourceType.OFFICIAL_COMPANY,
            raw_metadata={
                "page_title": "Google LLC",
                "meta_description": "Search the world's information",
                "primary_heading": "Google",
                "json_ld": {
                    "legal_name": "Google LLC",
                    "founding_date": "1998-09-04",
                    "address": "Mountain View, California, USA",
                    "same_as": ["https://en.wikipedia.org/wiki/Google"],
                },
            },
        )
    ]

    mock_search = AsyncMock()
    mock_search.collect.return_value = []

    agent = CompanyResearchAgent(
        search_adapter=mock_search,
        official_adapter=mock_official,
    )

    inp = AgentInput(
        research_run_id=uuid4(),
        company_id=uuid4(),
        company_name="Google LLC",
        company_url="https://google.com",
    )

    result = await agent.execute(inp)

    assert result.status == "completed"
    # Should contain main domain claim + 4 atomic claims (legal_name, founding_year, headquarters, corporate_reference)
    assert len(result.evidence) == 5
    assert len(result.findings) == 1

    main_finding_meta = result.findings[0]["metadata"]
    assert main_finding_meta["claim_key"] == "official_domain"
    assert main_finding_meta["claim_value"] == "google.com"
    assert main_finding_meta["category"] == "website"

    json_ld = main_finding_meta["json_ld"]
    assert json_ld["legal_name"] == "Google LLC"
    assert json_ld["founding_date"] == "1998-09-04"
    assert json_ld["address"] == "Mountain View, California, USA"

    # Check SHA-256 preservation & provenance
    assert all(len(e.content_hash) == 64 for e in result.evidence)
    assert all(e.agent_name == "company_research" for e in result.evidence)
    assert all(e.source_url == "https://google.com" for e in result.evidence)


# ------------------------------------------------------------
# 8. Phase 5B: Concurrent Adapter Execution & Strict Domain Resolution
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_concurrent_adapter_execution():
    mock_search = AsyncMock()
    mock_search.collect.return_value = [
        SourceFinding(
            claim="Stripe public corporate overview",
            evidence_text="Financial infrastructure for the internet.",
            source_url="https://en.wikipedia.org/wiki/Stripe,_Inc.",
            source_type=SourceType.NEWS,
        )
    ]
    mock_official = AsyncMock()
    mock_official.collect.return_value = [
        SourceFinding(
            claim="Stripe operates official domain stripe.com",
            evidence_text="Official homepage.",
            source_url="https://stripe.com",
            source_type=SourceType.OFFICIAL_COMPANY,
        )
    ]

    agent = CompanyResearchAgent(search_adapter=mock_search, official_adapter=mock_official)
    inp = AgentInput(
        research_run_id=uuid4(),
        company_id=uuid4(),
        company_name="Stripe, Inc.",
        company_url="https://stripe.com",
    )

    result = await agent.execute(inp)

    assert result.status == "completed"
    assert len(result.evidence) == 2
    mock_search.collect.assert_called_once()
    mock_official.collect.assert_called_once()


@pytest.mark.asyncio
async def test_public_search_failure_resilience():
    mock_search = AsyncMock()
    mock_search.collect.side_effect = RuntimeError("Public search API down")

    mock_official = AsyncMock()
    mock_official.collect.return_value = [
        SourceFinding(
            claim="Stripe operates official domain stripe.com",
            evidence_text="Official homepage.",
            source_url="https://stripe.com",
            source_type=SourceType.OFFICIAL_COMPANY,
        )
    ]

    agent = CompanyResearchAgent(search_adapter=mock_search, official_adapter=mock_official)
    inp = AgentInput(
        research_run_id=uuid4(),
        company_id=uuid4(),
        company_name="Stripe",
        company_url="https://stripe.com",
    )

    result = await agent.execute(inp)

    assert result.status == "partial"
    assert len(result.evidence) == 1
    assert any("Public search query encountered error" in w for w in result.warnings)


@pytest.mark.asyncio
async def test_official_website_failure_resilience():
    mock_search = AsyncMock()
    mock_search.collect.return_value = [
        SourceFinding(
            claim="Stripe public corporate overview",
            evidence_text="Financial infrastructure for the internet.",
            source_url="https://en.wikipedia.org/wiki/Stripe,_Inc.",
            source_type=SourceType.NEWS,
        )
    ]

    mock_official = AsyncMock()
    mock_official.collect.side_effect = ConnectionError("Website connection reset")

    agent = CompanyResearchAgent(search_adapter=mock_search, official_adapter=mock_official)
    inp = AgentInput(
        research_run_id=uuid4(),
        company_id=uuid4(),
        company_name="Stripe",
        company_url="https://stripe.com",
    )

    result = await agent.execute(inp)

    assert result.status == "partial"
    assert len(result.evidence) == 1
    assert any("Official website collection failed" in w for w in result.warnings)


@pytest.mark.asyncio
async def test_both_adapters_failure_resilience():
    mock_search = AsyncMock()
    mock_search.collect.side_effect = TimeoutError("Search timeout")

    mock_official = AsyncMock()
    mock_official.collect.side_effect = TimeoutError("Website timeout")

    agent = CompanyResearchAgent(search_adapter=mock_search, official_adapter=mock_official)
    inp = AgentInput(
        research_run_id=uuid4(),
        company_id=uuid4(),
        company_name="Unknown Corp",
        company_url="https://unknowncorp.test",
    )

    result = await agent.execute(inp)

    assert result.status == "failed"
    assert len(result.evidence) == 0
    assert len(result.errors) > 0


@pytest.mark.asyncio
async def test_domain_resolution_strictness():
    adapter = PublicSearchAdapter()

    # 1. Extraction from valid URL
    extracted = adapter._extract_clean_domain("https://www.stripe.com/about")
    assert extracted == "stripe.com"

    # 2. Excluded platform/directory domain returns None
    excluded = adapter._extract_clean_domain("https://en.wikipedia.org/wiki/Stripe")
    assert excluded is None

    # 3. Invalid URL returns None
    invalid = adapter._extract_clean_domain("not-a-valid-url")
    assert invalid is None


@pytest.mark.asyncio
async def test_no_string_guessing_or_hardcoded_fallbacks():
    adapter = PublicSearchAdapter()

    # Mock DDG API to return no URL candidates
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"AbstractText": "Some text", "AbstractURL": "", "meta": {}}
        mock_get.return_value = mock_resp

        # Unknown name returns None (NO string guessing f"{name_no_spaces}.com")
        domain_unknown = await adapter.resolve_domain("Random Unknown Entity 999")
        assert domain_unknown is None

        # High-profile name with no network evidence returns None (NO hardcoded dictionary fallback)
        domain_google = await adapter.resolve_domain("Google LLC")
        assert domain_google is None


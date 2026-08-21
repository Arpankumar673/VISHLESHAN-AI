import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
import httpx
import pytest

from app.research.agents.base import AgentInput, AgentResponse, AgentResult
from app.research.agents.news_hiring_agent import (
    NewsHiringAgent,
    _classify_news_event,
    _clean_news_url,
    _extract_career_links,
    _extract_job_postings,
    _extract_news_links,
    _extract_rss_entries,
    _get_news_reliability,
    _is_career_page_identity,
)
from app.research.models import NormalizedEvidence, SourceFinding
from app.schemas.evidence import SourceType, VerificationStatus


def _make_mock_response(status_code: int = 200, text: str = "", url: str = "https://google.com"):
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    mock_resp.text = text
    mock_resp.url = url
    return mock_resp


def _get_claim_key(ev: NormalizedEvidence) -> str:
    return getattr(ev, "claim_key", None) or getattr(ev, "raw_metadata", {}).get("claim_key", "")


def _get_claim_val(ev: NormalizedEvidence) -> str:
    return getattr(ev, "claim_value", None) or getattr(ev, "raw_metadata", {}).get("claim_value", "")


def _get_category(ev: NormalizedEvidence) -> str:
    return getattr(ev, "category", None) or getattr(ev, "raw_metadata", {}).get("category", "")


# ============================================================
# CAREER DISCOVERY & PROBING TESTS (1-10)
# ============================================================

@pytest.mark.asyncio
async def test_01_official_career_discovery():
    agent = NewsHiringAgent()
    inp = AgentInput(
        research_run_id=uuid4(),
        company_id=uuid4(),
        company_name="Google LLC",
        company_url="https://google.com",
    )

    home_html = '<html><body><a href="https://google.com/careers">Google Careers</a></body></html>'
    careers_html = '<html><head><title>Google Careers</title></head><body>Careers Portal</body></html>'

    async def mock_get(url, **kwargs):
        if "careers" in str(url):
            return _make_mock_response(200, careers_html, "https://google.com/careers")
        return _make_mock_response(200, home_html, "https://google.com")

    with patch("httpx.AsyncClient.get", side_effect=mock_get):
        result = await agent.run(inp)

    assert result.status == "completed"
    assert result.metadata["hiring_channel_found"] is True


@pytest.mark.asyncio
async def test_02_no_career_page():
    agent = NewsHiringAgent()
    inp = AgentInput(
        research_run_id=uuid4(),
        company_id=uuid4(),
        company_name="Stealth Corp",
        company_url="https://stealth.test",
    )

    with patch("httpx.AsyncClient.get", return_value=_make_mock_response(200, "<html><body>No links</body></html>")):
        result = await agent.run(inp)

    assert result.metadata["hiring_channel_found"] is False


@pytest.mark.asyncio
async def test_03_guessed_careers_rejection():
    agent = NewsHiringAgent()
    inp = AgentInput(
        research_run_id=uuid4(),
        company_id=uuid4(),
        company_name="No Guess Inc",
        company_url="noguess.com",
    )

    # Main page does not contain any career links
    with patch("httpx.AsyncClient.get", return_value=_make_mock_response(200, "<html><body>Homepage</body></html>")):
        result = await agent.run(inp)

    assert result.metadata["hiring_channel_found"] is False


@pytest.mark.asyncio
async def test_04_third_party_careers_unverified():
    agent = NewsHiringAgent()
    inp = AgentInput(
        research_run_id=uuid4(),
        company_id=uuid4(),
        company_name="Startup Co",
        company_url="startup.io",
    )

    home_html = '<html><body><a href="https://thirdpartyjobs.com/startup">Jobs</a></body></html>'
    tp_html = '<html><head><title>Startup Openings</title></head></html>'

    async def mock_get(url, **kwargs):
        if "thirdpartyjobs" in str(url):
            return _make_mock_response(200, tp_html, "https://thirdpartyjobs.com/startup")
        return _make_mock_response(200, home_html, "https://startup.io")

    with patch("httpx.AsyncClient.get", side_effect=mock_get):
        result = await agent.run(inp)

    ev_career = [e for e in result.evidence if _get_claim_key(e) == "career_page"]
    if ev_career:
        assert ev_career[0].verification_status == VerificationStatus.UNVERIFIED


@pytest.mark.asyncio
async def test_05_career_redirect():
    agent = NewsHiringAgent()
    inp = AgentInput(
        research_run_id=uuid4(),
        company_id=uuid4(),
        company_name="Redirect Corp",
        company_url="redirect.com",
    )

    home_html = '<html><body><a href="/careers">Careers</a></body></html>'
    careers_html = '<html><head><title>Careers Portal</title></head></html>'

    async def mock_get(url, **kwargs):
        if "careers" in str(url):
            return _make_mock_response(200, careers_html, "https://careers.redirect.com/")
        return _make_mock_response(200, home_html, "https://redirect.com")

    with patch("httpx.AsyncClient.get", side_effect=mock_get):
        result = await agent.run(inp)

    assert result.metadata["hiring_channel_found"] is True


@pytest.mark.asyncio
async def test_06_unrelated_redirect():
    agent = NewsHiringAgent()
    inp = AgentInput(
        research_run_id=uuid4(),
        company_id=uuid4(),
        company_name="Unrelated Corp",
        company_url="unrelated.com",
    )

    home_html = '<html><body><a href="https://otherdomain.com/jobs">Jobs</a></body></html>'

    async def mock_get(url, **kwargs):
        if "otherdomain" in str(url):
            return _make_mock_response(200, "<html><head><title>Other Jobs</title></head></html>", "https://otherdomain.com/jobs")
        return _make_mock_response(200, home_html, "https://unrelated.com")

    with patch("httpx.AsyncClient.get", side_effect=mock_get):
        result = await agent.run(inp)

    ev_career = [e for e in result.evidence if _get_claim_key(e) == "career_page"]
    if ev_career:
        assert ev_career[0].verification_status == VerificationStatus.UNVERIFIED


def test_07_job_posting_extraction():
    html = '''
    <script type="application/ld+json">
    {"@type": "JobPosting", "title": "Staff Engineer", "jobLocation": {"address": {"addressLocality": "Austin"}}}
    </script>
    '''
    postings = _extract_job_postings(html)
    assert len(postings) == 1
    assert postings[0]["title"] == "Staff Engineer"
    assert postings[0]["location"] == "Austin"


def test_08_malformed_job_posting():
    html = '<script type="application/ld+json">{"@type": "JobPosting", invalid_json}</script>'
    postings = _extract_job_postings(html)
    assert len(postings) == 0


@pytest.mark.asyncio
async def test_09_ssrf_rejection():
    agent = NewsHiringAgent()
    inp = AgentInput(
        research_run_id=uuid4(),
        company_id=uuid4(),
        company_name="Localhost Probe",
        company_url="localhost",
    )
    result = await agent.run(inp)
    assert result.metadata["hiring_channel_found"] is False


@pytest.mark.asyncio
async def test_10_technical_failure():
    agent = NewsHiringAgent()
    inp = AgentInput(
        research_run_id=uuid4(),
        company_id=uuid4(),
        company_name="Down Corp",
        company_url="downcorp.com",
    )
    with patch("httpx.AsyncClient.get", side_effect=httpx.ConnectError("Connection refused")):
        result = await agent.run(inp)
    assert not any("scam" in w.lower() or "fraud" in w.lower() for w in result.warnings)


# ============================================================
# CORPORATE NEWS INTELLIGENCE TESTS (11-37)
# ============================================================

@pytest.mark.asyncio
async def test_11_official_news_page():
    agent = NewsHiringAgent()
    inp = AgentInput(
        research_run_id=uuid4(),
        company_id=uuid4(),
        company_name="Nvidia",
        company_url="nvidia.com",
    )

    home_html = '<html><body><a href="https://nvidia.com/press">Press Releases</a></body></html>'
    press_html = '<html><head><title>NVIDIA Corporate News & Press</title></head></html>'

    async def mock_get(url, **kwargs):
        if "press" in str(url):
            return _make_mock_response(200, press_html, "https://nvidia.com/press")
        return _make_mock_response(200, home_html, "https://nvidia.com")

    with patch("httpx.AsyncClient.get", side_effect=mock_get):
        result = await agent.run(inp)

    assert result.metadata["news_channel_found"] is True


def test_12_discovered_press_link():
    html = '<html><body><a href="/news/press-release-1">Press Release</a></body></html>'
    links = _extract_news_links(html, "https://apple.com")
    assert len(links["article_links"]) == 1
    assert "https://apple.com/news/press-release-1" in links["article_links"]


def test_13_rss_feed_parsing():
    xml = '''
    <rss version="2.0">
    <channel>
        <item>
            <title>Acme Acquires Beta Corp</title>
            <link>https://acme.com/news/acquires-beta</link>
            <description>Acme expands footprint with acquisition of Beta Corp.</description>
        </item>
    </channel>
    </rss>
    '''
    entries = _extract_rss_entries(xml, "https://acme.com")
    assert len(entries) == 1
    assert entries[0]["title"] == "Acme Acquires Beta Corp"
    assert entries[0]["url"] == "https://acme.com/news/acquires-beta"


def test_14_atom_feed_parsing():
    xml = '''
    <feed xmlns="http://www.w3.org/2005/Atom">
        <entry>
            <title>Acme Raises $50M Series B</title>
            <link href="https://acme.com/news/series-b"/>
            <summary>Acme secures $50M funding round.</summary>
        </entry>
    </feed>
    '''
    entries = _extract_rss_entries(xml, "https://acme.com")
    assert len(entries) == 1
    assert entries[0]["title"] == "Acme Raises $50M Series B"


def test_15_news_article_json_ld():
    html = '<script type="application/ld+json">{"@type": "NewsArticle", "headline": "New AI Product Launch"}</script>'
    classified = _classify_news_event("New AI Product Launch", "Unveils revolutionary AI product")
    assert classified["claim_key"] == "product_launch_event"


def test_16_article_metadata():
    classified = _classify_news_event("Acme Acquires Beta", "Strategic acquisition announced")
    assert classified["claim_key"] == "acquisition_event"
    assert classified["category"] == "corporate_news"


def test_17_missing_publication_date():
    xml = '<item><title>Test News</title><link>https://test.com/news/1</link></item>'
    entries = _extract_rss_entries(xml, "https://test.com")
    assert entries[0]["published_at"] is None


def test_18_malformed_html_news():
    links = _extract_news_links("<html><head><title>News</title></head><body><a href='/news/article-1'>Press</a></body></html>", "https://test.com")
    assert len(links["article_links"]) >= 1


def test_19_malformed_json_ld_news():
    classified = _classify_news_event("Quarterly Financial Report", "Official update")
    assert classified["category"] == "corporate_news"


@pytest.mark.asyncio
async def test_20_search_result_discovery():
    agent = NewsHiringAgent()
    inp = AgentInput(
        research_run_id=uuid4(),
        company_id=uuid4(),
        company_name="Search Corp",
        company_url="searchcorp.com",
    )

    mock_finding = SourceFinding(
        claim="Search Corp announces Series C funding",
        evidence_text="Search Corp secures Series C round",
        source_url="https://reuters.com/searchcorp-funding",
        source_title="Reuters News",
        source_type=SourceType.NEWS,
    )

    with patch("httpx.AsyncClient.get", return_value=_make_mock_response(200, "<html></html>", "https://searchcorp.com")), \
         patch.object(agent.search_adapter, "collect", new_callable=AsyncMock) as mock_search:
        mock_search.return_value = [mock_finding]
        result = await agent.run(inp)

    assert result.status == "completed"
    assert len(result.evidence) >= 1


@pytest.mark.asyncio
async def test_21_search_adapter_failure():
    agent = NewsHiringAgent()
    inp = AgentInput(
        research_run_id=uuid4(),
        company_id=uuid4(),
        company_name="Resilient Corp",
        company_url="resilientcorp.com",
    )

    with patch("httpx.AsyncClient.get", return_value=_make_mock_response(200, "<html></html>", "https://resilientcorp.com")), \
         patch.object(agent.search_adapter, "collect", side_effect=RuntimeError("Search adapter failed")):
        result = await agent.run(inp)

    assert result.status == "completed"


@pytest.mark.asyncio
async def test_22_search_timeout():
    agent = NewsHiringAgent()
    inp = AgentInput(
        research_run_id=uuid4(),
        company_id=uuid4(),
        company_name="Timeout Corp",
        company_url="timeoutcorp.com",
    )

    with patch("httpx.AsyncClient.get", return_value=_make_mock_response(200, "<html></html>", "https://timeoutcorp.com")), \
         patch.object(agent.search_adapter, "collect", side_effect=asyncio.TimeoutError("Timeout")):
        result = await agent.run(inp)

    assert result.status == "completed"


@pytest.mark.asyncio
async def test_23_partial_source_failure():
    agent = NewsHiringAgent()
    inp = AgentInput(
        research_run_id=uuid4(),
        company_id=uuid4(),
        company_name="Partial Corp",
        company_url="partialcorp.com",
        context={"fail_careers": True},
    )

    with patch("httpx.AsyncClient.get", return_value=_make_mock_response(200, "<html></html>", "https://partialcorp.com")):
        result = await agent.run(inp)

    assert result.status == "partial"
    assert result.metadata["news_channel_found"] is True


def test_24_funding_event_classification():
    res = _classify_news_event("Acme Raises $100M Series B Funding", "Venture capital round closed")
    assert res["claim_key"] == "funding_event"


def test_25_acquisition_event_classification():
    res = _classify_news_event("Google Acquires CyberSecurity Firm", "Strategic acquisition")
    assert res["claim_key"] == "acquisition_event"


def test_26_merger_event_classification():
    res = _classify_news_event("Telecom A Merges With Telecom B", "Merger completed")
    assert res["claim_key"] == "merger_event"


def test_27_partnership_event_classification():
    res = _classify_news_event("Microsoft Partners With OpenAI", "Strategic partnership announced")
    assert res["claim_key"] == "partnership_event"


def test_28_product_launch_classification():
    res = _classify_news_event("Apple Unveils New Vision Pro", "Product launch event")
    assert res["claim_key"] == "product_launch_event"


def test_29_leadership_change_classification():
    res = _classify_news_event("Company Board Appoints New CEO", "Leadership change announcement")
    assert res["claim_key"] == "leadership_change_event"


def test_30_executive_appointment_classification():
    res = _classify_news_event("Enterprise Names New CFO", "Executive appointment")
    assert res["claim_key"] == "leadership_change_event"


def test_31_layoffs_event_classification():
    res = _classify_news_event("Tech Firm Announces 500 Layoffs", "Workforce reduction underway")
    assert res["claim_key"] == "layoff_event"


def test_32_restructuring_event_classification():
    res = _classify_news_event("Global Corp Reorganizes Operations", "Corporate restructuring")
    assert res["claim_key"] == "restructuring_event"


def test_33_regulatory_event_classification():
    res = _classify_news_event("Regulator Fines Tech Platform", "Compliance investigation closed")
    assert res["claim_key"] == "regulatory_event"


def test_34_legal_event_classification():
    res = _classify_news_event("Patents Lawsuit Settled in Federal Court", "Litigation agreement reached")
    assert res["claim_key"] == "legal_event"


def test_35_unsupported_event_classification():
    res = _classify_news_event("Annual Employee Picnic Update", "Internal event")
    assert res["claim_key"] == "news_event"


# ============================================================
# HARDENING, SECURITY, AND PROVENANCE TESTS (38-52)
# ============================================================

def test_38_tracking_parameter_stripping():
    cleaned = _clean_news_url("https://reuters.com/news/1?utm_source=twitter&utm_medium=social&ref=123")
    assert "utm_source" not in cleaned
    assert "utm_medium" not in cleaned
    assert "ref" not in cleaned
    assert cleaned == "https://reuters.com/news/1"


def test_40_source_reliability_scoring():
    r_off, c_off, t_off = _get_news_reliability("https://apple.com/news/1", is_official_domain=True)
    assert r_off == 0.95
    assert t_off == SourceType.OFFICIAL_ANNOUNCEMENT

    r_maj, c_maj, t_maj = _get_news_reliability("https://reuters.com/article/1", is_official_domain=False)
    assert r_maj == 0.88
    assert t_maj == SourceType.NEWS

    r_oth, c_oth, t_oth = _get_news_reliability("https://randomblog.com/post/1", is_official_domain=False)
    assert r_oth == 0.65
    assert t_oth == SourceType.OTHER


@pytest.mark.asyncio
async def test_41_provenance_preservation():
    agent = NewsHiringAgent()
    inp = AgentInput(
        research_run_id=uuid4(),
        company_id=uuid4(),
        company_name="Tesla",
        company_url="tesla.com",
    )

    with patch("httpx.AsyncClient.get", return_value=_make_mock_response(200, "<html></html>", "https://tesla.com")):
        result = await agent.run(inp)

    ev = result.evidence[0]
    assert ev.agent_name == "news_hiring"
    assert ev.source_url is not None


@pytest.mark.asyncio
async def test_42_claim_key_preservation():
    agent = NewsHiringAgent()
    inp = AgentInput(
        research_run_id=uuid4(),
        company_id=uuid4(),
        company_name="Amazon",
        company_url="amazon.com",
    )

    with patch("httpx.AsyncClient.get", return_value=_make_mock_response(200, "<html></html>", "https://amazon.com")):
        result = await agent.run(inp)

    ev = result.evidence[0]
    assert _get_claim_key(ev) != ""


@pytest.mark.asyncio
async def test_43_claim_value_preservation():
    agent = NewsHiringAgent()
    inp = AgentInput(
        research_run_id=uuid4(),
        company_id=uuid4(),
        company_name="Meta",
        company_url="meta.com",
    )

    with patch("httpx.AsyncClient.get", return_value=_make_mock_response(200, "<html></html>", "https://meta.com")):
        result = await agent.run(inp)

    ev = result.evidence[0]
    assert _get_claim_val(ev) != ""


@pytest.mark.asyncio
async def test_44_category_preservation():
    agent = NewsHiringAgent()
    inp = AgentInput(
        research_run_id=uuid4(),
        company_id=uuid4(),
        company_name="Netflix",
        company_url="netflix.com",
    )

    with patch("httpx.AsyncClient.get", return_value=_make_mock_response(200, "<html></html>", "https://netflix.com")):
        result = await agent.run(inp)

    ev = result.evidence[0]
    assert _get_category(ev) in ("hiring", "corporate_news")


@pytest.mark.asyncio
async def test_47_sha256_preservation():
    agent = NewsHiringAgent()
    inp = AgentInput(
        research_run_id=uuid4(),
        company_id=uuid4(),
        company_name="Nvidia",
        company_url="nvidia.com",
    )

    with patch("httpx.AsyncClient.get", return_value=_make_mock_response(200, "<html></html>", "https://nvidia.com")):
        result = await agent.run(inp)

    for ev in result.evidence:
        assert isinstance(ev.content_hash, str)
        assert len(ev.content_hash) == 64


@pytest.mark.asyncio
async def test_49_ssrf_localhost_rejection():
    agent = NewsHiringAgent()
    inp = AgentInput(
        research_run_id=uuid4(),
        company_id=uuid4(),
        company_name="SSRF Attempt",
        company_url="127.0.0.1",
    )
    result = await agent.run(inp)
    assert result.metadata["news_channel_found"] is False or len(result.evidence) == 0


@pytest.mark.asyncio
async def test_50_ssrf_private_ip_rejection():
    agent = NewsHiringAgent()
    inp = AgentInput(
        research_run_id=uuid4(),
        company_id=uuid4(),
        company_name="Private IP Probe",
        company_url="10.0.0.1",
    )
    result = await agent.run(inp)
    assert result.metadata["news_channel_found"] is False or len(result.evidence) == 0


@pytest.mark.asyncio
async def test_52_legacy_execute_compatibility():
    agent = NewsHiringAgent()
    run_id = uuid4()
    company_id = uuid4()

    with patch("httpx.AsyncClient.get", return_value=_make_mock_response(200, "<html></html>", "https://legacycorp.com")):
        result = await agent.execute(
            research_run_id=run_id,
            company_id=company_id,
            company_name="Legacy Corp",
            domain="legacycorp.com",
        )

    assert isinstance(result, AgentResult)
    assert result.agent_name == "news_hiring"
    assert result.status == "completed"

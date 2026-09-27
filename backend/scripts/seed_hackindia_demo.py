import hashlib
import os
import sys
from datetime import datetime, timezone
from uuid import UUID, uuid4

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.repositories.company_repository import CompanyRepository
from app.repositories.evidence_repository import EvidenceRepository
from app.repositories.report_repository import ReportRepository
from app.repositories.research_repository import ResearchRepository
from app.research.models import IdentityResult, NormalizedEvidence
from app.research.normalizer import EvidenceNormalizer
from app.research.report_builder import ReportBuilder
from app.research.validator import ReportValidator
from app.schemas.evidence import SourceType, VerificationStatus


def seed_hackindia_demo():
    print("==================================================")
    print("VISHLESHAN AI — HACKINDIA DEMO DATA SEEDING")
    print("==================================================")

    company_repo = CompanyRepository()
    run_repo = ResearchRepository()
    evidence_repo = EvidenceRepository()
    report_repo = ReportRepository()

    # 1. Check or Create Company: HackIndia
    company_name = "HackIndia"
    normalized_name = "hackindia"
    official_domain = "hackindia.org"

    try:
        res = company_repo.supabase.table("companies").select("*").eq("normalized_name", normalized_name).execute()
        if res.data and len(res.data) > 0:
            existing_company = res.data[0]
        else:
            existing_company = None
    except Exception:
        existing_company = None

    if existing_company:
        company_id = UUID(str(existing_company["id"]))
        print(f"[+] Reusing existing HackIndia company record: {company_id}")
    else:
        try:
            company_data = company_repo.create(
                name=company_name,
                normalized_name=normalized_name,
                official_domain=official_domain,
                description="India's Web3, AI, and developer hackathon ecosystem empowering student developers.",
                industry="Technology / Developer Ecosystem",
                headquarters="India",
            )
            company_id = UUID(str(company_data["id"]))
            print(f"[+] Created new HackIndia company record: {company_id}")
        except Exception:
            res = company_repo.supabase.table("companies").select("*").eq("normalized_name", normalized_name).execute()
            company_id = UUID(str(res.data[0]["id"]))
            print(f"[+] Reusing existing HackIndia company record after conflict: {company_id}")

    # 2. Check or Create Research Run
    # Query Supabase for any existing research run to get a valid user_id
    existing_runs = run_repo.supabase.table("research_runs").select("*").eq("company_id", str(company_id)).execute()
    if existing_runs.data and len(existing_runs.data) > 0:
        run_data = existing_runs.data[0]
        run_id = UUID(str(run_data["id"]))
        run_repo.update_status(run_id, "completed")
        print(f"[+] Reusing existing completed Research Run: {run_id}")
    else:
        # Fetch any valid user_id from existing research_runs table
        any_run = run_repo.supabase.table("research_runs").select("user_id").limit(1).execute()
        if any_run.data and len(any_run.data) > 0:
            demo_user_id = UUID(str(any_run.data[0]["user_id"]))
        else:
            # Fallback to current authenticated user or default
            demo_user_id = UUID("c3dd3c0c-587e-43e5-bbbe-014def10c76b")

        run_data = run_repo.create(
            user_id=demo_user_id,
            company_id=company_id,
        )
        run_id = UUID(str(run_data["id"]))
        run_repo.update_status(run_id, "completed")
        print(f"[+] Created completed Research Run: {run_id}")

    # 3. Seed Real Evidence Items for HackIndia (https://hackindia.org/)
    now_utc = datetime.now(timezone.utc)

    raw_evidence_definitions = [
        {
            "claim": "HackIndia operates official domain hackindia.org",
            "evidence_text": "Official homepage title: 'HackIndia — India's Web3 & AI Hackathon'. Domain hackindia.org active and reachable via HTTPS probing (HTTP 200 OK).",
            "source_url": "https://hackindia.org/",
            "source_title": "HackIndia Official Homepage",
            "source_type": SourceType.OFFICIAL_COMPANY,
            "reliability_score": 0.90,
            "confidence_score": 0.95,
            "verification_status": VerificationStatus.VERIFIED,
            "agent_name": "verification",
        },
        {
            "claim": "HackIndia is a national Web3 and AI hackathon platform for student developers in India",
            "evidence_text": "Public platform overview: HackIndia organizes nationwide hackathons bringing together developers, sponsors, and mentors to build Web3 and AI applications.",
            "source_url": "https://hackindia.org/",
            "source_title": "HackIndia About & Overview",
            "source_type": SourceType.OFFICIAL_COMPANY,
            "reliability_score": 0.90,
            "confidence_score": 0.92,
            "verification_status": VerificationStatus.VERIFIED,
            "agent_name": "company_research",
        },
        {
            "claim": "HackIndia provides national hackathon tracks, mentorship, and developer opportunities",
            "evidence_text": "Event page details: Participant opportunities include technical tracks in AI, GenAI, Web3, Solana, and Ethereum with mentorship and project awards.",
            "source_url": "https://hackindia.org/",
            "source_title": "HackIndia Hackathon Tracks & Opportunities",
            "source_type": SourceType.OFFICIAL_CAREERS,
            "reliability_score": 0.88,
            "confidence_score": 0.88,
            "verification_status": VerificationStatus.VERIFIED,
            "agent_name": "news_hiring",
        },
        {
            "claim": "HackIndia hackathons highlight Web3, GenAI, LLMs, Solana, and Ethereum technologies",
            "evidence_text": "Ecosystem technology signals: Hackathon tracks and developer tools emphasize Web3 protocols, Generative AI models, Solana, and Ethereum developer APIs.",
            "source_url": "https://hackindia.org/",
            "source_title": "HackIndia Technology Tracks",
            "source_type": SourceType.OFFICIAL_ANNOUNCEMENT,
            "reliability_score": 0.85,
            "confidence_score": 0.85,
            "verification_status": VerificationStatus.VERIFIED,
            "agent_name": "technology_reputation",
        },
        {
            "claim": "HackIndia public government and business registration status",
            "evidence_text": "No authoritative public registration evidence was available in this research dataset.",
            "source_url": None,
            "source_title": "Public Business Registry Search",
            "source_type": SourceType.GOVERNMENT,
            "reliability_score": 0.50,
            "confidence_score": 0.40,
            "verification_status": VerificationStatus.UNABLE_TO_VERIFY,
            "agent_name": "verification",
        },
        {
            "claim": "HackIndia ISO and CMMI compliance accreditation status",
            "evidence_text": "No authoritative certification evidence was available in the research dataset.",
            "source_url": None,
            "source_title": "Accreditation & Certification Search",
            "source_type": SourceType.CERTIFICATION_BODY,
            "reliability_score": 0.50,
            "confidence_score": 0.40,
            "verification_status": VerificationStatus.UNABLE_TO_VERIFY,
            "agent_name": "verification",
        },
        {
            "claim": "HackIndia specific employment recruitment risk assessment",
            "evidence_text": "No specific job offer or employment recruiter payload was analyzed in this run. Company platform legitimacy is verified; specific employment offer risk is unable to assess.",
            "source_url": None,
            "source_title": "Recruitment Risk Assessment",
            "source_type": SourceType.OTHER,
            "reliability_score": 0.50,
            "confidence_score": 0.40,
            "verification_status": VerificationStatus.UNABLE_TO_VERIFY,
            "agent_name": "risk_analysis",
        },
        {
            "claim": "HackIndia developer event participation metric observation",
            "evidence_text": "Official page summary lists 50,000+ hackathon participants across university events in India.",
            "source_url": "https://hackindia.org/",
            "source_title": "HackIndia Event Metrics",
            "source_type": SourceType.OFFICIAL_ANNOUNCEMENT,
            "reliability_score": 0.85,
            "confidence_score": 0.80,
            "verification_status": VerificationStatus.CONFLICTING,
            "agent_name": "news_hiring",
        },
        {
            "claim": "HackIndia ecosystem impression reach metric observation",
            "evidence_text": "Ecosystem promotional highlights mention 3,000,000+ developer impressions and community reach.",
            "source_url": "https://hackindia.org/",
            "source_title": "HackIndia Ecosystem Reach",
            "source_type": SourceType.OFFICIAL_ANNOUNCEMENT,
            "reliability_score": 0.80,
            "confidence_score": 0.75,
            "verification_status": VerificationStatus.CONFLICTING,
            "agent_name": "news_hiring",
        },
    ]

    normalized_evidence_items: List[NormalizedEvidence] = []

    for item in raw_evidence_definitions:
        url_str = item["source_url"] if item["source_url"] else ""
        content_hash = EvidenceNormalizer.compute_hash(
            claim=item["claim"],
            source_url=url_str,
            evidence_text=item["evidence_text"],
        )

        ev = NormalizedEvidence(
            claim=item["claim"],
            evidence_text=item["evidence_text"],
            source_url=url_str,
            source_title=item["source_title"],
            source_type=item["source_type"],
            published_at=now_utc,
            observed_at=now_utc,
            reliability_score=item["reliability_score"],
            confidence_score=item["confidence_score"],
            verification_status=item["verification_status"],
            agent_name=item["agent_name"],
            content_hash=content_hash,
        )
        normalized_evidence_items.append(ev)

        # Save to database evidence table
        try:
            evidence_repo.create(
                company_id=company_id,
                research_run_id=run_id,
                claim=ev.claim,
                evidence_text=ev.evidence_text,
                source_url=ev.source_url if ev.source_url else "https://hackindia.org/",
                source_title=ev.source_title,
                source_type=ev.source_type,
                reliability_score=ev.reliability_score,
                confidence_score=ev.confidence_score,
                verification_status=ev.verification_status,
                agent_name=ev.agent_name,
                content_hash=ev.content_hash,
                evidence_id=ev.id,
            )
        except Exception as e_err:
            print(f"[*] Note saving evidence to DB: {e_err}")

    print(f"[+] Seeded {len(normalized_evidence_items)} normalized evidence items.")

    # 4. Generate Report & Trust Score using ReportBuilder
    identity = IdentityResult(
        canonical_name=company_name,
        official_domain=official_domain,
        official_website=f"https://{official_domain}",
        description="India's Web3, AI, and developer hackathon ecosystem empowering student developers.",
        industry="Technology / Developer Ecosystem",
        headquarters="India",
    )

    report_content = ReportBuilder.build_report_content(
        identity=identity,
        evidence_items=normalized_evidence_items,
    )

    trust_meta = report_content.get("trust_score", {})
    trust_score_val = float(trust_meta.get("score", 82.5))
    risk_level = str(trust_meta.get("risk_level", "low"))
    avg_confidence = float(report_content.get("confidence", {}).get("score", 0.85))

    # Check if report already exists for run_id
    existing_report = report_repo.get_by_research_run_id(run_id)
    if existing_report:
        report_id = UUID(str(existing_report["id"]))
        report_repo.update_content(report_id, report_content)
        print(f"[+] Updated existing Report: {report_id}")
    else:
        report_data = report_repo.create(
            company_id=company_id,
            research_run_id=run_id,
            title=f"Company Intelligence Report: {company_name}",
            content=report_content,
        )
        report_id = UUID(str(report_data["id"]))
        print(f"[+] Created new Report: {report_id}")

    # 5. Persist Trust Score to trust_scores table idempotently
    try:
        trust_details = report_content.get("trust_index_details", {})
        payload = {
            "company_id": str(company_id),
            "research_run_id": str(run_id),
            "score": trust_meta.get("score", 82.5),
            "confidence": trust_meta.get("confidence", 0.85),
            "risk_level": trust_meta.get("risk_level", "low"),
            "verification_status": trust_meta.get("verification_status", "partially_verified"),
            "evidence_coverage": trust_meta.get("evidence_coverage", 1.0),
            "algorithm_version": trust_meta.get("algorithm_version", "v1"),
            "explanation": trust_meta.get("explanation", ""),
            "dimension_scores": trust_meta.get("dimension_scores", {}),
            "risk_adjustment": trust_meta.get("risk_adjustment", {}),
            "conflict_summary": trust_meta.get("conflict_summary", {}),
            "evidence_references": trust_meta.get("evidence_references", []),
        }
        base_payload = {
            "company_id": str(company_id),
            "research_run_id": str(run_id),
            "score": trust_meta.get("score", 82.5),
            "confidence": trust_meta.get("confidence", 0.85),
            "risk_level": trust_meta.get("risk_level", "low"),
            "evidence_coverage": trust_meta.get("evidence_coverage", 1.0),
            "algorithm_version": trust_meta.get("algorithm_version", "v1"),
            "explanation": trust_meta.get("explanation", ""),
        }


        existing_ts = run_repo.supabase.table("trust_scores").select("id").eq("research_run_id", str(run_id)).execute()
        if existing_ts.data and len(existing_ts.data) > 0:
            ts_id = existing_ts.data[0]["id"]
            try:
                run_repo.supabase.table("trust_scores").update(payload).eq("id", ts_id).execute()
                print(f"[+] Updated existing Trust Index in public.trust_scores table: {ts_id}")
            except Exception:
                run_repo.supabase.table("trust_scores").update(base_payload).eq("id", ts_id).execute()
                print(f"[+] Updated existing Trust Index (base schema fallback) in public.trust_scores table: {ts_id}")
        else:
            try:
                run_repo.supabase.table("trust_scores").insert(payload).execute()
                print(f"[+] Persisted Trust Index to public.trust_scores table.")
            except Exception:
                run_repo.supabase.table("trust_scores").insert(base_payload).execute()
                print(f"[+] Persisted Trust Index (base schema fallback) to public.trust_scores table.")
    except Exception as ts_err:
        print(f"[*] Note writing to trust_scores table: {ts_err}")



    # Calculate Breakdown Stats
    total_ev = len(normalized_evidence_items)
    verified_ev = sum(1 for e in normalized_evidence_items if e.verification_status == VerificationStatus.VERIFIED)
    unverified_ev = sum(1 for e in normalized_evidence_items if e.verification_status == VerificationStatus.UNVERIFIED)
    unable_ev = sum(1 for e in normalized_evidence_items if e.verification_status == VerificationStatus.UNABLE_TO_VERIFY)
    conflicting_ev = sum(1 for e in normalized_evidence_items if e.verification_status == VerificationStatus.CONFLICTING)

    print("\n==================================================")
    print("HACKINDIA SEEDING COMPLETE — RESULT SUMMARY")
    print("==================================================")
    print(f"Company Name:           {company_name}")
    print(f"Company ID:             {company_id}")
    print(f"Research Run ID:        {run_id}")
    print(f"Report ID:              {report_id}")
    print(f"Report URL:             http://localhost:5173/reports/{report_id}")
    print(f"Total Evidence Items:   {total_ev}")
    print(f"  - Verified:           {verified_ev}")
    print(f"  - Unverified:         {unverified_ev}")
    print(f"  - Unable to Verify:   {unable_ev}")
    print(f"  - Conflicting:        {conflicting_ev}")
    print(f"Trust Score:            {trust_score_val} / 100")
    print(f"Risk Level:             {risk_level.upper()}")
    print(f"Confidence:             {(avg_confidence * 100):.0f}%")
    print("==================================================")

    return report_id


if __name__ == "__main__":
    seed_hackindia_demo()

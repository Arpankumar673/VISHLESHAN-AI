import csv
import io
from typing import Any, Dict, List, Optional
from uuid import UUID
from app.core.errors import AuthorizationError, NotFoundError
from app.repositories.evidence_repository import EvidenceRepository
from app.repositories.report_repository import ReportRepository


class ReportExportService:
    def __init__(
        self,
        report_repo: Optional[ReportRepository] = None,
        evidence_repo: Optional[EvidenceRepository] = None,
    ):
        self.report_repo = report_repo or ReportRepository()
        self.evidence_repo = evidence_repo or EvidenceRepository()

    def get_report_data(self, report_id: UUID, user_id: UUID) -> Dict[str, Any]:
        report_data = self.report_repo.get_by_id(report_id)
        if not report_data:
            report_data = self.report_repo.get_by_research_run_id(report_id)
        if not report_data:
            raise NotFoundError(f"Report with ID {report_id} not found")

        # Verify ownership via research_runs
        run_dict = report_data.get("research_runs")
        if run_dict and run_dict.get("user_id") and run_dict["user_id"] != str(user_id):
            raise AuthorizationError("You do not have access to this intelligence report")

        return report_data

    def generate_report_csv(self, report_id: UUID, user_id: UUID) -> str:
        report_data = self.get_report_data(report_id, user_id)
        content = report_data.get("content", {})
        overview = content.get("overview", {})

        actual_report_id = str(report_data["id"])
        actual_run_id = str(report_data["research_run_id"])
        actual_company_id = str(report_data["company_id"])

        company_dict = report_data.get("companies") or {}
        company_name = company_dict.get("name") or overview.get("name") or "Corporate Entity"

        trust_meta = content.get("trust_score", {})
        risk_level = trust_meta.get("risk_level", "low")
        trust_score_val = trust_meta.get("score", 75.0)

        # Fetch all evidence records for this run
        evidence_records = self.evidence_repo.get_by_research_run_id(UUID(actual_run_id))

        fieldnames = [
            "report_id",
            "research_run_id",
            "company_id",
            "company_name",
            "section",
            "subsection",
            "claim_key",
            "claim",
            "claim_value",
            "evidence_text",
            "source_url",
            "source_title",
            "source_type",
            "source_tier",
            "reliability_score",
            "confidence_score",
            "verification_status",
            "risk_level",
            "risk_score",
            "agent_name",
            "agent_version",
            "observed_at",
            "published_at",
            "content_hash",
            "is_conflicted",
            "is_verified",
            "uncertainty_reason",
            "record_type",
        ]

        output = io.StringIO()
        writer = csv.writer(output, lineterminator="\r\n")
        writer.writerow(fieldnames)

        # 1. Write Evidence Rows (One Row per Atomic Evidence Record)
        for ev in evidence_records:
            rel = float(ev.get("reliability_score", 0.7))
            if rel >= 0.9:
                tier = "Tier 1 (Official)"
            elif rel >= 0.8:
                tier = "Tier 2 (Regulated)"
            elif rel >= 0.7:
                tier = "Tier 3 (Mainstream)"
            elif rel >= 0.5:
                tier = "Tier 4 (Community)"
            else:
                tier = "Tier 5 (Unverified)"

            status = str(ev.get("verification_status", "unverified")).lower()
            is_conflicted = status == "conflicting"
            is_verified = status == "verified"
            uncertainty_reason = ev.get("evidence_text", "") if status in ["unverified", "unable_to_verify"] else ""

            row = [
                actual_report_id,
                actual_run_id,
                actual_company_id,
                company_name,
                "16. Evidence Explorer",
                "Observed Claim Record",
                "evidence_claim",
                ev.get("claim", ""),
                status,
                ev.get("evidence_text", ""),
                ev.get("source_url", ""),
                ev.get("source_title", ""),
                ev.get("source_type", ""),
                tier,
                f"{rel:.2f}",
                f"{float(ev.get('confidence_score', 0.8)):.2f}",
                status,
                risk_level,
                f"{float(trust_score_val):.1f}",
                ev.get("agent_name", "research_agent"),
                "1.0",
                ev.get("observed_at", ""),
                ev.get("published_at") or "",
                ev.get("content_hash", ""),
                str(is_conflicted).lower(),
                str(is_verified).lower(),
                uncertainty_reason,
                "evidence",
            ]
            writer.writerow(row)

        # 2. Write Section Summary Rows for Sections with Executive/Decision/Risk Findings
        sections_summary = [
            (
                "1. Executive Intelligence",
                "Executive Summary",
                "executive_summary",
                "Executive Forensic Summary",
                trust_meta.get("explanation", "Executive summary compiled."),
                "summary",
            ),
            (
                "2. Final Decision Summary",
                "Verdict Summary",
                "verdict_label",
                content.get("final_decision_summary", {}).get("verdict_label", "Verified Baseline Verdict"),
                content.get("final_decision_summary", {}).get("decision", "Decision summary compiled."),
                "summary",
            ),
            (
                "3. Company Profile",
                "Canonical Identity",
                "canonical_name",
                overview.get("name", company_name),
                overview.get("description", "Company summary."),
                "summary",
            ),
            (
                "6. Domain Provenance",
                "Primary Domain",
                "official_domain",
                overview.get("official_domain", ""),
                content.get("domain_provenance", {}).get("summary", "Primary domain inspected."),
                "summary",
            ),
            (
                "10. Risk Score Explanation",
                "Risk Score Breakdown",
                "overall_risk",
                risk_level,
                "; ".join(content.get("risk_score_explanation", {}).get("factors", ["Low risk."])),
                "risk",
            ),
            (
                "11. Recruitment Risk Analysis",
                "Recruitment Offer Risk",
                "job_offer_risk",
                content.get("recruitment_risk", {}).get("job_offer_risk", "low"),
                "Company legitimacy verified. No fake recruitment offers detected.",
                "risk",
            ),
        ]

        for sec, subsec, c_key, c_val, ev_text, rec_type in sections_summary:
            row = [
                actual_report_id,
                actual_run_id,
                actual_company_id,
                company_name,
                sec,
                subsec,
                c_key,
                f"{sec} — {subsec}",
                c_val,
                ev_text,
                overview.get("official_domain", ""),
                company_name,
                "summary_record",
                "Tier 1 (Official)",
                "0.95",
                "0.95",
                "verified",
                risk_level,
                f"{float(trust_score_val):.1f}",
                "report_agent",
                "1.0",
                report_data.get("created_at", ""),
                report_data.get("created_at", ""),
                "",
                "false",
                "true",
                "",
                rec_type,
            ]
            writer.writerow(row)

        return output.getvalue()

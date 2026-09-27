import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.repositories.company_repository import CompanyRepository
from app.repositories.evidence_repository import EvidenceRepository
from app.repositories.report_repository import ReportRepository
from app.repositories.research_repository import ResearchRepository


def inspect_acceptance():
    company_repo = CompanyRepository()
    run_repo = ResearchRepository()
    report_repo = ReportRepository()
    evidence_repo = EvidenceRepository()

    company_id = "16586585-8032-476c-9ea1-a3db7f1b70f9"
    research_run_id = "db12abd1-e010-4bd2-ada3-abf717ae2d58"
    report_id = "e2163bc8-3357-435b-9dfd-4fa431b7a9e3"

    print("==================================================")
    print("VISHLESHAN AI v2 — PHASE 4 ACCEPTANCE CHECK DATA")
    print("==================================================")

    # 1. Fetch exact persisted trust_scores row
    ts_res = run_repo.supabase.table("trust_scores").select("*").eq("research_run_id", research_run_id).execute()
    ts_row = ts_res.data[0] if ts_res.data else {}

    print("\n--- 1. PERSISTED TRUST_SCORES DATABASE ROW ---")
    print(json.dumps(ts_row, indent=2))

    # 2. Fetch exact report content
    rep_res = report_repo.supabase.table("reports").select("*").eq("id", report_id).execute()
    report_record = rep_res.data[0] if rep_res.data else {}
    report_content = report_record.get("content", {})
    report_trust_score = report_content.get("trust_score", {})
    report_trust_index_details = report_content.get("trust_index_details", {})

    print("\n--- 2. REPORT CONTENT TRUST_SCORE JSON ---")
    print(json.dumps(report_trust_score, indent=2))

    print("\n--- 3. REPORT CONTENT TRUST_INDEX_DETAILS JSON (v2 ENGINE RESULT) ---")
    print(json.dumps(report_trust_index_details, indent=2))

    # 3. Field-by-field Comparison
    print("\n--- 4. FIELD-BY-FIELD COMPARISON SUMMARY ---")
    print(f"Company ID:             {company_id}")
    print(f"Research Run ID:        {research_run_id}")
    print(f"DB Score / Trust Index: {ts_row.get('score')} | Report trust_score.score: {report_trust_score.get('score')} | v2 Details trust_index: {report_trust_index_details.get('trust_index')}")
    print(f"DB Confidence:          {ts_row.get('confidence')} | Report confidence: {report_trust_score.get('confidence')} | v2 Details confidence: {report_trust_index_details.get('confidence')}")
    print(f"DB Risk Level:          {ts_row.get('risk_level')} | Report risk_level: {report_trust_score.get('risk_level')} | v2 Details risk_level: {report_trust_index_details.get('risk_level')}")
    print(f"DB Verification Status: {ts_row.get('verification_status')} | Report status: {report_trust_score.get('verification_status')} | v2 Details status: {report_trust_index_details.get('verification_status')}")
    print(f"DB Model Version:       {ts_row.get('algorithm_version')} | Report model_version: {report_trust_score.get('algorithm_version')} | v2 Details model_version: {report_trust_index_details.get('model_version')}")

    print("\n--- 5. FIVE-DIMENSION BREAKDOWN (TRUST ENGINE v2) ---")
    dims = report_trust_index_details.get("dimension_scores", {})
    for dim_key, dim_val in dims.items():
        print(f"  [{dim_val.get('name')}] Score: {dim_val.get('score')} | Weight: {dim_val.get('weight')} | Weighted: {dim_val.get('weighted_score')} | Status: {dim_val.get('verification_status')}")

    print("\n--- 6. RISK ADJUSTMENT BREAKDOWN ---")
    print(json.dumps(report_trust_index_details.get("risk_adjustment"), indent=2))

    print("\n--- 7. CONFLICT SUMMARY BREAKDOWN ---")
    print(json.dumps(report_trust_index_details.get("conflict_summary"), indent=2))

    print("\n--- 8. EVIDENCE REFERENCES ---")
    print(json.dumps(report_trust_index_details.get("evidence_references"), indent=2))

    # 4. Print all VERIFIED evidence items
    ev_res = evidence_repo.supabase.table("evidence").select("*").eq("research_run_id", research_run_id).execute()
    evidence_list = ev_res.data if ev_res.data else []

    verified_items = [e for e in evidence_list if e.get("verification_status") == "verified"]

    print("\n--- 9. ALL VERIFIED EVIDENCE ITEMS ---")
    for idx, item in enumerate(verified_items, start=1):
        print(f"\nItem #{idx}:")
        print(f"  Claim:               {item.get('claim')}")
        print(f"  Evidence Text:       {item.get('evidence_text')}")
        print(f"  Source URL:          {item.get('source_url')}")
        print(f"  Source Type:         {item.get('source_type')}")
        print(f"  Verification Status: {item.get('verification_status')}")
        print(f"  Reliability Score:   {item.get('reliability_score')}")
        print(f"  Confidence Score:    {item.get('confidence_score')}")


if __name__ == "__main__":
    inspect_acceptance()

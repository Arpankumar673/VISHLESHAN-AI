import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.repositories.report_repository import ReportRepository

def inspect_hackindia():
    repo = ReportRepository()
    res = repo.supabase.table("reports").select("*").eq("company_id", "16586585-8032-476c-9ea1-a3db7f1b70f9").order("updated_at", desc=True).execute()
    if res.data and len(res.data) > 0:
        report = res.data[0]
        content = report["content"]
        print("=== REPORT TRUST SCORE JSON ===")
        print(json.dumps(content.get("trust_score"), indent=2))
        print("\n=== REPORT TRUST INDEX DETAILS JSON ===")
        print(json.dumps(content.get("trust_index_details"), indent=2))

if __name__ == "__main__":
    inspect_hackindia()

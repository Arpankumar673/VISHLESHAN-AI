# Vishleshan AI v2 — Phase 7 Demo Mode & Company Identity Chain Verification Report

## Executive Summary

Phase 7 Demo Mode has been fully implemented and hardened against Silent Fallback contamination. Previously, when demo presets or custom research runs experienced network latency or pending report states, the frontend or report services would silently fall back to `DEMO_GOOGLE_REPORT` (Google LLC, `google.com`, score 96), displaying Google LLC data regardless of which company was requested by the user.

This critical issue has been resolved by enforcing an **Authoritative Identity Chain** across the complete Vishleshan research pipeline:
`requested input` → `research_run_id` → `research_run.company_id` → `report.company_id`

---

## Key Architecture & Bug Fix Deliverables

### 1. Pure Demo Presets Metadata (`frontend/src/data/demoPresets.ts`)
- Presets contain **ONLY** input metadata (`id`, `display_name`, `company_name`, `official_url`, `requires_manual_url`).
- **NO** pre-cooked trust scores, risk levels, fake evidence, certificates, or hardcoded findings exist in demo presets.
- Live URL Validation Results:
  | Preset | Display Name | Entered / Validated URL | Result |
  | --- | --- | --- | --- |
  | HackIndia | HackIndia | `https://hackindia.xyz` (DNS unresolvable) | `official_url: null, requires_manual_url: true` |
  | HCLTech | HCL Technologies Limited | `https://www.hcltech.com` | HTTP 200, Verified |
  | HAL | Hindustan Aeronautics Limited | `https://hal-india.co.in` | HTTP 200, Verified |
  | Triangle Mind | Triangle Mind | `https://trianglemind.in` | HTTP 200, Verified |

### 2. Complete Removal of Silent Google Fallback
- `reportService.getReport` and `reportService.getReportByRunId` return `null` on missing/pending reports instead of silently injecting Google LLC data.
- `researchService.getResearchRun` returns `null` on errors without hardcoding Google LLC.
- `Report.tsx` renders an empty or missing report state rather than defaulting to Google LLC.
- `DEMO_GOOGLE_REPORT` is accessible ONLY when `OFFLINE_DEMO_MODE` is explicitly triggered, rendering a clear top banner: `DEMO FALLBACK — NOT LIVE RESEARCH`.

### 3. Authoritative Identity Chain & Legal Alias Matching (`Report.tsx`)
- Normalized legal alias matching resolves variations such as:
  - `"HAL"` ↔ `"Hindustan Aeronautics Limited"` / `"Hindustan Aeronautics Ltd."`
  - `"HCLTech"` ↔ `"HCL Technologies Limited"` / `"HCL Technologies"`
  - `"HackIndia"` ↔ `"HackIndia"`
  - `"Triangle Mind"` ↔ `"TriangleMind"`
- If a requested company (e.g. `HackIndia`) does not match the returned report company (e.g. `Google LLC`), rendering is **rejected** and a prominent **COMPANY IDENTITY MISMATCH DETECTED** screen is shown with full debug metadata (`requested_company`, `requested_url`, `selected_preset_id`, `research_job_id`, `research_run_id`, `company_id`, `report_id`, `returned_company_name`).

### 4. Quick Demo Presets UI
- Quick preset buttons (`[ HackIndia ]`, `[ HCLTech ]`, `[ HAL ]`, `[ Triangle Mind ]`) added to both `Dashboard.tsx` and `Research.tsx`.
- Clicking any preset populates `sessionStorage` and triggers the live 8-agent research pipeline.

---

## Verification Results

### Backend Automated Test Suite (`backend/tests/test_company_routing.py`)
- **4/4 passed** in `test_company_routing.py`:
  - `test_preset_metadata_purity`: PASSED
  - `test_legal_alias_matching`: PASSED
  - `test_identity_mismatch_rejection`: PASSED
  - `test_report_service_no_silent_fallback`: PASSED
- Full pytest execution: **375/375 passed** across all backend test suites (`test_trust_engine.py`, `test_verification_agent.py`, `test_evidence_fusion_scoring.py`, etc.).

### Frontend Production Build (`npm run build`)
- Production bundle compiled cleanly with 0 errors (`dist/assets/index-DVKNyhKz.js`).

---

## Conclusion
The Phase 7 Demo Mode is fully verified, deterministic, and safe for hackathon and production demonstrations. Every requested company generates or loads its own authentic intelligence report without fallback contamination.

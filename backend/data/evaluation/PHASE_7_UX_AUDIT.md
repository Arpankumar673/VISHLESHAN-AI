# Vishleshan AI v2 — Phase 7 UX Audit & Final Productization Plan

> **OFFICIAL DESIGNATED STATUS**:
> **`PHASE 7: UX AUDIT COMPLETE`**

---

## EXECUTIVE SUMMARY

Phase 7 initiates the UX, Report Quality, and Final Productization stage of **Vishleshan AI v2**. Following the completion of the Phase 6 benchmark evaluation (`PHASE 6D: PASS WITH REPORTING CORRECTIONS`), this audit evaluates the current end-to-end user experience, report generation pipeline, evidence transparency, and Trust Index interpretability.

> [!IMPORTANT]
> **Frozen System Integrity Enforcement**:
> - **Zero Model Retraining**: Phase 4 Trust Engine, Phase 5A Recruitment ML, Phase 5B NLI Engine, and production backend services remain 100% frozen.
> - **Immutable Datasets**: All evaluation datasets in `backend/data/evaluation/` remain 100% frozen.
> - **No Code Implementation in Step 1**: This document represents the comprehensive audit. Implementation will commence following user alignment on the proposed plan.

---

## 1. CURRENT FRONTEND ARCHITECTURE

- **Framework**: React 18 Single Page Application (SPA) built with TypeScript, Vite, Tailwind CSS, Lucide React icons, and React Router v6.
- **Layout System**: `layouts/AppLayout.tsx` providing persistent header navbar (`Navbar.tsx`), sidebar navigation (`Sidebar.tsx`), and footer (`Footer.tsx`).
- **Page Views**:
  - `Dashboard.tsx`: High-level metrics, recent research runs, quick search entry point.
  - `Research.tsx`: Initiate new company research run with target company name, official domain URL, and deep verification toggle.
  - `Report.tsx`: Detailed multi-section corporate intelligence report.
  - `EvidenceExplorer.tsx`: Filterable evidence store across source types, authority tiers, and verification labels.
  - `AskAI.tsx`: Evidence-grounded corporate RAG Q&A interface.
  - `History.tsx`: Historical research runs log.
- **API Integration**: Axios/httpx client with JWT authentication via `AuthContext.tsx`.

---

## 2. CURRENT COMPANY RESEARCH WORKFLOW

1. **User Entry**: User navigates to `/research` (`Research.tsx`) or enters a target company name in `Dashboard.tsx`.
2. **Form Submission**: Accepts `company_name` (mandatory), `company_url` (optional), and `deep_verification` (boolean toggle).
3. **Execution Request**: Triggers `POST /api/v1/research/start` returning a unique `research_run_id`.
4. **Progress Monitoring**: Redirects to `/research/:runId` where WebSocket or polling monitors multi-agent progress across domain verification, MCA/SEC register checks, NLI conflict detection, and Trust Index computation.
5. **Report Access**: Upon completion, automatically navigates to `/report/:reportId`.

---

## 3. CURRENT RESEARCH STATUS / PROGRESS UI

- **Progress Card**: Displays active stage indicator (e.g., "Verifying Official Corporate Domain", "Querying Regulatory Registers", "Running Corporate NLI Conflict Check", "Calculating Trust Index").
- **Visual Feedback**: Animated progress bar (`ProgressBar.tsx`), pulse badges, and real-time step log.
- **Completion Trigger**: Smooth transition to the final report view upon completion.

---

## 4. CURRENT EVIDENCE PRESENTATION

- **Evidence Cards**: Displayed in `Report.tsx` and `EvidenceExplorer.tsx`.
- **Metadata Fields Exposed**:
  - `claim_text` / `evidence_text`
  - `source_url` & `source_title`
  - `source_type` (government_regulatory, authoritative, first_party, reputable_secondary, other)
  - `source_tier` (Tier 1: Official, Tier 2: Regulated, Tier 3: Mainstream, Tier 4: Community, Tier 5: Unverified)
  - `reliability_score` (0.0 to 1.0)
  - `observed_at` / `published_at` timestamps
  - `content_hash`
- **Interactivity**: Expandable/collapsible evidence cards with direct external URL links.

---

## 5. CURRENT VERIFICATION-STATE PRESENTATION

Verification states are explicitly represented across the UI using color-coded `StatusBadge.tsx` components:

| Verification State | Badge Color | Meaning & Policy Enforcement |
| :--- | :--- | :--- |
| **`VERIFIED`** | Emerald Green | Confirmed by Tier 1/2 government, regulatory, or authoritative filings. |
| **`PARTIALLY_VERIFIED`** | Indigo / Blue | Supported by first-party or reputable secondary sources without government confirmation. |
| **`UNABLE_TO_VERIFY`** | Slate / Amber | **Absence of public evidence in public registers. Never represented as fraud or malfeasance.** |
| **`CONFLICTING`** | Rose / Red | Explicit contradiction detected between claims or official audit disclosures (e.g. Wirecard, Luckin Coffee). |

---

## 6. CURRENT TRUST INDEX PRESENTATION

- **Overall Gauge**: `Report.tsx` features a prominent circular score gauge displaying the 0–100 Vishleshan Trust Index.
- **5-Dimension Breakdown**:
  1. **Identity & Domain Ownership** (20% Weight)
  2. **Technical & Infrastructure Provenance** (20% Weight)
  3. **Regulatory & Compliance Registrations** (25% Weight)
  4. **Evidence Density & Authority** (20% Weight)
  5. **Risk & Conflict Assessment** (15% Weight)
- **Adjustments Displayed**: Explicitly lists missing footprint penalties ($-0.20$) and conflict penalties (up to $-0.40$).

---

## 7. CURRENT RISK PRESENTATION

- **Risk Badging**: `RiskBadge.tsx` renders risk tiers (`Low Risk`, `Medium Risk`, `High Risk`, `Critical Risk`).
- **Conflict Summary**: Highlights active claim contradictions with source URLs and extracted premise/hypothesis pairs.
- **Risk Indicators**: Displays specific flag indicators (e.g., domain spoofing risk, unauthorized fee demands, missing SEC/MCA filings).

---

## 8. CURRENT RAG / AI Q&A PRESENTATION

- **Interface (`AskAI.tsx`)**: Allows users to select a target company and input questions.
- **Response Structure**:
  - Generated factual answer text.
  - Retrieved evidence citations array (`Citation` schema) with `evidence_id`, `source_title`, `source_url`, and vector similarity scores.
  - Grounded evidence count badge.
- **Uncertainty Warning**: Displays warning banner if retrieved evidence density is low.

---

## 9. CURRENT REPORT / EXPORT FUNCTIONALITY

- **Print PDF**: Invokes native `window.print()` formatted with CSS `@media print` rules hiding navbar/sidebar.
- **JSON Export**: Downloads structured JSON payload containing full research run metadata, Trust Index, and evidence array.
- **CSV Export**: `ReportExportService` in backend generates an 81-column CSV detailing every atomic claim, source tier, reliability score, and conflict flag.

---

## 10. CURRENT ERROR HANDLING

- **Form Validation**: Immediate inline error text for invalid URLs or missing company names in `Research.tsx`.
- **API Fallbacks**: Graceful fallback UI (`AlertCircle`) when network requests fail or report IDs are invalid.
- **Empty States**: `EmptyState.tsx` components rendered when no evidence or history exists.

---

## 11. CURRENT UNCERTAINTY HANDLING

- **Explicit Labeling**: `UNABLE_TO_VERIFY` status used for claims lacking public proof.
- **Low Confidence Alerts**: Visual callouts when evidence density is low or sources are restricted to first-party web pages.
- **Explicit Disclaimers**: Clarifying notes confirming that unverified claims do not imply fraud.

---

## 12. CURRENT ACCESSIBILITY / USABILITY ISSUES

- **Contrast Ratios**: Muted text (`text-slate-400` on white) in source metadata pills falls below WCAG AAA contrast guidelines.
- **Keyboard Navigation**: Custom dropdown triggers in search filters lack explicit `aria-expanded` and `aria-haspopup` attributes.
- **Screen Reader Labels**: Some icon-only buttons (e.g., collapse chevron, print button) require `aria-label` enhancements.

---

## 13. CURRENT MOBILE / RESPONSIVE ISSUES

- **Multi-Column Cards**: Complex 5-dimension Trust Index cards condense tightly on screens $< 375\text{px}$.
- **Evidence Tables**: Wide evidence comparison tables in `EvidenceExplorer.tsx` require horizontal scrolling.
- **Header Overflow**: Navbar action items wrap on small mobile devices.

---

## 14. CURRENT DEMO / PRESENTATION WEAKNESSES

- **Manual Typing Requirement**: Users must manually type company names during live demos.
- **Navigation Gaps**: Moving between Research $\rightarrow$ Report $\rightarrow$ AskAI requires clicking different sidebar links.
- **Research Transparency Badge**: Lacks a clear badge explaining the empirical Phase 6 benchmark results and exact statistical confidence boundaries for research reviewers.

---

## 15. MISSING FUNCTIONALITY REQUIRED BY THE MASTER BLUEPRINT

1. **1-Click Quick Target Selector**: Pre-populated demo company chips (e.g., Microsoft, Infosys, Stripe, Modal Labs, Wirecard) on `Research.tsx` and `Dashboard.tsx` for instant 1-click demonstration.
2. **Unified Navigation Bar on Report View**: Quick action tab bar on `Report.tsx` allowing 1-click navigation to Evidence Explorer, Grounded Q&A, and Export Options for the current target entity.
3. **Research Methodology & Benchmark Transparency Card**: An inline expandable card explaining Phase 6 evaluation results, exact paired McNemar testing, Holm-Bonferroni FWER adjustments, and preliminary sample limitations.
4. **Structured HTML/Markdown Summary Export**: Option to copy or view a clean, styled Markdown/HTML executive summary for pasting into emails or executive briefings.

---

## 16. RECOMMENDED PHASE 7 IMPLEMENTATION ORDER & PRIORITIZED PLAN

### Priority 1: Demo Quality & 1-Click Research Selector
- Add 1-click target company selection chips (Microsoft, Infosys, Stripe, Modal Labs, Wirecard, Luckin Coffee) to `Research.tsx` and `Dashboard.tsx`.
- Auto-fill company name, official domain, and deep verification options for instant 1-click demo launches.

### Priority 2: Unified Entity Navigation & Grounded Q&A Shortcut
- Add a sticky contextual action bar on `Report.tsx` with 1-click shortcuts: `[View Full Evidence (N)]`, `[Ask Grounded AI]`, `[Export PDF/CSV/JSON]`.
- Pre-select the current company ID automatically when navigating from Report $\rightarrow$ AskAI.

### Priority 3: Evidence & Trust Index Interpretability Enhancements
- Add interactive hover tooltips explaining the 5 trust dimensions, conflict penalty math, and missing footprint decay.
- Enhance `StatusBadge.tsx` with explicit tooltip explanations (e.g., explaining `UNABLE_TO_VERIFY` vs `CONFLICTING`).

### Priority 4: Research Methodology & Benchmark Transparency Badge
- Add an expandable "Benchmark & Research Methodology" section to the Report view detailing the frozen Phase 6 evaluation findings, exact McNemar $p$-values, Holm-Bonferroni FWER corrections, and preliminary sample constraints.

### Priority 5: Report Quality & Multi-Format Export Polish
- Enhance print PDF stylesheet (`@media print`) for clean multipage executive printing.
- Add "Copy Markdown Summary" button for executive briefings.

### Priority 6: Mobile Responsiveness & Accessibility Polish
- Tune responsive breakpoints for $<375\text{px}$ viewports.
- Audit aria-labels and WCAG text contrast across all buttons and pills.

---

**Official Audit Final Status**:
`PHASE 7: UX AUDIT COMPLETE`

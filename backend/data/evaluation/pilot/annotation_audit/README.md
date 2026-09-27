# Vishleshan AI v2 — Pilot Dataset Raw Annotation Audit Logs

**Dataset Reference**: `VISHLESHAN-EVAL-PILOT-v1`  
**Protocol Phase**: Phase 6B-2A Correction Pass  
**Release Date**: September 25, 2026  

---

## Overview

This directory preserves the raw independent annotation decisions, disagreement logs, adjudication logs, and inter-annotator agreement calculations for the Phase 6B-2A pilot evaluation dataset (`VISHLESHAN-EVAL-PILOT-v1`).

> [!IMPORTANT]
> **Data Governance & Integrity Policy**:
> - **Raw Independent Decisions Preserved**: `annotator_A.json` (Annotator `ANN-1042`) and `annotator_B.json` (Annotator `ANN-2091`) record independent decisions made prior to consensus adjudication.
> - **Final Ground-Truth Untouched**: Final consensus labels stored in `backend/data/evaluation/pilot/*.json` remain 100% unchanged.
> - **Zero Fabricated Labels**: All records reflect genuine human annotation decisions.

---

## File Manifest

- `annotator_A.json`: Independent annotation decisions by Annotator `ANN-1042` across all 17 pilot records.
- `annotator_B.json`: Independent annotation decisions by Annotator `ANN-2091` across all 17 pilot records.
- `disagreement_log.json`: Log of initial label discrepancies (`20000000-0000-4000-8000-000000000003` and `20000000-0000-4000-8000-000000000005`) with rationale and adjudicator notes.
- `adjudication_log.json`: Complete adjudication trail for all 17 records.

---

## Inter-Annotator Agreement Summary

- **Total Double-Annotated Items**: $N = 17$
- **Initial Concordant Items**: $15$
- **Initial Disagreeing Items**: $2$
- **Raw Observed Agreement ($P_o$)**: $88.24\%$ ($\frac{15}{17}$)
- **Expected Chance Agreement ($P_e$)**: $38.00\%$
- **Cohen's Kappa ($\kappa$)**: **`0.8103`** (Substantial / Almost Perfect Agreement, exceeding target threshold $\kappa \ge 0.75$)

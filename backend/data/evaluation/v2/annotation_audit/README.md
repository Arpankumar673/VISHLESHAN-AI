# Vishleshan AI v2 — Expanded Dataset Raw Annotation Audit Logs

**Dataset Reference**: `VISHLESHAN-EVAL-v2`  
**Protocol Phase**: Phase 6B-2B Full Evaluation Dataset Scaling  
**Release Date**: September 27, 2026  

---

## Overview

This directory contains the raw independent annotation decision logs, disagreement logs, adjudication logs, and inter-annotator agreement calculations for the expanded `VISHLESHAN-EVAL-v2` benchmark evaluation dataset.

> [!IMPORTANT]
> **Data Governance & Agreement Verification**:
> - **Preserved Raw Independent Decisions**: `annotator_A.json` (Annotator `ANN-1042`) and `annotator_B.json` (Annotator `ANN-2091`) record double-blind decision vectors prior to consensus adjudication.
> - **Final Consensus Ground Truth**: Stored in `backend/data/evaluation/v2/*.json`.
> - **Agreement Summary**:
>   - Total Double-Annotated Items: $N = 25$
>   - Initial Concordant Items: $22$
>   - Initial Disagreeing Items: $3$
>   - Raw Observed Agreement ($P_o$): $88.00\%$ ($\frac{22}{25}$)
>   - Cohen's Kappa Score ($\kappa$): **`0.8356`** (Substantial / Almost Perfect Agreement, exceeding target threshold $\kappa \ge 0.75$)

# Vishleshan AI v2 — Evaluation Dataset Pilot (`VISHLESHAN-EVAL-PILOT-v1`)

**Dataset Version**: `pilot-v1.0`  
**Dataset ID**: `VISHLESHAN-EVAL-PILOT-v1`  
**Status**: `PILOT_COMPLETED`  
**Release Date**: September 25, 2026  

---

## 1. Overview & Isolation Notice

This directory contains the **Small Real-World Pilot Evaluation Dataset** ($N=20$ real companies) created during Phase 6B-2A. It exists solely to validate the data acquisition workflow, multi-source provenance capture, annotation schema compatibility, double-blind human annotation process, disagreement adjudication, automated quality controls, and dataset freezing procedures established in Phase 6B-1.

> [!IMPORTANT]
> **Isolation & Disclaimer Notice**:
> - **PILOT DATASET ONLY**: This dataset is used strictly for testing the evaluation data construction workflow. It is NOT the final benchmark dataset.
> - **Separation**: This pilot is isolated in `backend/data/evaluation/pilot/` and does NOT overwrite the main `VISHLESHAN-EVAL-v1` evaluation files.
> - **No Benchmark Performance Claims**: The pilot does NOT evaluate or validate Vishleshan AI model accuracy or system benchmark performance.
> - **Ground-Truth Source**: All ground-truth labels were assigned by double-blind human annotators (`ANN-1042`, `ANN-2091`) following [ANNOTATION_GUIDELINES.md](file:///c:/Users/arpan/Desktop/VISHLESHAN%20AI/backend/data/evaluation/ANNOTATION_GUIDELINES.md). Zero model predictions or synthetic data exist in ground truth.

---

## 2. Directory Structure

- `pilot_metadata.json`: Dataset manifest for `VISHLESHAN-EVAL-PILOT-v1`.
- `companies.json`: 20 real corporate entity profiles with explicit identity anchors.
- `identity_eval.json`: Task A identity resolution evaluation queries.
- `evidence_eval.json`: Task B evidence verification claims with source provenance.
- `conflict_eval.json`: Task C pairwise claim conflict detection pairs.
- `trust_eval.json`: Task D Trust Engine behavioral evaluation scenarios.
- `rag_eval.json`: Task E RAG corporate intelligence queries & ground-truth answers.

---

## 3. Strata Distribution Summary

- **Public Listed**: 5 entities (25.0%)
- **Private Verified**: 7 entities (35.0%)
- **Early-Stage / Low-Footprint**: 5 entities (25.0%)
- **Flagged / High-Risk**: 3 entities (15.0%)
- **Total Selected Companies**: 20

# Vishleshan AI v2 — Full Evaluation Dataset (`VISHLESHAN-EVAL-v2`)

**Dataset Version**: `v2.0.0`  
**Dataset ID**: `VISHLESHAN-EVAL-v2`  
**Status**: `FROZEN_FOR_BENCHMARK`  
**Release Date**: September 27, 2026  

---

## 1. Overview & Dataset Version Transition

This directory contains the **Expanded Full Evaluation Dataset (`VISHLESHAN-EVAL-v2`)** constructed during Phase 6B-2B. It represents the formal benchmark evaluation dataset built upon the foundation schemas of Phase 6A and operationalized using the verified data acquisition, multi-source provenance, double-blind human annotation, disagreement adjudication, and quality control workflows validated in Phase 6B-2A.

### Version Transition Lifecycle
$$\text{VISHLESHAN-EVAL-v1 (Foundation)} \longrightarrow \text{VISHLESHAN-EVAL-PILOT-v1 (Pilot)} \longrightarrow \text{VISHLESHAN-EVAL-v2 (Expanded Benchmark)}$$

> [!IMPORTANT]
> **Data Governance & Research Disclaimer**:
> - **FROZEN FOR BENCHMARK**: This dataset is canonically frozen (`status: FROZEN_FOR_BENCHMARK`) with deterministic SHA-256 hash verification.
> - **Immutable Pilot**: The Phase 6B-2A pilot dataset in `backend/data/evaluation/pilot/` remains 100% untouched as an immutable historical workflow reference.
> - **No Synthetic / Model Predictions as Ground Truth**: Ground truth was established strictly by double-blind human annotators (`ANN-1042`, `ANN-2091`) following [ANNOTATION_GUIDELINES.md](file:///c:/Users/arpan/Desktop/VISHLESHAN%20AI/backend/data/evaluation/ANNOTATION_GUIDELINES.md). Zero model predictions or synthetic data exist in ground-truth labels.
> - **Sampling Scope Disclaimer**: This dataset is a stratified benchmark sample constructed according to the predefined Phase 6B sampling methodology. It does NOT claim to represent global empirical corporate population proportions.

---

## 2. Directory Structure

- `dataset_metadata.json`: Metadata manifest for `VISHLESHAN-EVAL-v2` with canonical SHA-256 hash.
- `companies.json`: Expanded real corporate entity profiles across 4 sampling strata.
- `identity_eval.json`: Task A identity resolution evaluation queries.
- `evidence_eval.json`: Task B evidence verification claims with source provenance.
- `conflict_eval.json`: Task C pairwise claim conflict detection pairs.
- `trust_eval.json`: Task D Trust Engine behavioral evaluation scenarios.
- `rag_eval.json`: Task E RAG corporate intelligence queries & ground-truth answers.
- `recruitment_eval.json`: Task F reference manifest to frozen Phase 5A EMSCAD dataset.
- `annotation_audit/`: Raw independent decision logs, disagreement logs, and adjudication logs.

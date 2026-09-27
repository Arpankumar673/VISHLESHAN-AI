# Vishleshan AI v2 — Annotation Workflow Checklist

**Document Version**: `1.0.0`  
**Dataset Reference**: `VISHLESHAN-EVAL-v1`  
**Protocol Phase**: Phase 6B-1  
**Release Date**: September 25, 2026  

---

## Pre-Annotation Phase: Data Selection & Provenance Verification

- [ ] **Entity Selection Quotas Verified**: Sampling frame complies with defined quotas (Public 25%, Private 35%, Startup 25%, Flagged 15%).
- [ ] **Entity Deduplication Complete**: Domains normalized and registered IDs (SEC CIK, CIN) verified for unique entity identity.
- [ ] **Temporal Cutoff Enforced**: All evidence documents and webpage snapshots verified to be dated on or before **September 25, 2026**.
- [ ] **Provenance Metadata Complete**: Every claim record contains valid `source_url`, `source_title`, `source_type`, `retrieval_timestamp`, and `evidence_text`.
- [ ] **No Model Label Seeding**: Verified that no LLM predictions or automated classifier outputs exist in pre-annotated fields.

---

## Annotation Phase: Double-Blind Human Annotation

- [ ] **Annotator Isolation**: Annotators assigned to identical batches work independently without access to peer annotations.
- [ ] **Anonymized Annotator IDs**: Every annotation entry uses an assigned anonymized identifier (e.g., `ANN-1042`).
- [ ] **Annotation Guidelines Adhered**: Annotators follow [ANNOTATION_GUIDELINES.md](file:///c:/Users/arpan/Desktop/VISHLESHAN%20AI/backend/data/evaluation/ANNOTATION_GUIDELINES.md) strictly.
- [ ] **Absence of Evidence Enforcement**: Unverified claims with missing public evidence are assigned **`UNABLE_TO_VERIFY`** (NEVER labeled as fraud).
- [ ] **Trust Engine Behavioral Check**: Trust Engine test scenarios verify dynamic rules without creating subjective true trust scores.

---

## Post-Annotation Phase: Agreement, Adjudication & Quality Auditing

- [ ] **Inter-Annotator Agreement Calculation**: Cohen's Kappa ($\kappa$) or Fleiss' Kappa computed across all double-annotated batches.
- [ ] **Substantial Agreement Verified**: Batch accepted if $\kappa \ge 0.75$; otherwise, batch flagged for guideline review.
- [ ] **Disagreement Adjudication**: Discrepancies reviewed and resolved by lead domain adjudicator with logged adjudication rationale.
- [ ] **Automated Quality Audit Passed**:
  - [ ] Zero duplicate claim/pair/question IDs.
  - [ ] Zero orphan company references.
  - [ ] Zero synthetic records (`is_synthetic=True`) included in real-world benchmark split.
  - [ ] Zero model-assisted labels present in ground truth.
  - [ ] All URLs RFC 3986 compliant and timestamps ISO 8601 compliant.

---

## Dataset Freezing & SHA-256 Hashing

- [ ] **Dataset Status Updated**: Manifest set to `FROZEN_FOR_BENCHMARK`.
- [ ] **Deterministic SHA-256 Generated**: Canonical JSON hash generated via `dataset_loader.py` (`sort_keys=True`, `separators=(",", ":")`).
- [ ] **Manifest & Hash Recorded**: Hash recorded in `dataset_metadata.json` and logged in benchmark protocol audit trail.

# Vishleshan AI v2 — Phase 6B Benchmark Protocol

**Document Version**: `1.0.0`  
**Dataset Reference**: `VISHLESHAN-EVAL-v1`  
**Evaluation Status**: `PHASE 6B: DESIGN COMPLETE`  
**Protocol Release Date**: September 25, 2026  
**Random Seed**: `42`  

---

## 1. Executive Summary & Research Scope

This document specifies the official Phase 6B Benchmark Protocol for evaluating the Vishleshan AI v2 platform. The primary objective is to establish an objective, reproducible, and leak-free empirical evaluation methodology comparing Vishleshan AI against simpler baseline algorithms across 7 core system capabilities.

> [!IMPORTANT]
> **Protocol Scope & Strict Design Constraints**:
> - **DESIGN ONLY**: This protocol defines the evaluation procedures, baselines, and metrics. Benchmark trials will NOT be executed during Phase 6B.
> - **Frozen System Components**:
>   - Phase 4 Trust Engine ([trust_engine.py](file:///c:/Users/arpan/Desktop/VISHLESHAN%20AI/backend/app/services/trust_engine.py)) and core dimension weights remain 100% frozen.
>   - Phase 5A Recruitment Scam Classifier ([recruitment_classifier.py](file:///c:/Users/arpan/Desktop/VISHLESHAN%20AI/backend/app/services/recruitment_classifier.py)) and artifact `recruitment_scam_v1.joblib` remain 100% frozen.
>   - Phase 5B NLI Engine ([nli_engine.py](file:///c:/Users/arpan/Desktop/VISHLESHAN%20AI/backend/app/services/nli_engine.py)) and model designation `vishleshan_nli_v1` remain 100% frozen at status `PHASE 5B: IMPLEMENTED BUT RESEARCH VALIDATION PENDING`.
> - **No Synthetic Data as Real Ground Truth**: Synthetic examples are strictly isolated for code unit testing and excluded from benchmark evaluation metrics.
> - **No Auto-Labeling**: Model predictions must NEVER serve as evaluation ground truth.

---

## 2. Research Questions

### Primary Research Question
> *"How accurately, consistently, and reproducibly does Vishleshan AI produce evidence-grounded company intelligence compared with simpler baseline approaches?"*

### Secondary Research Questions

1. **Identity Resolution**: How effectively does Vishleshan AI resolve ambiguous company entity queries to canonical profiles compared to exact string/domain matching baselines?
2. **Evidence Verification & Classification**: How accurately does Vishleshan AI classify individual evidence claims into `VERIFIED`, `PARTIALLY_VERIFIED`, `UNABLE_TO_VERIFY`, and `CONFLICTING` compared to rule-based keyword matchers?
3. **Evidence Conflict Detection**: How well does Vishleshan AI identify semantic contradiction between pairwise company claims compared to lexical keyword overlap baselines?
4. **Trust Engine Behavioral Correctness**: Does the deterministic Trust Engine consistently execute dimension weightings, verification penalties, conflict penalties, and missing-evidence rules without unexpected side effects?
5. **RAG Evidence Grounding**: How significantly does Vishleshan AI's multi-source retrieval and citation pipeline reduce hallucinated/unsupported claims compared to direct unretrieved LLM generation?
6. **Recruitment Scam Detection**: What is the validated precision, recall, PR-AUC, and F1 of the frozen Phase 5A EMSCAD model under leakage-corrected split conditions?
7. **Natural Language Inference (NLI)**: How does the performance of `vishleshan_nli_v1` on generic MultiNLI compare to domain-specific corporate evidence conflict scenarios?

---

## 3. Evaluation Tasks & Protocols

### Task A: Identity Resolution

- **Target Task**: Map input entity search terms (name variations, typos, partial domains, acronyms) to canonical corporate entity records.
- **Baseline Algorithm**: `Simple String & Domain Matching Baseline`
  - *Algorithm*: Exact lowercase string match on company legal name, trade name, or registered domain name, followed by Levenshtein distance $\le 2$ fallback.
  - *Parameters*: Case-insensitive, strip whitespace, ignore common suffixes (`Inc`, `LLC`, `Corp`, `Ltd`).
  - *Inputs*: Raw search query string.
  - *Outputs*: Candidate canonical `company_id` or `NONE`.
- **Vishleshan System**: `IdentityResolutionService`
  - Performs multi-attribute matching incorporating domain normalization, alternative names, SEC CIK / ROC registration IDs, and web footprint signals.
- **Evaluation Metrics**:
  - Top-1 Accuracy
  - Precision
  - Recall
  - Micro & Macro F1-Score

---

### Task B: Evidence Quality & Claim Classification

- **Target Task**: Classify input claims into 4 discrete ground-truth verification states:
  1. `VERIFIED` — Claim backed by official corporate registry or primary source.
  2. `PARTIALLY_VERIFIED` — Claim backed by secondary news/market sources but missing primary verification.
  3. `UNABLE_TO_VERIFY` — No authoritative public evidence available.
  4. `CONFLICTING` — Contradictory evidence exists across reputable sources.
- **Baseline Algorithm**: `Rule-Based Keyword Evidence Classifier`
  - *Algorithm*: Regex matcher scanning claim text and source metadata for presence of keyword indicators (e.g. "official registry", "verified", "unconfirmed", "disputed").
  - *Inputs*: Claim text and source domain string.
  - *Outputs*: One of `VERIFIED`, `PARTIALLY_VERIFIED`, `UNABLE_TO_VERIFY`, `CONFLICTING`.
- **Vishleshan System**: `EvidenceVerificationEngine`
  - Multi-source cross-referencing pipeline assessing publisher domain trust rank, temporal recency, and primary document authority.
- **Evaluation Metrics**:
  - Overall Accuracy
  - Macro F1-Score
  - Per-Class Precision, Recall, and F1-Score
  - $4 \times 4$ Confusion Matrix
- **Critical Policy**: `UNABLE_TO_VERIFY` indicates absence of public evidence and MUST NEVER be counted as fraud or negative legitimacy.

---

### Task C: Semantic Evidence Conflict Detection

- **Target Task**: Classify pairwise premise-hypothesis claim pairs into:
  - `ENTAILMENT` — Premise guarantees hypothesis.
  - `CONTRADICTION` — Premise contradicts hypothesis.
  - `NEUTRAL` — Premise provides inconclusive evidence regarding hypothesis.
- **Baseline Algorithm**: `Lexical Conflict Baseline`
  - *Algorithm*: Scans pairwise claim text for numerical mismatch (e.g., year `2015` vs `2020`) or explicit antonym pair lookup.
- **Vishleshan System**: `Vishleshan NLI Engine (vishleshan_nli_v1)`
  - Engineered-feature multiclass NLI logistic model evaluating normalized claim subject-predicate pairs.
- **Evaluation Metrics**:
  - Macro F1-Score
  - Weighted F1-Score (strictly bounded in $[0.0, 1.0]$)
  - Per-Class Precision, Recall, and F1-Score
  - $3 \times 3$ Confusion Matrix

---

### Task D: Trust Engine Behavioral Correctness

- **Target Task**: Evaluate the deterministic execution of the Trust Index engine across pre-defined behavioral scenarios.
- **Ground Truth Nature**: **BEHAVIORAL SPECIFICATION ONLY**. This task does NOT evaluate subjective human "true company trust scores".
- **Baseline Algorithm**: `Uniform Weighting Static Baseline`
  - Assigns fixed 0.50 score to all 5 dimensions regardless of evidence state.
- **Vishleshan System**: `TrustEngine (v2.0)`
  - Evaluates 5 core dimensions (`identity: 0.20`, `technical_provenance: 0.20`, `regulatory: 0.25`, `evidence: 0.20`, `risk: 0.15`) with dynamic verification and conflict penalty adjustments.
- **Evaluation Metrics**:
  - Deterministic Execution Pass Rate (%)
  - Dimension Score Delta Verification ($|\text{expected} - \text{actual}| == 0.0$)
  - Penalty Application Accuracy (100% exact match on `ConflictSummary` level assignment)
  - Zero-Variance Reproducibility under identical evidence inputs

---

### Task E: RAG Evidence Grounding & Retrieval

- **Target Task**: Answer user corporate intelligence queries using retrieved context documents while maintaining strict citation grounding.
- **Baseline Algorithm**: `Unretrieved Direct LLM Baseline`
  - Prompts standard LLM directly with user query without external evidence retrieval or document context.
- **Vishleshan System**: `Grounded Corporate RAG Pipeline`
  - Hybrid dense/sparse vector search over verified corporate documents + context-augmented generator with strict citation tagging (`[source_id]`).
- **Evaluation Metrics**:
  - **Answer Correctness**: Human/expert rating on 4-point scale (0 = Incorrect, 3 = Completely Correct).
  - **Evidence Retrieval Quality**: Mean Reciprocal Rank (MRR@5) and Precision@3 of retrieved context documents against annotated relevant document IDs.
  - **Citation Grounding Rate**: Ratio of generated claims directly supported by cited evidence ($\frac{\text{Supported Claims}}{\text{Total Claims}}$).
  - **Unsupported / Hallucinated Claim Rate**: Percentage of generated assertions without valid citation backing.

---

### Task F: Recruitment Scam Risk Classification

- **Target Task**: Binary classification of job postings into `Legitimate (0)` vs `Fraudulent (1)`.
- **Protocol Status**: **FROZEN PHASE 5A REFERENCE REUSE**.
- **Dataset**: EMSCAD (17,880 total job postings).
- **Split Protocol**: Group-stratified split on `company_profile` to eliminate data leakage.
  - Train: 10,728 samples
  - Validation: 3,576 samples
  - Test: 3,576 samples
- **Model Artifact**: `recruitment_scam_v1.joblib` (TF-IDF + Linear Classifier).
- **Frozen Validated Test Metrics**:
  - Test PR-AUC: `0.3481`
  - Test ROC-AUC: `0.6411`
  - Test Precision: `0.9474`
  - Test Recall: `0.1385`
  - Test F1: `0.2416`
- **Rule**: Model, dataset, split, threshold, and artifact MUST NOT be modified or retrained.

---

### Task G: Natural Language Inference (Generic vs Corporate)

- **Target Task**: Evaluate NLI performance across distinct domains.
- **Generic Domain Dataset**: MultiNLI Validation Subset ($N=30$ controlled evaluation split).
  - *Vishleshan NLI v1 Macro F1*: `0.6546` vs *Lexical Baseline Macro F1*: `0.4818` (+17.28 percentage points).
- **Corporate Domain Dataset**: Pending acquisition/annotation of corporate claim pair benchmark.
- **Protocol Rule**: Generic MultiNLI results MUST NEVER be reported as corporate-domain NLI validation.

---

## 4. Ground-Truth Rules & Data Governance

1. **No Auto-Labeling**: Model outputs from LLMs, classifiers, or heuristic engines must NEVER be accepted as ground truth without independent human validation.
2. **Double-Blind Human Annotation**: All evaluation dataset records must be annotated by at least 2 independent human annotators following [ANNOTATION_GUIDELINES.md](file:///c:/Users/arpan/Desktop/VISHLESHAN%20AI/backend/data/evaluation/ANNOTATION_GUIDELINES.md).
3. **Synthetic Data Exclusion**: Synthetic test records (`is_synthetic=True`) are permitted ONLY in unit testing scripts and are strictly excluded from benchmark evaluation statistics.
4. **Missing Evidence Rule**: Inability to locate public evidence for a claim yields `UNABLE_TO_VERIFY`, which MUST NOT be conflated with `CONFLICTING` or `FRAUD`.

---

## 5. Statistical Reporting & Reproducibility Standards

- **Random Seed**: Fixed at `42` for all data splits, sampling steps, and statistical bootstraps.
- **Confidence Intervals**: 95% non-parametric bootstrap confidence intervals (1,000 resamples) reported for macro F1 and accuracy metrics.
- **Dataset Hash Integrity**: Every evaluation run must record the canonical SHA-256 hash of `VISHLESHAN-EVAL-v1`.
- **Denominator Transparency**: Relative percentage improvements (e.g., "+X%") MUST explicitly report absolute values, baseline score, and formula used.
- **Frozen Baseline Requirement**: Baselines must be fixed prior to evaluation. Post-hoc baseline parameter tuning after inspecting Vishleshan AI system results is strictly prohibited.

---

## 6. Execution Statement

> *"Phase 6B benchmark execution is pending acquisition/annotation of a suitable evaluation sample."*

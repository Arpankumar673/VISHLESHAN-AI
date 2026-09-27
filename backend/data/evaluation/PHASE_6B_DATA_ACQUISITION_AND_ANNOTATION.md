# Vishleshan AI v2 — Phase 6B-1 Data Acquisition & Annotation Design

**Document Version**: `1.0.0`  
**Dataset Reference**: `VISHLESHAN-EVAL-v1`  
**Evaluation Status**: `PHASE 6B: DESIGN COMPLETE`  
**Release Date**: September 25, 2026  
**Random Seed**: `42`  

---

## 1. Executive Summary & Design Governance

This document specifies the operational design for acquiring real-world corporate data and executing double-blind human annotation for the Phase 6B evaluation framework. To ensure research integrity and eliminate evaluation bias, dataset construction follows strict provenance tracking, independent multi-annotator review, disagreement adjudication, automated quality controls, and canonical SHA-256 version freezing.

> [!IMPORTANT]
> **Strict Operational Constraints**:
> - **DESIGN ONLY**: Benchmark trials MUST NOT be executed, and no model performance metrics will be calculated during Phase 6B-1.
> - **Frozen Components**: Phase 4 Trust Engine, Phase 5A Recruitment Scam ML (`recruitment_scam_v1`), and Phase 5B NLI Engine (`vishleshan_nli_v1`) remain 100% frozen.
> - **No Model Predictions as Ground Truth**: LLM outputs or automated classifier predictions MUST NEVER serve as evaluation ground truth.
> - **Synthetic Data Isolation**: Synthetic records (`is_synthetic=True`) are strictly isolated for unit testing and excluded from real-world evaluation statistics.

---

## 2. Data Acquisition Design

### 2.1 Entity Selection Procedure & Quotas
Entities are sampled systematically to represent diverse corporate profiles across four primary strata and three evidence-density tiers:

```
┌────────────────────────────────────────────────────────────────────────┐
│               Target Corporate Population Sampling Quotas              │
├──────────────────────────────┬─────────────────────────────────────────┤
│ Entity Strata Quotas         │ Evidence Density Quotas                 │
├──────────────────────────────┼─────────────────────────────────────────┤
│ • Public Listed: 25%         │ • High Density (>10 sources): 30%       │
│ • Private Verified: 35%      │ • Medium Density (3–10 sources): 50%    │
│ • Startup / Low Footprint: 25%│ • Low Density (<3 sources): 20%         │
│ • Flagged / High-Risk: 15%   │                                         │
└──────────────────────────────┴─────────────────────────────────────────┘
```
*Note: Sampling quotas reflect intentional benchmark stratification parameters to ensure test coverage across difficult scenarios, not global empirical corporate population proportions.*

### 2.2 Selection & Filtering Workflow
1. **Sampling Frame Identification**: Candidate entity identifiers are collected from official business registries (e.g., SEC EDGAR, Ministry of Corporate Affairs, UK Companies House) and public business directories.
2. **Deduplication**: Domain normalization (stripping `www.`, subdomains, protocols) and CIK/CIN registration matching to eliminate duplicate entity profiles.
3. **Temporal Cutoff Enforcement**: All evidence documents and web pages must be anchored to publication dates on or before **September 25, 2026**.
4. **Handling Ambiguous & Disappearing Entities**:
   - Entities lacking domain references or official registration numbers are excluded to avoid identity ambiguity.
   - Entities whose public evidence sources become unavailable or deleted during data collection are retained if archived snapshots exist; otherwise, they are logged as `UNAVAILABLE_SOURCE` and excluded from the active sample.

---

## 3. Source Provenance Requirements

Every real-world evidence record added to `VISHLESHAN-EVAL-v1` must maintain complete, immutable provenance metadata.

### 3.1 Provenance Metadata Schema
Every evidence claim must include:
- `evaluation_company_id`: Canonical company reference string.
- `source_url`: Full canonical URL of source document.
- `source_title`: Title of webpage, article, or document.
- `source_type`: One of `OFFICIAL_REGISTRY`, `OFFICIAL_WEBSITE`, `SECONDARY_NEWS`, `FINANCIAL_FILING`, `RECRUITMENT_POSTING`, `THIRD_PARTY_DIRECTORY`.
- `publication_date`: ISO 8601 date string (if available).
- `retrieval_timestamp`: ISO 8601 timestamp of data acquisition.
- `evidence_text`: Direct verbatim text snippet supporting the claim.
- `publisher_authority`: Authority rating (`HIGH`, `MEDIUM`, `LOW`).

### 3.2 Source Ground-Truth Policy
- **Official vs. Third-Party Sources**: Official company websites and filings are primary sources for identity attributes, but MUST NOT be automatically accepted as ground truth for dispute or fraud assertions.
- **Independent Verification**: Claims regarding regulatory compliance or legal status require cross-referencing against primary government registries.
- **Absence of Evidence**: Inability to find public evidence yields **`UNABLE_TO_VERIFY`**, which MUST NEVER be assigned as a negative legitimacy penalty or fraud score.

---

## 4. Task-to-Schema Annotation Mapping

Evaluation data records are mapped directly to the Pydantic schemas established in Phase 6A ([evaluation_dataset.py](file:///c:/Users/arpan/Desktop/VISHLESHAN%20AI/backend/app/schemas/evaluation_dataset.py)):

| Task | Capability Area | Ground-Truth Labels & Schema | Ground-Truth Constraints |
| :--- | :--- | :--- | :--- |
| **Task A** | **Identity Resolution** | Schema: `EvaluationCompanyRecord`<br>Labels: `CORRECT_ENTITY`, `INCORRECT_ENTITY`, `AMBIGUOUS` | Matches raw query string to canonical `evaluation_company_id`. |
| **Task B** | **Evidence Verification** | Schema: `GroundTruthClaim`<br>Labels: `VERIFIED`, `PARTIALLY_VERIFIED`, `UNABLE_TO_VERIFY`, `CONFLICTING` | Enforces explicit definition: `UNABLE_TO_VERIFY != FRAUD`. |
| **Task C** | **Conflict Detection** | Schema: `ConflictEvalPair`<br>Labels: `ENTAILMENT`, `CONTRADICTION`, `NEUTRAL` | Evaluates normalized claim subject-predicate pairs. |
| **Task D** | **Trust Engine Behavior** | Schema: `TrustBehaviorScenario`<br>Labels: Exact dimension score & penalty behavior | **BEHAVIORAL SPECIFICATION ONLY**. Subjective "true trust scores" are strictly prohibited. |
| **Task E** | **RAG Evidence Grounding** | Schema: `RAGEvalQuery`<br>Labels: `expected_answer`, `required_evidence_ids` | Requires expert human-annotated answers and document citations. |
| **Task F** | **Recruitment Scam ML** | Schema: `RecruitmentEvalReference`<br>Labels: `0 (Legitimate)`, `1 (Fraudulent)` | References frozen Phase 5A EMSCAD dataset split without raw CSV duplication. |
| **Task G** | **NLI Domains** | Schema: `ConflictEvalPair`<br>Labels: `ENTAILMENT`, `CONTRADICTION`, `NEUTRAL` | Distinguishes generic MultiNLI validation from corporate-domain NLI validation. |

---

## 5. Human Annotator Workflow & Double-Blind Protocol

Human annotation follows a 7-step double-blind workflow to ensure objectivity and auditability:

```
Step 1: Raw Record Extraction (Machine-Assisted Preprocessing)
   │
   ▼
Step 2: Assign Anonymized Annotator IDs (e.g., Annotator A-01, A-02)
   │
   ▼
Step 3: Independent Double-Blind Annotation (Annotators work in isolation)
   │
   ▼
Step 4: Disagreement Detection (Automated comparison of labels)
   │
 ├─────────── Agreement Rate >= Threshold? ──────────┐
 │ YES                                                │ NO
 ▼                                                    ▼
Step 5: Direct Label Assignment            Step 6: Lead Adjudication Review
 │                                                    │
 └──────────────────────┬─────────────────────────────┘
                        │
                        ▼
           Step 7: Immutable Audit Trail Logging
```

### 5.1 Preprocessing vs. Human Decision Separation
- **Machine-Assisted Preprocessing**: Automated tools may be used to extract raw text snippets, normalize HTML, and clean boilerplate.
- **Human Ground-Truth Decision**: All final label assignments (`VERIFIED`, `CONTRADICTION`, etc.) MUST be made independently by human annotators. LLMs or automated tools are strictly prohibited from generating ground-truth labels.

### 5.2 Anonymization & Audit Trail
- Annotator identities are recorded using anonymized IDs (e.g., `ANN-8041`, `ANN-3912`) to preserve privacy and prevent bias.
- Every label entry records `annotation_timestamp`, `annotator_id`, `annotation_method` (`DOUBLE_BLIND_HUMAN`), and `adjudication_notes` (if adjudicated).

---

## 6. Inter-Annotator Agreement Methodology

Inter-annotator agreement is quantified using standard statistical reliability metrics:

1. **Two-Annotator Agreement (Cohen's Kappa $\kappa$)**:
   $$\kappa = \frac{P_o - P_e}{1 - P_e}$$
   where $P_o$ is relative observed agreement and $P_e$ is hypothetical chance agreement probability.
   - *Target Quality Threshold*: $\kappa \ge 0.75$ (Substantial Agreement).

2. **Multi-Annotator Agreement (Fleiss' Kappa)**:
   Applied when $>2$ annotators evaluate RAG answer correctness or identity ambiguity.

3. **Per-Class Agreement Reporting**:
   Agreement rates are reported separately for each category (`VERIFIED`, `CONTRADICTION`, etc.) to detect specific class confusion.

---

## 7. Automated Data Quality Controls

Before freezing any evaluation dataset version, automated quality validation must execute cleanly via [dataset_loader.py](file:///c:/Users/arpan/Desktop/VISHLESHAN%20AI/backend/app/evaluation/dataset_loader.py):

- **Unique Identifier Check**: Rejects duplicate `claim_id`, `pair_id`, or `question_id`.
- **Orphan Reference Check**: Rejects claims referencing unknown `evaluation_company_id`.
- **URL & Timestamp Validation**: Validates RFC 3986 URL syntax and ISO 8601 timestamp formats.
- **Synthetic & Model Label Leak Prevention**:
  - Rejects records containing `is_synthetic=True` from real-world evaluation statistics.
  - Rejects records where `annotation_method` indicates model or LLM generation.
- **Label Boundary Enforcement**: Enforces strict enum limits for all categorical labels.

---

## 8. Dataset Lifecycle & Version Freezing Protocol

```
[Draft Data] ──► [Annotation] ──► [Quality Audit] ──► [Adjudication] ──► [Dataset Freeze] ──► [Canonical JSON Hash]
```

1. **Draft Stage**: Data acquired and preprocessed.
2. **Annotation Stage**: Double-blind human annotation in progress.
3. **Quality Audit**: Inter-annotator agreement metrics computed and automated schema checks executed.
4. **Adjudication**: Disagreements resolved by lead domain expert.
5. **Dataset Freeze**: Dataset status set to `FROZEN_FOR_BENCHMARK`.
6. **Canonical Hashing**: Deterministic SHA-256 hash computed over canonical JSON (`sort_keys=True`, `separators=(",", ":")`).
7. **Benchmark Execution**: Benchmark trials may be launched ONLY after hash verification.

---

## 9. Sample Size Rationale & Planned Targets

- **Planned Benchmark Target**: $N \ge 300$ real-world records per task.
- **Statistical Validity Notice**:
  > *"The planned target of $N \ge 300$ is a benchmark design target and does not by itself establish statistical validity. Final usable sample sizes depend strictly on eligible entity counts, source availability, annotation completion, quality filtering, and class distribution."*

---

## 10. Execution Statement

> *"Phase 6B benchmark execution is pending acquisition/annotation of a suitable evaluation sample."*

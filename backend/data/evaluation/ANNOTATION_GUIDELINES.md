# Vishleshan AI v2 — Ground-Truth Annotation Guidelines
## Dataset Version: `VISHLESHAN-EVAL-v1`

### 1. Purpose & Principles

This document establishes the official annotation policy for building real-world ground-truth evaluation datasets for Vishleshan AI v2.

> [!IMPORTANT]
> **Core Annotation Rules**:
> 1. **Model Predictions Are NOT Ground Truth**: Under no circumstances should LLM outputs, Trust Index scores, or automated agent predictions be accepted as ground truth without human verification against first-party/official source evidence.
> 2. **Absence of Evidence Is NOT Fraud**: Missing public evidence yields `UNABLE_TO_VERIFY`, NEVER "fraudulent" or `CONFLICTING`.
> 3. **Traceable Provenance Mandatory**: Every ground-truth claim must record explicit source URL, source title, and source category (`first_party`, `government_regulatory`, `authoritative`, `reputable_secondary`, `other`).
> 4. **Anonymized Annotator Identifiers**: Annotators are identified using anonymized codes (e.g., `ANNOTATOR_001`, `ANNOTATOR_002`). No personal PII (names, emails, phone numbers) is recorded.

---

### 2. Verification Status Label Definitions (`GroundTruthClaim`)

- **`VERIFIED`**:
  - The claim is explicitly confirmed by official government filings, regulatory registries, or primary corporate domain records.
  - *Example*: Company registration number matching state corporate registry database.
- **`PARTIALLY_VERIFIED`**:
  - The claim is supported by reputable secondary sources or partial official evidence, but full primary verification is incomplete.
  - *Example*: News reports from major media outlets citing company operations without direct registry access.
- **`UNABLE_TO_VERIFY`**:
  - No authoritative public evidence is available to confirm or refute the claim.
  - *Rule*: Default label when evidence is missing. Must never be labeled fraudulent.
- **`CONFLICTING`**:
  - Direct evidence items from recognized sources present contradictory facts regarding the same attribute.
  - *Example*: Official incorporation filing stating 2015 vs company press release stating 2022.

---

### 3. NLI Conflict Label Definitions (`ConflictEvalPair`)

- **`ENTAILMENT`**: Premise evidence text guarantees or directly supports the hypothesis claim.
- **`CONTRADICTION`**: Premise evidence text directly contradicts or invalidates the hypothesis claim.
- **`NEUTRAL`**: Premise evidence text neither proves nor disproves the hypothesis claim.

> [!CAUTION]
> **`UNABLE_TO_VERIFY != CONTRADICTION`**: Unverifiable claims lack evidence and are NOT contradiction pairs. Contradiction requires two active claims asserting mutually exclusive facts.

---

### 4. Trust Engine Behavioral Evaluation Scenarios (`trust_eval.json`)

`trust_eval.json` evaluates deterministic **Trust Engine behavioral rules**:
- **Identity Dimension**: Verified identity evidence must produce `score >= 85.0` and status `VERIFIED`.
- **Missing Evidence Handling**: Zero regulatory filings must produce `UNABLE_TO_VERIFY` with reduced confidence, NOT a company legitimacy penalty.
- **Conflict Handling**: Multiple conflicting claims must trigger `MINOR_CONFLICT` or `MAJOR_CONFLICT` and reduce final confidence score via `confidence_penalty`.
- **Determinism**: Identical evidence inputs must yield identical Trust Index score outputs.

---

### 5. Synthetic vs Real-World Data Isolation

- **Real Evaluation Records**: Sourced from actual verified corporate intelligence and marked with `is_synthetic: false`. Included in official benchmark evaluation statistics.
- **Synthetic Unit-Test Records**: Created for software testing and marked explicitly with `is_synthetic: true`. **Must be excluded from real-world evaluation statistics.**

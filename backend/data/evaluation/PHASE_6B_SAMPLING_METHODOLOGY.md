# Vishleshan AI v2 — Phase 6B Sampling Methodology

**Document Version**: `1.0.0`  
**Dataset Reference**: `VISHLESHAN-EVAL-v1`  
**Evaluation Status**: `PHASE 6B: DESIGN COMPLETE`  
**Release Date**: September 25, 2026  
**Random Seed**: `42`  

---

## 1. Executive Summary & Design Rationale

This document defines the official sampling strategy for constructing evaluation datasets under the Phase 6B benchmark protocol. To guarantee scientific integrity, avoid selection bias, and prevent data leakage, evaluation samples must be drawn systematically from defined target populations using stratified probability sampling rather than convenience sampling or artificial data generation.

> [!IMPORTANT]
> **Real-World Sampling Execution Statement**:
> *"Phase 6B benchmark execution is pending acquisition/annotation of a suitable evaluation sample."*
>
> **Strict Prohibition**: Synthetic data, template objects, or unvalidated model predictions MUST NEVER be presented as real-world evaluation samples.

---

## 2. Target Population & Sampling Unit

### Target Population
The target population consists of active global commercial and corporate entities operating across diverse industry sectors (Technology, Financial Services, E-Commerce, Healthcare, Professional Services, and Logistics) with verifiable public business footprints.

### Sampling Unit
The primary sampling unit is a **Canonical Corporate Entity Record** comprising:
1. Legal Entity Metadata (Legal Name, Trade Names, Registration ID / CIK, Jurisdiction, Domain).
2. Evidence Claim Set (Incorporation year, physical address, leadership, regulatory status, domain registration).
3. Associated Document Corpus (Official registry filings, news articles, website pages, job postings).

---

## 3. Stratification Variables & Sample Size Rationale

### Stratification Framework
To ensure robust representation across diverse corporate profiles, sampling is stratified across three key dimensions:

```
                          ┌─────────────────────────────────────────┐
                          │     Corporate Target Population         │
                          └────────────────────┬────────────────────┘
                                               │
               ┌───────────────────────────────┼───────────────────────────────┐
               ▼                               ▼                               ▼
     [Entity Type Tier]               [Evidence Density]               [Risk Profile]
┌───────────────────────────┐    ┌───────────────────────────┐    ┌───────────────────────────┐
│ 1. Public Listed (25%)    │    │ 1. High (>10 sources)     │    │ 1. Low Risk / Normal      │
│ 2. Private Verified (35%) │    │ 2. Medium (3–10 sources)  │    │ 2. Medium Risk            │
│ 3. Early-Stage / Low (25%)│    │ 3. Low (<3 sources)       │    │ 3. High Risk / Flagged    │
│ 4. Flagged / Scam (15%)   │    └───────────────────────────┘    └───────────────────────────┘
└───────────────────────────┘
```

1. **Entity Type Tier**:
   - **Publicly Listed Companies (25%)**: High transparency, extensive filings (SEC 10-K, MCA).
   - **Established Private Companies (35%)**: Moderate transparency, commercial registry records.
   - **Early-Stage / Low-Footprint Entities (25%)**: Minimal public footprint, recently registered domains.
   - **High-Risk / Scam-Flagged Entities (15%)**: Known or suspected fraudulent entities, unregistered job posters.

2. **Evidence Density**:
   - **High Density (>10 sources)**: Well-documented entities with redundant news and registry data.
   - **Medium Density (3–10 sources)**: Standard commercial footprint.
   - **Low Density (<3 sources)**: Sparse public evidence requiring `UNABLE_TO_VERIFY` classification.

3. **Geographic Jurisdiction**:
   - Primary: North America, India, EU/UK, Asia-Pacific.

### Sample Size Rationale
Statistical power calculations dictate sample size requirements to achieve 95% confidence intervals with a margin of error $E \le \pm 0.05$ on Macro F1:
- Minimum required sample size per task: $N \ge 300$ independent real-world entity records (or claim pairs).
- For binary classification tasks (e.g. Task F EMSCAD), sample sizes of $N = 3,576$ (test split) provide high statistical power ($> 0.99$).

---

## 4. Inclusion & Exclusion Criteria

### Inclusion Criteria
1. Entity has a distinct legal name and at least one verifiable domain or official registration identifier.
2. At least 2 independent primary or secondary sources exist for claimed evidence attributes (except for low-density test strata).
3. All source documents were published or captured prior to the temporal cutoff.
4. Human annotation completed by at least 2 independent annotators with Inter-Annotator Agreement (Cohen's $\kappa \ge 0.75$).

### Exclusion Criteria
1. Entities with ambiguous names lacking domain or registration anchors (e.g., generic names like "Consulting LLC").
2. Entities whose evidence sources contain unresolvable copyright or privacy restrictions preventing open research archiving.
3. Records generated by LLM auto-prompting or synthetic template scripts.
4. Duplicate entity records or records with overlapping evidence snippets across evaluation tasks.

---

## 5. Deduplication & Temporal Cutoff Rules

### Deduplication Protocol
1. **Domain Normalization**: Canonicalize domains (strip `www.`, subdomains, query parameters).
2. **Registration ID Matching**: Match SEC CIK, MCA Corporate Identification Numbers (CIN), or UK Companies House numbers.
3. **Overlap Filtering**: Ensure zero overlap between training corpora used in baseline training and evaluation test sets.

### Temporal Cutoff
- **Cutoff Date**: September 25, 2026.
- All evidence documents, domain registrations, and registry filings must reflect status as of or prior to this cutoff date.

---

## 6. Handling Companies with Insufficient Public Evidence

> [!IMPORTANT]
> **Absence of Evidence Policy**:
> - If an entity or claim lacks public evidence in open registries or authoritative web sources, the ground-truth label MUST be set to **`UNABLE_TO_VERIFY`**.
> - An `UNABLE_TO_VERIFY` state MUST NEVER be penalized as a fraudulent entity or assigned a negative legitimacy score.
> - Baselines and Vishleshan AI system components are evaluated on their ability to correctly identify missing evidence without hallucinating verification or false fraud assertions.

---

## 7. Status Declaration

> *"Phase 6B benchmark execution is pending acquisition/annotation of a suitable evaluation sample."*

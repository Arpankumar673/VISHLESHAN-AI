# Vishleshan AI v2 — Phase 6D Final Statistical Consistency Audit Report

**Audited Target Artifacts**:
- `backend/data/evaluation/v2/phase6d_additions/benchmark_results.json`
- `backend/data/evaluation/PHASE_6D_TARGETED_EVALUATION_REPORT.md`
- `backend/app/evaluation/phase6d_runner.py`

---

## 1. EXECUTIVE VERDICT

> **OFFICIAL AUDIT DECISION**:
> **`PASS WITH REPORTING CORRECTIONS`**
>
> **Summary Rationale**:
> 1. **Raw Counts & Point Estimates Verified**: All raw counts ($N=10$ Task A, $N=20$ Task B, $N=24$ Task C, $N=16$ Task D, $N=12$ Task E) and point metrics (Task C $+16.67\%$ accuracy, $+0.1517$ Macro F1) are 100% mathematically correct and verified from raw predictions.
> 2. **Primary Inferential Test Rule**: For small paired binary outcomes ($N \le 24$), the exact McNemar / Binomial test is established as the **primary inferential significance test**. Paired bootstrap $p$-values are classified strictly as secondary sensitivity analysis.
> 3. **Exact $P$-Value Correction for Task C**: Recalculating the two-tailed exact binomial test on Task C ($n=6$ discordant pairs, $b=1, c=5$) yields exact $p = \mathbf{0.2188}$ (corrected from $0.1250$ due to 6-pair binomial distribution evaluation).
> 4. **Holm-Bonferroni FWER Decision**: Under primary exact McNemar testing with Holm-Bonferroni FWER control ($\alpha = 0.05$), **only Task E (RAG Grounding, $p_{adj} = 0.0024$) achieves statistical significance**. Tasks B ($p_{adj} = 0.1250$), D ($p_{adj} = 0.1250$), C ($p_{adj} = 0.4375$), and A ($p_{adj} = 1.0000$) represent observed functional improvements where statistical significance is not established.
> 5. **Reporting Language Softening**: Softened NLI model recommendations and over-generalized research claims to reflect exact statistical boundaries.

---

## 2. RAW COUNTS & ACCURACY VERIFICATION

Independent recalculation of baseline and system predictions across all expanded tasks:

| Subsystem Task | Record Count ($N$) | Ground-Truth SubSet | Baseline Correct | Vishleshan Correct | Baseline Accuracy | Vishleshan Accuracy | Verification Status |
| :--- | :---: | :--- | :---: | :---: | :---: | :---: | :--- |
| **Task A (Identity)** | $N = 10$ | `identity_eval.json` | 10 | 10 | 100.0% | **100.0%** | **VERIFIED (Match: 100%)** |
| **Task B (Evidence)** | $N = 20$ | `evidence_eval.json` | 13 | 19 | 65.00% | **95.00%** | **VERIFIED (Match: 100%)** |
| **Task C (Corporate NLI)** | $N = 24$ | `conflict_eval.json` | 6 | 10 | 25.00% | **41.67%** | **VERIFIED (Match: 100%)** |
| **Task D (Trust Engine)** | $N = 16$ | `trust_eval.json` | 10 | 16 | 62.50% | **100.0%** | **VERIFIED (Match: 100%)** |
| **Task E (RAG Grounding)** | $N = 12$ | `rag_eval.json` | 0 | 12 | 0.00% | **100.0%** | **VERIFIED (Match: 100%)** |

---

## 3. EXACT P-VALUE AUDIT (PRIMARY INFERENCE)

Exact paired testing was conducted on raw paired predictions using two-tailed binomial evaluation over discordant pair counts ($b$: baseline right & system wrong; $c$: baseline wrong & system right):

| Subsystem Task | $N$ | Baseline Correct | System Correct | Discordant $b$ | Discordant $c$ | Total Discordant $n$ | Exact $P$-value Calculation | Audited Exact $P$-value |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- | :---: |
| **Task A (Identity)** | 10 | 10 | 10 | 0 | 0 | 0 | $1.0000$ (No discordant pairs) | **$1.0000$** |
| **Task B (Evidence)** | 20 | 13 | 19 | 0 | 6 | 6 | $2 \times (0.5)^6 = 2 \times 0.015625$ | **$0.0312$** |
| **Task C (Corporate NLI)** | 24 | 6 | 10 | 1 | 5 | 6 | $2 \times \sum_{k=0}^{1} \binom{6}{k} (0.5)^6 = 14 / 64$ | **$0.2188$** (Corrected from 0.125) |
| **Task D (Trust Engine)** | 16 | 10 | 16 | 0 | 6 | 6 | $2 \times (0.5)^6 = 2 \times 0.015625$ | **$0.0312$** |
| **Task E (RAG Grounding)** | 12 | 0 | 12 | 0 | 12 | 12 | $2 \times (0.5)^{12} = 2 \times 0.00024414$ | **$0.0005$** |

---

## 4. HOLM-BONFERRONI MULTIPLE COMPARISON AUDIT

To control Family-Wise Error Rate (FWER) at $\alpha = 0.05$, the **Holm-Bonferroni step-down procedure** was executed over the complete set of audited exact $p$-values across Tasks A–E ($m = 5$ tests):

### Holm-Bonferroni Step-by-Step Analysis:

1. **Rank 1 — Task E (RAG Grounding)**:
   - Raw Exact $P$-value: $p_{(1)} = \mathbf{0.0005}$
   - Adjusted Alpha Threshold: $\alpha_{adj, 1} = 0.05 / (5 - 1 + 1) = \mathbf{0.0100}$
   - Adjusted $P$-value: $p_{adj} = \min(1.0, 5 \times 0.000488) = \mathbf{0.0024}$
   - **Decision**: $p_{adj} = 0.0024 \le 0.05 \implies$ **REJECT $H_0$ (STATISTICALLY SIGNIFICANT)**

2. **Rank 2 — Task B (Evidence Verification)**:
   - Raw Exact $P$-value: $p_{(2)} = \mathbf{0.03125}$
   - Adjusted Alpha Threshold: $\alpha_{adj, 2} = 0.05 / (5 - 2 + 1) = \mathbf{0.0125}$
   - Adjusted $P$-value: $p_{adj} = \min(1.0, \max(0.0024, 4 \times 0.03125)) = \mathbf{0.1250}$
   - **Decision**: $p_{adj} = 0.1250 > 0.05 \implies$ **DO NOT REJECT $H_0$ (NOT SIGNIFICANT)**

3. **Rank 3 — Task D (Trust Engine)**:
   - Raw Exact $P$-value: $p_{(3)} = \mathbf{0.03125}$
   - Adjusted Alpha Threshold: $\alpha_{adj, 3} = 0.05 / (5 - 3 + 1) = \mathbf{0.0167}$
   - Adjusted $P$-value: $p_{adj} = \min(1.0, \max(0.1250, 3 \times 0.03125)) = \mathbf{0.1250}$
   - **Decision**: $p_{adj} = 0.1250 > 0.05 \implies$ **DO NOT REJECT $H_0$ (NOT SIGNIFICANT)**

4. **Rank 4 — Task C (Corporate NLI)**:
   - Raw Exact $P$-value: $p_{(4)} = \mathbf{0.21875}$
   - Adjusted Alpha Threshold: $\alpha_{adj, 4} = 0.05 / (5 - 4 + 1) = \mathbf{0.0250}$
   - Adjusted $P$-value: $p_{adj} = \min(1.0, \max(0.1250, 2 \times 0.21875)) = \mathbf{0.4375}$
   - **Decision**: $p_{adj} = 0.4375 > 0.05 \implies$ **DO NOT REJECT $H_0$ (NOT SIGNIFICANT)**

5. **Rank 5 — Task A (Identity Resolution)**:
   - Raw Exact $P$-value: $p_{(5)} = \mathbf{1.0000}$
   - Adjusted Alpha Threshold: $\alpha_{adj, 5} = 0.05 / (5 - 5 + 1) = \mathbf{0.0500}$
   - Adjusted $P$-value: $p_{adj} = \mathbf{1.0000}$
   - **Decision**: $p_{adj} = 1.0000 > 0.05 \implies$ **DO NOT REJECT $H_0$ (NOT SIGNIFICANT)**

> [!CRITICAL]
> **Primary Inferential Audit Finding**: Under primary exact McNemar testing with Holm-Bonferroni FWER control, **only Task E (RAG Grounding) achieves statistical significance ($p_{adj} = 0.0024$)**. Tasks B, C, and D demonstrate clear observed functional improvements, but do not achieve FWER-adjusted statistical significance at $\alpha = 0.05$.

---

## 5. SENSITIVITY ANALYSIS: PAIRED BOOTSTRAP AUDIT

The non-parametric paired bootstrap test ($B=1,000$, seed `42`, 95% percentile CI) is audited as a **sensitivity analysis**:

| Subsystem Task | $N$ | Vishleshan Accuracy | 95% Bootstrap CI | Paired Bootstrap $p$-value | Bootstrap Holm-Bonferroni $p_{adj}$ | Sensitivity Finding |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **Task A (Identity)** | 10 | 100.0% | `[1.0000, 1.0000]` | $1.0000$ | $1.0000$ | Consistent with exact test (N.S.) |
| **Task B (Evidence)** | 20 | 95.00% | `[0.8500, 1.0000]` | $0.0010$ | **$0.0040$** | Significant under bootstrap resampling |
| **Task C (Corporate NLI)** | 24 | 41.67% | `[0.2083, 0.6250]` | $0.0120$ | **$0.0120$** | Significant under bootstrap resampling |
| **Task D (Trust Engine)** | 16 | 100.0% | `[1.0000, 1.0000]` | $0.0010$ | **$0.0040$** | Significant under bootstrap resampling |
| **Task E (RAG Grounding)** | 12 | 100.0% | `[1.0000, 1.0000]` | $0.0010$ | **$0.0040$** | Significant under bootstrap resampling |

> [!NOTE]
> **Methodological Separation Rule**: Bootstrap $p$-values are reported strictly as secondary sensitivity analysis. Primary inferential claims are governed exclusively by exact McNemar testing.

---

## 6. TASK C SPECIFIC AUDIT — CORPORATE CONFLICT NLI

- **Baseline Metrics**: Accuracy = **25.00%** (6/24), Macro F1 = **0.2372**.
- **Vishleshan System Metrics**: Accuracy = **41.67%** (10/24), Macro F1 = **0.3889**.
- **Point Metric Changes**:
  - Accuracy Change: **$+16.67\%$** ($25.00\% \longrightarrow 41.67\%$).
  - Macro F1 Change: **$+0.1517$** ($0.2372 \longrightarrow 0.3889$).
- **Statistical Significance**: Exact $p = 0.2188 > 0.05$. Statistical significance is **NOT claimed**.
- **Diagnostic Finding**: The system demonstrated functional gains on explicit numerical/status contradictions (detecting Wirecard, Theranos, Enron, and Luckin Coffee fraud), but misclassified 8/11 implicit entailments as `NEUTRAL`.

---

## 7. TASK E SPECIFIC AUDIT — RAG EVIDENCE GROUNDING

- **Operational Grounding Definition**: Response generated strictly from retrieved evidence documents with valid `Citation` schema metadata (`evidence_id`, `source_url`, `similarity`).
- **Audit Verification**: All 12 system queries in `rag_eval.json` satisfied the ground-truth answer and citation metadata requirements (Grounding Rate = 100.0%, Recall@1 = 100.0%).
- **Baseline Verification**: Un-grounded keyword retrieval generated 0/12 valid citations (Grounding Rate = 0.00%).
- **Generalization Caveat**: Achieving 100% grounding on $N=12$ test queries validates functional RAG pipeline correctness, but does NOT constitute proof of universal RAG immunity to hallucinations on unconstrained domain queries.

---

## 8. REQUIRED REPORTING CORRECTIONS

1. **Softened NLI Model Recommendation**:
   - *Replace*: Statement saying deploying `cross-encoder/nli-deberta-v3-xsmall` is "required" based on this benchmark.
   - *With*: **"The observed failure mode motivates a future experiment comparing the current NLI implementation against a pretrained semantic NLI model."**
2. **Corrected Research Claims**:
   - *Permitted Statement*: **"Phase 6D demonstrates observed functional improvements on Tasks B, C, D, and E."**
   - *Prohibited Statement*: "Vishleshan is statistically superior across Tasks B-E."
3. **Primary Significance Table**:
   - Display exact McNemar $p$-values and Holm-Bonferroni adjusted $p$-values as the primary inferential standard in report tables.

---

## 9. FINAL RECOMMENDATION

1. **Accept Audit Verdict**: **`PASS WITH REPORTING CORRECTIONS`**.
2. **Preserve Benchmark Artifacts**: Leave `benchmark_results.json` and ground-truth files 100% untouched.
3. **Update Report Documentation**: Align research narrative in `PHASE_6D_TARGETED_EVALUATION_REPORT.md` with the primary exact inferential audit.

---
**Official Audit Sign-Off**:
`PHASE 6D FINAL STATISTICAL CONSISTENCY AUDIT COMPLETE — VERDICT: PASS WITH REPORTING CORRECTIONS`

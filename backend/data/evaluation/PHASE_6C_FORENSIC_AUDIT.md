# Vishleshan AI v2 — Phase 6C Forensic Benchmark Audit Report

**Audited Target Documents**:
- `backend/data/evaluation/v2/benchmark_results.json`
- `backend/data/evaluation/PHASE_6C_BENCHMARK_REPORT.md`
- `backend/app/evaluation/benchmark_runner.py`

---

## 1. EXECUTIVE VERDICT

> **OFFICIAL AUDIT DECISION**:
> **`PASS WITH REPORTING CORRECTIONS`**
>
> **Summary Rationale**:
> 1. **Dataset & Model Code Integrity**: Zero dataset files (`VISHLESHAN-EVAL-v2`), Phase 4 Trust Engine, Phase 5A Recruitment ML, or Phase 5B NLI code were modified. Pre-flight SHA-256 hash verification matched `8bd44b481a7211a1f54e8461f6678933de6a26390b5c726b24e97e4ec2a4c3c3` (`True`).
> 2. **Reproducibility Verification**: All reported metrics in `benchmark_results.json` are 100% mathematically reproducible from `benchmark_runner.py` using random seed `42` and 1,000 bootstrap resamples.
> 3. **Methodological & Reporting Corrections Required**:
>    - **Small Sample Size Limitations**: Sample sizes across tasks ($N=6$ for Task A, $N=8$ for Task B, $N=4$ for Task C, $N=4$ for Task D, $N=3$ for Task E) are too small to justify claims of universal generalization or statistical power.
>    - **Bootstrap Degeneracy on Small N**: Non-parametric bootstrap CIs on 100% accuracy data ($N=8$, $N=4$, $N=3$) yield zero-width intervals `[1.0000, 1.0000]`. These reflect sample-level constancy, NOT zero population uncertainty.
>    - **Exact Paired Testing vs. Bootstrap**: For small $N$, paired bootstrap difference tests underestimate $p$-values due to discrete resampling artifacts. Exact McNemar / exact binomial tests show $p_{exact} \ge 0.2500$ for all tasks, indicating that observed differences do not achieve statistical significance at $\alpha = 0.05$.
>    - **Multiple Comparisons**: Applying Holm-Bonferroni correction across the 5 hypothesis tests renders Task B bootstrap $p = 0.0210$ non-significant (adjusted $\alpha = 0.0125$).
>    - **Overstated Research Claims**: Phrases asserting "statistically significant superiority", "research validated", or calling $p = 0.0680$ "marginally significant" must be toned down to reflect preliminary evaluation constraints.

---

## 2. DATASET / SAMPLE-SIZE AUDIT

The frozen benchmark dataset `VISHLESHAN-EVAL-v2` contains 28 real corporate entities mapped across 4 sampling strata. However, the ground-truth evaluation subsets present small sample sizes per task:

| Subsystem Task | Record Count ($N$) | Ground-Truth SubSet | Strata Coverage | Sample Size Assessment |
| :--- | :---: | :--- | :---: | :--- |
| **Task A (Identity Resolution)** | $N = 6$ | `identity_eval.json` | Strata 1 & 4 | **Small Sample** ($N=6$) — High variance in point estimates. |
| **Task B (Evidence Verification)** | $N = 8$ | `evidence_eval.json` | Strata 1, 2, 3, 4 | **Small Sample** ($N=8$) — 100% system score yields degenerate CI. |
| **Task C (Corporate NLI)** | $N = 4$ | `conflict_eval.json` | Strata 1, 4 | **Small Sample** ($N=4$) — High class imbalance. |
| **Task D (Trust Engine)** | $N = 4$ | `trust_eval.json` | Strata 1, 3, 4 | **Small Sample** ($N=4$) — Behavioral spec scenarios. |
| **Task E (RAG Grounding)** | $N = 3$ | `rag_eval.json` | Strata 1, 4 | **Tiny Sample** ($N=3$) — Functional sanity check only. |
| **Task F (Phase 5A Scam ML)** | $N = 3,584$ | EMSCAD Test Split | External Benchmark | **Adequate Sample Size** (Frozen reference). |

---

## 3. TASK A AUDIT — IDENTITY RESOLUTION

- **Sample Size ($N$)**: 6 queries.
- **Ground-Truth Class Distribution**: `VERIFIED`: 6, `UNABLE_TO_VERIFY`: 0, `SUSPICIOUS`: 0, `CONFLICTING`: 0.
- **Baseline Predictions**: 6 `VERIFIED` (Accuracy = 6/6 = **100.0%**).
- **Vishleshan System Predictions**: 5 `VERIFIED`, 1 `UNABLE_TO_VERIFY` (Accuracy = 5/6 = **83.33%**).
- **Confusion Matrix (Vishleshan System)**:
  ```json
  {
    "VERIFIED": { "VERIFIED": 5, "UNABLE_TO_VERIFY": 1, "SUSPICIOUS": 0, "CONFLICTING": 0 },
    "UNABLE_TO_VERIFY": { "VERIFIED": 0, "UNABLE_TO_VERIFY": 0, "SUSPICIOUS": 0, "CONFLICTING": 0 }
  }
  ```
- **Metrics**: Accuracy = **83.33%**, Macro Precision = **0.5000**, Macro Recall = **0.4167**, Macro F1 = **0.4545**, Weighted F1 = **0.9091**.
- **Bootstrap 95% CI**: Accuracy `[0.5000, 1.0000]`, Macro F1 `[0.3333, 1.0000]`.
- **Hypothesis Test & $p$-value**: Paired bootstrap $p = 1.0000$. Exact McNemar $p = 1.0000$.
- **Audit Findings**:
  1. $5/6 = 83.33\%$ is mathematically verified.
  2. The single Vishleshan error occurred on claim `"Wirecard insolvency Munich"` because strict anchor resolution required an explicit HRB/CIK identifier in the text.
  3. Small sample size ($N=6$) results in a wide confidence interval (`[50.0%, 100.0%]`). This result is preliminary and lacks statistical power.

---

## 4. TASK B AUDIT — EVIDENCE VERIFICATION

- **Sample Size ($N$)**: 8 claims.
- **Ground-Truth Class Distribution**: `VERIFIED`: 4, `PARTIALLY_VERIFIED`: 1, `UNABLE_TO_VERIFY`: 2, `CONFLICTING`: 1.
- **Baseline Predictions**: `VERIFIED`: 5 (4 true VERIFIED + 1 false CONFLICTING), `PARTIALLY_VERIFIED`: 3 (1 true PARTIALLY_VERIFIED + 2 false UNABLE_TO_VERIFY). Accuracy = 5/8 = **62.50%**.
- **Vishleshan System Predictions**: `VERIFIED`: 4, `PARTIALLY_VERIFIED`: 1, `UNABLE_TO_VERIFY`: 2, `CONFLICTING`: 1. Accuracy = 8/8 = **100.0%**.
- **Confusion Matrix (Vishleshan System)**:
  ```json
  {
    "VERIFIED": { "VERIFIED": 4, "PARTIALLY_VERIFIED": 0, "UNABLE_TO_VERIFY": 0, "CONFLICTING": 0 },
    "PARTIALLY_VERIFIED": { "VERIFIED": 0, "PARTIALLY_VERIFIED": 1, "UNABLE_TO_VERIFY": 0, "CONFLICTING": 0 },
    "UNABLE_TO_VERIFY": { "VERIFIED": 0, "PARTIALLY_VERIFIED": 0, "UNABLE_TO_VERIFY": 2, "CONFLICTING": 0 },
    "CONFLICTING": { "VERIFIED": 0, "PARTIALLY_VERIFIED": 0, "UNABLE_TO_VERIFY": 0, "CONFLICTING": 1 }
  }
  ```
- **Metrics**: Accuracy = **100.0%**, Macro P/R/F1 = **1.0000**, Weighted P/R/F1 = **1.0000**.
- **Bootstrap 95% CI**: Baseline Accuracy `[0.2500, 0.8750]`, System Accuracy `[1.0000, 1.0000]`.
- **Hypothesis Test & $p$-value**:
  - Implemented Paired Bootstrap $p$-value = **$0.0210$**.
  - Independent Exact McNemar / Binomial Test ($B=3, C=0$ discordant pairs): $p_{exact} = 2 \times (0.5)^3 = \mathbf{0.2500}$.
- **Audit Findings**:
  1. The bootstrap CI `[1.0000, 1.0000]` is mathematically correct for non-parametric resampling on constant $100\%$ accuracy data, BUT represents a **degenerate zero-width interval** caused by sample-level constancy. It does NOT prove zero uncertainty in the general population.
  2. For $N=8$ with 3 discordant pairs, exact McNemar testing yields $p_{exact} = 0.2500$, which is **NOT statistically significant at $\alpha = 0.05$**. Resampling $N=8$ with replacement underestimates pair variance.

---

## 5. TASK C AUDIT — CONFLICT DETECTION / CORPORATE NLI

- **Sample Size ($N$)**: 4 claim pairs.
- **Ground-Truth Class Distribution**: `ENTAILMENT`: 1, `CONTRADICTION`: 2, `NEUTRAL`: 1.
- **Baseline Predictions**: `ENTAILMENT`: 0, `CONTRADICTION`: 1, `NEUTRAL`: 3. Accuracy = 2/4 = **50.00%**.
- **Vishleshan NLI Predictions**: `ENTAILMENT`: 0, `CONTRADICTION`: 1, `NEUTRAL`: 3. Accuracy = 2/4 = **50.00%**.
- **Confusion Matrix (Both Systems)**:
  ```json
  {
    "ENTAILMENT": { "ENTAILMENT": 0, "CONTRADICTION": 0, "NEUTRAL": 1 },
    "CONTRADICTION": { "ENTAILMENT": 0, "CONTRADICTION": 1, "NEUTRAL": 1 },
    "NEUTRAL": { "ENTAILMENT": 0, "CONTRADICTION": 0, "NEUTRAL": 1 }
  }
  ```
- **Metrics**: Accuracy = **50.00%**, Macro Precision = **0.4444**, Macro Recall = **0.5000**, Macro F1 = **0.3889**, Weighted F1 = **0.4583**.
- **Bootstrap 95% CI**: Accuracy `[0.0000, 1.0000]`, Macro F1 `[0.0000, 1.0000]`.
- **Hypothesis Test & $p$-value**: Paired bootstrap $p = 1.0000$. Exact McNemar $p = 1.0000$.
- **Audit Findings**:
  1. Baseline and Vishleshan NLI generated **100% identical prediction vectors**.
  2. The Vishleshan NLI engine provided **0.00% empirical improvement** over the surface lexical baseline on corporate evidence pairs.
  3. The fallback engineered-feature NLI model failed on implicit corporate legal entailment (predicting `NEUTRAL` instead of `ENTAILMENT` due to low token overlap $< 0.55$).
  4. The corporate NLI benchmark provides **no evidence of system superiority**.

---

## 6. TASK D AUDIT — TRUST ENGINE BEHAVIORAL CORRECTNESS

- **Sample Size ($N$)**: 4 behavioral scenarios.
- **Ground-Truth Class Distribution**: `VERIFIED`: 1, `UNABLE_TO_VERIFY`: 1, `CONFLICTING`: 2.
- **Baseline Predictions**: `VERIFIED`: 1, `UNABLE_TO_VERIFY`: 3. Accuracy = 2/4 = **50.00%**.
- **Vishleshan System Predictions**: `VERIFIED`: 1, `UNABLE_TO_VERIFY`: 1, `CONFLICTING`: 2. Accuracy = 4/4 = **100.0%**.
- **Confusion Matrix (Vishleshan System)**:
  ```json
  {
    "VERIFIED": { "VERIFIED": 1, "UNABLE_TO_VERIFY": 0, "SUSPICIOUS": 0, "CONFLICTING": 0 },
    "UNABLE_TO_VERIFY": { "VERIFIED": 0, "UNABLE_TO_VERIFY": 1, "SUSPICIOUS": 0, "CONFLICTING": 0 },
    "SUSPICIOUS": { "VERIFIED": 0, "UNABLE_TO_VERIFY": 0, "SUSPICIOUS": 0, "CONFLICTING": 0 },
    "CONFLICTING": { "VERIFIED": 0, "UNABLE_TO_VERIFY": 0, "SUSPICIOUS": 0, "CONFLICTING": 2 }
  }
  ```
- **Metrics**: Accuracy = **100.0%**, Macro P/R/F1 = **1.0000**, Weighted P/R/F1 = **1.0000**.
- **Bootstrap 95% CI**: Baseline `[0.0000, 1.0000]`, System `[1.0000, 1.0000]`.
- **Hypothesis Test & $p$-value**:
  - Implemented Paired Bootstrap $p$-value = **$0.0680$**.
  - Independent Exact McNemar / Binomial Test ($B=2, C=0$): $p_{exact} = \mathbf{0.5000}$.
- **Audit Findings**:
  1. Reported $p = 0.0680$ is **NOT statistically significant at standard $\alpha = 0.05$**.
  2. Describing $p = 0.0680$ as "marginally significant" in research literature is improper when $\alpha = 0.05$ threshold is enforced.
  3. The result confirms deterministic implementation compliance across 4 scenarios, but sample size $N=4$ precludes statistical significance claims.

---

## 7. TASK E AUDIT — RAG EVIDENCE GROUNDING

- **Sample Size ($N$)**: 3 queries in `rag_eval.json`.
- **Ground-Truth Criteria**: Factually correct corporate answer, citation linking to valid evidence ID, grounded strictly in retrieved source.
- **Baseline Predictions (Un-grounded Keyword)**: 0/3 grounded (Accuracy = **0.00%**).
- **Vishleshan RAG System Predictions**: 3/3 grounded, 3/3 correct citation IDs (Accuracy = **100.0%**).
- **Metrics**: Accuracy = **100.0%**, Grounding Rate = **1.0000**, Evidence ID Recall@1 = **1.0000**.
- **Bootstrap 95% CI**: Baseline `[0.0000, 0.0000]`, System `[1.0000, 1.0000]`.
- **Hypothesis Test & $p$-value**:
  - Implemented Paired Bootstrap $p$-value = **$0.0010$**.
  - Independent Exact Binomial Test ($B=3, C=0$): $p_{exact} = \mathbf{0.2500}$.
- **Operational Definitions in Code**:
  - **"grounding"**: Response generated exclusively from retrieved evidence snippets with valid `Citation` schema metadata (`evidence_id`, `source_url`, `similarity`).
  - **"correct answer"**: Factual concordance with SEC filings, BaFin insolvency records, or MCA master data.
  - **"unsupported claim"**: Generative output lacking verified citation metadata.
- **Audit Findings**:
  1. $0\%$ baseline vs. $100\%$ system is calculated correctly from `rag_eval.json` ground truth.
  2. Tiny sample size ($N=3$) represents a basic functional verification. It does NOT constitute proof of universal RAG superiority or immunity to hallucinations on complex domain queries.

---

## 8. TASK F AUDIT — PHASE 5A RECRUITMENT SCAM ML REFERENCE

- **Source Dataset**: EMSCAD Real-World Benchmark Reference ($N = 3,584$ test split).
- **Model Target**: `recruitment_scam_v1` (Frozen Phase 5A joblib artifact).
- **Reported Frozen Metrics**:
  - **Test PR-AUC**: `0.3481`
  - **ROC-AUC**: `0.6411`
  - **Precision**: `0.9474`
  - **Recall**: `0.1385`
  - **F1 Score**: `0.2416`
- **Audit Findings**:
  1. All 5 metrics match the frozen Phase 5A reference evaluation values exactly.
  2. No code, model weights, or dataset files were recomputed or altered.
  3. Retained documentation correction statement:
     `"NOT CALCULATED — the current evaluation interface does not expose a suitable continuous multiclass decision score for ranking-based AUC evaluation."`

---

## 9. BOOTSTRAP IMPLEMENTATION AUDIT

Code audit of `compute_bootstrap_ci` in `backend/app/evaluation/benchmark_runner.py`:

```python
def compute_bootstrap_ci(y_true, y_pred, labels, metric_key="accuracy", n_resamples=1000, ci=0.95, seed=42):
    rng = np.random.RandomState(seed)
    n = len(y_true)
    bootstrap_scores = []
    for _ in range(n_resamples):
        indices = rng.choice(n, size=n, replace=True)
        sample_true = [y_true[i] for i in indices]
        sample_pred = [y_pred[i] for i in indices]
        metrics = compute_classification_metrics(sample_true, sample_pred, labels)
        bootstrap_scores.append(metrics.get(metric_key, 0.0))
    alpha = (1.0 - ci) / 2.0
    lower = float(np.percentile(bootstrap_scores, alpha * 100))
    upper = float(np.percentile(bootstrap_scores, (1.0 - alpha) * 100))
    return (round(lower, 4), round(upper, 4))
```

### Verification Checklist:
- [x] **Resampling Unit**: Resamples evaluation examples ($i \in [0, n-1]$), preserving paired true/pred tuples.
- [x] **Paired Preservation**: Baseline and system evaluations resample identical index arrays per iteration.
- [x] **Resample Iterations**: Exactly $1,000$ resamples are executed.
- [x] **Random Seed**: `seed=42` is explicitly set via `RandomState(42)`.
- [x] **Percentile Calculation**: Uses `np.percentile(..., 2.5)` and `np.percentile(..., 97.5)`.
- [!] **Degeneracy Warning**: For datasets where $y_{true} == y_{pred}$ for all $N$ items ($N=8$ in Task B, $N=4$ in Task D, $N=3$ in Task E), every bootstrap resample has $100\%$ accuracy, producing `[1.0000, 1.0000]`. This zero-width interval must be documented as an artifact of small-sample constancy, not perfect population certainty.

---

## 10. HYPOTHESIS-TEST AUDIT

Code audit of `compute_paired_bootstrap_p_value` in `benchmark_runner.py`:

```python
def compute_paired_bootstrap_p_value(y_true, y_pred_baseline, y_pred_system, labels, metric_key="accuracy", n_resamples=1000, seed=42):
    rng = np.random.RandomState(seed)
    n = len(y_true)
    diffs = []
    for _ in range(n_resamples):
        indices = rng.choice(n, size=n, replace=True)
        s_true = [y_true[i] for i in indices]
        s_base = [y_pred_baseline[i] for i in indices]
        s_sys = [y_pred_system[i] for i in indices]
        m_base = compute_classification_metrics(s_true, s_base, labels).get(metric_key, 0.0)
        m_sys = compute_classification_metrics(s_true, s_sys, labels).get(metric_key, 0.0)
        diffs.append(m_sys - m_base)
    p_value = float(np.mean(np.array(diffs) <= 0))
    return round(max(0.001, p_value), 4)
```

### Comparison: Implemented Bootstrap Test vs. Exact McNemar Test

| Benchmark Task | $N$ | Implemented Bootstrap $p$ | Exact McNemar / Binomial $p$ | Statistically Significant ($\alpha=0.05$)? |
| :--- | :---: | :---: | :---: | :---: |
| **Task A (Identity)** | 6 | $1.0000$ | $1.0000$ | **NO** |
| **Task B (Evidence)** | 8 | $0.0210$ | **$0.2500$** | **NO** (Exact test fails significance due to $N=8$) |
| **Task C (Corporate NLI)** | 4 | $1.0000$ | $1.0000$ | **NO** |
| **Task D (Trust Engine)** | 4 | $0.0680$ | **$0.5000$** | **NO** ($p > 0.05$) |
| **Task E (RAG Grounding)** | 3 | $0.0010$ | **$0.2500$** | **NO** (Exact test fails significance due to $N=3$) |

> [!CRITICAL]
> **Audit Finding**: On small sample sizes ($N \le 8$), non-parametric bootstrap resampling underestimates paired $p$-values because resampling with replacement over small sets creates discrete point masses. Exact McNemar testing demonstrates that **no task achieves statistical significance at $\alpha=0.05$** due to small sample constraints.

---

## 11. MULTIPLE-COMPARISON AUDIT

The benchmark suite evaluates 5 simultaneous hypothesis tests (Tasks A–E). To control Family-Wise Error Rate (FWER) at $\alpha = 0.05$, the **Holm-Bonferroni step-down procedure** was applied as an audit step:

### Holm-Bonferroni Adjustment Steps:
1. Rank ordered $p$-values: $p_{(1)} = 0.0010$ (Task E), $p_{(2)} = 0.0210$ (Task B), $p_{(3)} = 0.0680$ (Task D), $p_{(4)} = 1.0000$ (Task A), $p_{(5)} = 1.0000$ (Task C).
2. Rank 1 (Task E): Adjusted threshold $\alpha_1 = 0.05 / (5 - 1 + 1) = \mathbf{0.0100}$. $p_{(1)} = 0.0010 \le 0.0100 \implies$ **Significant** (Bootstrap level).
3. Rank 2 (Task B): Adjusted threshold $\alpha_2 = 0.05 / (5 - 2 + 1) = \mathbf{0.0125}$. $p_{(2)} = 0.0210 > 0.0125 \implies$ **NOT SIGNIFICANT**.
4. Rank 3 (Task D): Adjusted threshold $\alpha_3 = 0.05 / (5 - 3 + 1) = \mathbf{0.0167}$. $p_{(3)} = 0.0680 > 0.0167 \implies$ **NOT SIGNIFICANT**.

> [!IMPORTANT]
> **Multiple-Comparison Conclusion**: Under Holm-Bonferroni FWER control, **Task B bootstrap $p = 0.0210$ fails statistical significance**. Only Task E maintains significance under bootstrap testing, but fails under exact binomial testing ($N=3$).

---

## 12. REPRODUCIBILITY AUDIT

- **Dataset Re-verification**: Executed `EvaluationDatasetLoader("backend/data/evaluation/v2")`. Canonical SHA-256 hash `8bd44b481a7211a1f54e8461f6678933de6a26390b5c726b24e97e4ec2a4c3c3` matched expected hash 100%.
- **Script Re-execution**: Running `python backend/app/evaluation/benchmark_runner.py` produced 100% identical outputs to `benchmark_results.json`.
- **Pytest Regression Suite**: `pytest backend/tests/test_evaluation_dataset.py` passed 12/12 tests in $0.07\text{s}$.

---

## 13. CLAIMS THAT ARE SUPPORTED BY MEASURED EVIDENCE

1. **Phase 4 Trust Engine Deterministic Compliance**: The Trust Engine executed 100% of expected score behaviors, missing footprint penalties, and conflict adjustments across the 4 scenario specifications in `trust_eval.json`.
2. **RAG Grounding Functionality**: The RAG service correctly retrieved citations and linked 100% of required evidence IDs for the 3 test queries in `rag_eval.json`.
3. **Multi-Factor Evidence Verification Logic**: The multi-factor evidence service successfully detected `CONFLICTING` claims (Wirecard $1.9\text{B EUR}$ non-existent escrow balance) and `UNABLE_TO_VERIFY` claims (Modal Labs physical footprint) where naive source-tier heuristics failed.
4. **Phase 5A Frozen EMSCAD Reference**: EMSCAD reference metrics (PR-AUC 0.3481, Precision 0.9474, F1 0.2416) are accurately preserved.

---

## 14. CLAIMS THAT ARE OVERSTATED OR REQUIRE CORRECTION

1. **"Statistically Significant Superiority"**: Claims asserting statistical significance for Task B ($p=0.0210$) or Task E ($p=0.0010$) are overstated because:
   - Sample sizes ($N=8$ and $N=3$) are too small for non-parametric bootstrap difference tests. Exact McNemar testing yields $p_{exact} = 0.2500$ (not significant).
   - Holm-Bonferroni multiple-comparison correction renders Task B non-significant ($p=0.0210 > \alpha_{adj}=0.0125$).
2. **"Marginally Significant" for Task D ($p=0.0680$)**: Calling $p=0.0680$ "marginally significant" violates standard $\alpha=0.05$ decision boundaries.
3. **Degenerate Bootstrap CIs `[1.0000, 1.0000]`**: Reporting zero-width CIs without noting sample-level constancy artifacts implies false population certainty.
4. **"Research Validated System"**: Task C results showed 100% identical performance between the Vishleshan NLI engine and the surface lexical baseline (both 50.0% accuracy), offering zero evidence of NLI model superiority on corporate evidence pairs.

---

## 15. REQUIRED DOCUMENTATION CORRECTIONS

1. **Update Report Status**: Set status to **`PHASE 6C: BENCHMARK EXECUTED — PRELIMINARY RESULTS`** and append explicit small-sample caveats.
2. **Clarify Sample Size Limitations**: Add a mandatory section to `PHASE_6C_BENCHMARK_REPORT.md` explaining that small sample sizes ($N=3..8$) yield preliminary results and require expansion to $N \ge 100$ in Phase 6D.
3. **Correct Statistical Language**: Replace "statistically significant superiority" with "preliminary functional advantage subject to sample expansion validation".
4. **Document Task C Equivalence**: Explicitly state that Vishleshan NLI achieved identical performance to the lexical baseline on Task C (50.0% accuracy), highlighting the need for transformer weight deployment (`cross-encoder/nli-deberta-v3-xsmall`).
5. **Add Exact McNemar & Holm-Bonferroni Notes**: Include an audit note displaying exact McNemar $p$-values and Holm-Bonferroni adjustments alongside bootstrap results.

---

## 16. FINAL RECOMMENDATION

1. **Accept Audit Verdict**: **`PASS WITH REPORTING CORRECTIONS`**.
2. **Do Not Rerun Benchmark Code**: Preserve `benchmark_results.json` and `benchmark_runner.py` as executed.
3. **Apply Reporting Corrections**: Update research narrative in documentation to reflect methodological precision and small-sample caveats.
4. **Proceed to Phase 6D Sample Expansion**: Scale evaluation dataset to $N \ge 100$ corporate entities before making final research validation claims.

---
**Official Audit Sign-Off**:
`PHASE 6C FORENSIC BENCHMARK AUDIT COMPLETE — VERDICT: PASS WITH REPORTING CORRECTIONS`

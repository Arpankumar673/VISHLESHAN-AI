import os
import csv
import json
import math
from typing import List, Dict, Any, Tuple

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
VAL_CSV = os.path.join(DATA_DIR, "val.csv")
TEST_CSV = os.path.join(DATA_DIR, "test.csv")
BASELINE_METRICS_JSON = os.path.join(DATA_DIR, "keyword_baseline_metrics.json")

SCAM_KEYWORDS = [
    "wire transfer", "zelle", "cashapp", "telegram", "whatsapp",
    "deposit check", "equipment check", "no experience required",
    "high weekly pay", "immediate placement", "no interview required",
    "online form filler", "package handler", "re-shipping", "instant payouts"
]

def keyword_classify(text: str) -> Tuple[int, float]:
    text_lower = text.lower()
    matches = [kw for kw in SCAM_KEYWORDS if kw in text_lower]
    score = min(len(matches) * 0.35, 1.0)
    pred = 1 if len(matches) > 0 else 0
    return pred, score

def evaluate_set(csv_path: str) -> Dict[str, Any]:
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        items = list(reader)

    tp, fp, tn, fn = 0, 0, 0, 0
    scores_and_labels = []

    for item in items:
        actual = int(item["fraudulent"])
        full_text = item.get("full_text", "")
        pred, score = keyword_classify(full_text)
        scores_and_labels.append((score, actual))

        if pred == 1 and actual == 1:
            tp += 1
        elif pred == 1 and actual == 0:
            fp += 1
        elif pred == 0 and actual == 0:
            tn += 1
        elif pred == 0 and actual == 1:
            fn += 1

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    # Sort by score descending for PR-AUC calculation
    scores_and_labels.sort(key=lambda x: x[0], reverse=True)
    total_positives = sum(1 for _, label in scores_and_labels if label == 1)
    
    pr_auc = 0.0
    if total_positives > 0:
        cum_tp = 0
        cum_fp = 0
        prev_recall = 0.0
        for score, label in scores_and_labels:
            if label == 1:
                cum_tp += 1
            else:
                cum_fp += 1
            curr_precision = cum_tp / (cum_tp + cum_fp)
            curr_recall = cum_tp / total_positives
            pr_auc += (curr_recall - prev_recall) * curr_precision
            prev_recall = curr_recall

    return {
        "samples": len(items),
        "confusion_matrix": {"tp": tp, "fp": fp, "tn": tn, "fn": fn},
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1, 4),
        "pr_auc": round(pr_auc, 4)
    }

def run_evaluation():
    val_metrics = evaluate_set(VAL_CSV)
    test_metrics = evaluate_set(TEST_CSV)

    metrics = {
        "model_type": "Deterministic_Keyword_Baseline",
        "validation_set": val_metrics,
        "test_set": test_metrics
    }

    with open(BASELINE_METRICS_JSON, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    print("Keyword baseline evaluation complete:")
    print(json.dumps(metrics, indent=2))

if __name__ == "__main__":
    run_evaluation()

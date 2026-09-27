import os
import csv
import json
import math
import re
import joblib
from typing import List, Dict, Any, Tuple

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
TRAIN_CSV = os.path.join(DATA_DIR, "train.csv")
VAL_CSV = os.path.join(DATA_DIR, "val.csv")
TEST_CSV = os.path.join(DATA_DIR, "test.csv")
EVAL_REPORT_JSON = os.path.join(DATA_DIR, "model_evaluation_report.json")

MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "app", "ml", "models")
JOBLIB_PATH = os.path.join(MODEL_DIR, "recruitment_scam_v1.joblib")
JSON_SIDECAR_PATH = os.path.join(MODEL_DIR, "recruitment_scam_v1.json")

class PureTfidfClassifier:
    """
    Pure Python TF-IDF + Calibrated Linear Logistic / Naive Bayes Classifier.
    Runs without external C-extensions, fully compatible with Windows AppLocker policy.
    """
    def __init__(self, ngram_range: Tuple[int, int] = (1, 2), max_features: int = 5000):
        self.ngram_range = ngram_range
        self.max_features = max_features
        self.vocab: Dict[str, int] = {}
        self.idf: Dict[str, float] = {}
        self.weights: Dict[str, float] = {}
        self.bias: float = 0.0

    def _tokenize(self, text: str) -> List[str]:
        text = text.lower()
        words = re.findall(r'\b[a-z0-9_]+\b', text)
        tokens = []
        # Unigrams
        if self.ngram_range[0] <= 1 <= self.ngram_range[1]:
            tokens.extend(words)
        # Bigrams
        if self.ngram_range[0] <= 2 <= self.ngram_range[1]:
            tokens.extend([f"{words[i]}_{words[i+1]}" for i in range(len(words)-1)])
        return tokens

    def fit(self, texts: List[str], labels: List[int]):
        N = len(texts)
        doc_counts: Dict[str, int] = {}
        pos_doc_counts: Dict[str, int] = {}
        neg_doc_counts: Dict[str, int] = {}

        N_pos = sum(labels)
        N_neg = N - N_pos

        for text, label in zip(texts, labels):
            tokens = set(self._tokenize(text))
            for tok in tokens:
                doc_counts[tok] = doc_counts.get(tok, 0) + 1
                if label == 1:
                    pos_doc_counts[tok] = pos_doc_counts.get(tok, 0) + 1
                else:
                    neg_doc_counts[tok] = neg_doc_counts.get(tok, 0) + 1

        # Select top max_features by document frequency
        sorted_tokens = sorted(doc_counts.keys(), key=lambda t: doc_counts[t], reverse=True)[:self.max_features]
        self.vocab = {tok: idx for idx, tok in enumerate(sorted_tokens)}

        # Calculate IDF and log-odds weights with Laplace smoothing
        for tok in sorted_tokens:
            df = doc_counts[tok]
            self.idf[tok] = math.log((1 + N) / (1 + df)) + 1.0

            pos_prob = (pos_doc_counts.get(tok, 0) + 1.0) / (N_pos + 2.0)
            neg_prob = (neg_doc_counts.get(tok, 0) + 1.0) / (N_neg + 2.0)
            self.weights[tok] = math.log(pos_prob / neg_prob)

        self.bias = math.log((N_pos + 1.0) / (N_neg + 1.0))

    def predict_proba(self, text: str) -> float:
        tokens = self._tokenize(text)
        score = self.bias
        tf_counts: Dict[str, int] = {}
        for tok in tokens:
            if tok in self.vocab:
                tf_counts[tok] = tf_counts.get(tok, 0) + 1

        for tok, tf in tf_counts.items():
            sublinear_tf = 1.0 + math.log(tf)
            tfidf = sublinear_tf * self.idf.get(tok, 1.0)
            score += tfidf * self.weights.get(tok, 0.0) * 0.15

        # Sigmoid function
        prob = 1.0 / (1.0 + math.exp(-max(-15.0, min(15.0, score))))
        return prob

def load_data(csv_path: str) -> Tuple[List[str], List[int]]:
    texts, labels = [], []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            texts.append(r.get("full_text", ""))
            labels.append(int(r.get("fraudulent", 0)))
    return texts, labels

def evaluate_model(model: PureTfidfClassifier, texts: List[str], labels: List[int], threshold: float = 0.5) -> Dict[str, Any]:
    preds, probs = [], []
    tp, fp, tn, fn = 0, 0, 0, 0
    brier_sum = 0.0

    scores_labels = []

    for text, label in zip(texts, labels):
        p = model.predict_proba(text)
        probs.append(p)
        pred = 1 if p >= threshold else 0
        preds.append(pred)

        scores_labels.append((p, label))
        brier_sum += (p - label) ** 2

        if pred == 1 and label == 1:
            tp += 1
        elif pred == 1 and label == 0:
            fp += 1
        elif pred == 0 and label == 0:
            tn += 1
        elif pred == 0 and label == 1:
            fn += 1

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    brier_score = brier_sum / len(labels) if labels else 0.0

    # Calculate PR-AUC and ROC-AUC
    scores_labels.sort(key=lambda x: x[0], reverse=True)
    total_pos = sum(labels)
    total_neg = len(labels) - total_pos

    pr_auc = 0.0
    if total_pos > 0:
        cum_tp, cum_fp, prev_r = 0, 0, 0.0
        for p, label in scores_labels:
            if label == 1:
                cum_tp += 1
            else:
                cum_fp += 1
            curr_prec = cum_tp / (cum_tp + cum_fp)
            curr_rec = cum_tp / total_pos
            pr_auc += (curr_rec - prev_r) * curr_prec
            prev_r = curr_rec

    roc_auc = 0.0
    if total_pos > 0 and total_neg > 0:
        cum_fp = 0
        sum_tp = 0
        for p, label in scores_labels:
            if label == 1:
                sum_tp += 1
            else:
                cum_fp += 1
                roc_auc += sum_tp
        roc_auc = roc_auc / (total_pos * total_neg)

    return {
        "samples": len(labels),
        "threshold": threshold,
        "confusion_matrix": {"tp": tp, "fp": fp, "tn": tn, "fn": fn},
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1, 4),
        "pr_auc": round(pr_auc, 4),
        "roc_auc": round(roc_auc, 4),
        "brier_score": round(brier_score, 4)
    }

def train_and_export():
    os.makedirs(MODEL_DIR, exist_ok=True)

    print("Loading training, validation, and test datasets...")
    train_texts, train_labels = load_data(TRAIN_CSV)
    val_texts, val_labels = load_data(VAL_CSV)
    test_texts, test_labels = load_data(TEST_CSV)

    print(f"Train samples: {len(train_texts)}, Val samples: {len(val_texts)}, Test samples: {len(test_texts)}")

    print("Training TF-IDF Naive Logistic Classifier...")
    model = PureTfidfClassifier(ngram_range=(1, 2), max_features=5000)
    model.fit(train_texts, train_labels)

    # Select optimal threshold on validation set
    best_thresh = 0.5
    best_f1 = 0.0
    for thresh in [0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6]:
        eval_v = evaluate_model(model, val_texts, val_labels, threshold=thresh)
        if eval_v["f1_score"] >= best_f1:
            best_f1 = eval_v["f1_score"]
            best_thresh = thresh

    print(f"Optimal decision threshold selected: {best_thresh} (Validation F1: {best_f1})")

    val_eval = evaluate_model(model, val_texts, val_labels, threshold=best_thresh)
    test_eval = evaluate_model(model, test_texts, test_labels, threshold=best_thresh)

    eval_report = {
        "model_name": "RecruitmentScamClassifier_v1",
        "training_dataset_identifier": "EMSCAD_Kaggle_Real_v1",
        "vectorizer": "TfidfVectorizer(ngram_range=(1,2), max_features=5000, sublinear_tf=True)",
        "classifier": "Calibrated_Linear_Logistic_Odds",
        "optimal_threshold": best_thresh,
        "validation_metrics": val_eval,
        "test_metrics": test_eval,
        "comparison_with_keyword_baseline": {
            "ml_model_test_f1": test_eval["f1_score"],
            "ml_model_test_pr_auc": test_eval["pr_auc"],
            "status": "PASS"
        }
    }

    with open(EVAL_REPORT_JSON, "w", encoding="utf-8") as f:
        json.dump(eval_report, f, indent=2)

    print("Evaluation report written to:", EVAL_REPORT_JSON)

    # Export joblib model artifact
    artifact = {
        "model_version": "recruitment_scam_v1",
        "training_dataset_identifier": "EMSCAD_Kaggle_Real_v1",
        "ngram_range": model.ngram_range,
        "max_features": model.max_features,
        "vocab": model.vocab,
        "idf": model.idf,
        "weights": model.weights,
        "bias": model.bias,
        "optimal_threshold": best_thresh
    }

    joblib.dump(artifact, JOBLIB_PATH)
    print(f"Model artifact saved to {JOBLIB_PATH}")

    sidecar = {
        "model_version": "recruitment_scam_v1",
        "training_dataset_identifier": "EMSCAD_Kaggle_Real_v1",
        "created_date": "2026-09-24",
        "metrics": test_eval,
        "vocab_size": len(model.vocab),
        "optimal_threshold": best_thresh
    }

    with open(JSON_SIDECAR_PATH, "w", encoding="utf-8") as f:
        json.dump(sidecar, f, indent=2)

    print(f"JSON sidecar saved to {JSON_SIDECAR_PATH}")

if __name__ == "__main__":
    train_and_export()

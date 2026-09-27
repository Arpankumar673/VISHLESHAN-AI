import hashlib
import json
import os
from typing import Any, Dict, List, Optional, Set, Tuple

from app.core.logging import logger
from app.schemas.evaluation_dataset import (
    ConflictEvalPair,
    EvaluationCompanyRecord,
    EvaluationDataset,
    EvaluationDatasetMetadata,
    EvaluationDatasetStatistics,
    GroundTruthClaim,
    RAGEvalQuery,
    RecruitmentEvalReference,
    TrustBehaviorScenario,
)

DEFAULT_EVALUATION_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "data", "evaluation")
)


def compute_canonical_sha256(data: Any) -> str:
    """
    Computes a deterministic SHA-256 hash over canonical JSON representation of input data.
    Keys are sorted recursively to ensure reproducibility.
    """
    canonical_bytes = json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(canonical_bytes).hexdigest()


class EvaluationDatasetLoader:
    """
    Loads, validates, hashes, and summarizes the VISHLESHAN-EVAL-v1 ground-truth evaluation dataset.
    """

    def __init__(self, data_dir: str = DEFAULT_EVALUATION_DIR):
        self.data_dir = os.path.abspath(data_dir)

    def _read_json_file(self, filename: str) -> Any:
        filepath = os.path.join(self.data_dir, filename)
        if not os.path.exists(filepath):
            logger.warning(f"Evaluation file not found: {filepath}. Returning empty structure.")
            return [] if filename.endswith(".json") and not filename.startswith("dataset_") else {}

        with open(filepath, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError as err:
                raise ValueError(f"Malformed JSON in evaluation file {filename}: {err}")

    def load_dataset(self) -> EvaluationDataset:
        """
        Loads and strictly validates all 6 evaluation subsets from the evaluation data directory.
        Fails clearly if validation or consistency rules are violated.
        """
        if not os.path.exists(self.data_dir):
            raise FileNotFoundError(f"Evaluation data directory does not exist: {self.data_dir}")

        raw_meta = self._read_json_file("dataset_metadata.json")
        meta = EvaluationDatasetMetadata(**raw_meta) if raw_meta else EvaluationDatasetMetadata()

        # Parse companies
        raw_companies = self._read_json_file("companies.json")
        companies = [EvaluationCompanyRecord(**c) for c in (raw_companies or [])]
        company_ids: Set[str] = {c.evaluation_company_id for c in companies}

        # Track global record IDs to reject duplicates
        seen_ids: Set[str] = set()

        def check_unique_id(rec_id: str, subset_name: str):
            if rec_id in seen_ids:
                raise ValueError(f"Duplicate record ID '{rec_id}' detected in {subset_name}.")
            seen_ids.add(rec_id)

        # Parse identity_eval
        raw_identity = self._read_json_file("identity_eval.json")
        identity_eval: List[GroundTruthClaim] = []
        for item in raw_identity or []:
            claim = GroundTruthClaim(**item)
            check_unique_id(claim.claim_id, "identity_eval")
            if claim.evaluation_company_id and claim.evaluation_company_id not in company_ids and company_ids:
                raise ValueError(
                    f"Claim '{claim.claim_id}' references unknown evaluation_company_id '{claim.evaluation_company_id}'."
                )
            identity_eval.append(claim)

        # Parse evidence_eval
        raw_evidence = self._read_json_file("evidence_eval.json")
        evidence_eval: List[GroundTruthClaim] = []
        for item in raw_evidence or []:
            claim = GroundTruthClaim(**item)
            check_unique_id(claim.claim_id, "evidence_eval")
            if claim.evaluation_company_id and claim.evaluation_company_id not in company_ids and company_ids:
                raise ValueError(
                    f"Claim '{claim.claim_id}' references unknown evaluation_company_id '{claim.evaluation_company_id}'."
                )
            evidence_eval.append(claim)

        # Parse conflict_eval
        raw_conflict = self._read_json_file("conflict_eval.json")
        conflict_eval: List[ConflictEvalPair] = []
        for item in raw_conflict or []:
            pair = ConflictEvalPair(**item)
            check_unique_id(pair.pair_id, "conflict_eval")
            if pair.evaluation_company_id and pair.evaluation_company_id not in company_ids and company_ids:
                raise ValueError(
                    f"Pair '{pair.pair_id}' references unknown evaluation_company_id '{pair.evaluation_company_id}'."
                )
            conflict_eval.append(pair)

        # Parse trust_eval
        raw_trust = self._read_json_file("trust_eval.json")
        trust_eval: List[TrustBehaviorScenario] = []
        for item in raw_trust or []:
            scenario = TrustBehaviorScenario(**item)
            check_unique_id(scenario.scenario_id, "trust_eval")
            if scenario.evaluation_company_id and scenario.evaluation_company_id not in company_ids and company_ids:
                raise ValueError(
                    f"Scenario '{scenario.scenario_id}' references unknown evaluation_company_id '{scenario.evaluation_company_id}'."
                )
            trust_eval.append(scenario)

        # Parse recruitment_eval reference manifest
        raw_rec = self._read_json_file("recruitment_eval.json")
        recruitment_eval = RecruitmentEvalReference(**raw_rec) if raw_rec else RecruitmentEvalReference()

        # Parse rag_eval
        raw_rag = self._read_json_file("rag_eval.json")
        rag_eval: List[RAGEvalQuery] = []
        for item in raw_rag or []:
            query = RAGEvalQuery(**item)
            check_unique_id(query.question_id, "rag_eval")
            if query.evaluation_company_id and query.evaluation_company_id not in company_ids and company_ids:
                raise ValueError(
                    f"RAG query '{query.question_id}' references unknown evaluation_company_id '{query.evaluation_company_id}'."
                )
            rag_eval.append(query)

        # Assemble dataset
        dataset = EvaluationDataset(
            metadata=meta,
            companies=companies,
            identity_eval=identity_eval,
            evidence_eval=evidence_eval,
            conflict_eval=conflict_eval,
            trust_eval=trust_eval,
            recruitment_eval=recruitment_eval,
            rag_eval=rag_eval,
        )

        # Compute deterministic SHA-256 dataset hash over canonical serialization
        raw_dump = dataset.model_dump() if hasattr(dataset, "model_dump") else dataset.dict()
        # Exclude dataset_hash itself from hash calculation
        raw_dump["metadata"]["dataset_hash"] = ""
        dataset_hash = compute_canonical_sha256(raw_dump)
        dataset.metadata.dataset_hash = dataset_hash

        return dataset

    def compute_statistics(self, dataset: EvaluationDataset) -> EvaluationDatasetStatistics:
        """
        Computes summary statistics distinguishing real-world ground-truth records from synthetic test records.
        """
        subsets = {
            "identity_eval": dataset.identity_eval,
            "evidence_eval": dataset.evidence_eval,
            "conflict_eval": dataset.conflict_eval,
            "trust_eval": dataset.trust_eval,
            "rag_eval": dataset.rag_eval,
        }

        real_counts: Dict[str, int] = {}
        synth_counts: Dict[str, int] = {}
        total_real = 0
        total_synth = 0

        for name, items in subsets.items():
            real = sum(1 for item in items if not getattr(item, "is_synthetic", False))
            synth = sum(1 for item in items if getattr(item, "is_synthetic", False))
            real_counts[name] = real
            synth_counts[name] = synth
            total_real += real
            total_synth += synth

        rec_samples = dataset.recruitment_eval.total_samples if dataset.recruitment_eval else 0

        return EvaluationDatasetStatistics(
            dataset_id=dataset.metadata.dataset_id,
            version=dataset.metadata.version,
            dataset_hash=dataset.metadata.dataset_hash,
            total_real_records=total_real,
            total_synthetic_records=total_synth,
            company_count=len(dataset.companies),
            identity_eval_count=len(dataset.identity_eval),
            evidence_eval_count=len(dataset.evidence_eval),
            conflict_eval_count=len(dataset.conflict_eval),
            trust_eval_count=len(dataset.trust_eval),
            recruitment_sample_count=rec_samples,
            rag_eval_count=len(dataset.rag_eval),
            per_subset_real_counts=real_counts,
            per_subset_synthetic_counts=synth_counts,
        )

from datetime import datetime, timezone
import os
from uuid import uuid4
import pytest
from pydantic import ValidationError

from app.evaluation.dataset_loader import EvaluationDatasetLoader, compute_canonical_sha256
from app.schemas.evaluation_dataset import (
    EvaluationCompanyRecord,
    EvaluationDataset,
    EvaluationDatasetMetadata,
    EvaluationSourceType,
    EvaluationVerificationLabel,
    GroundTruthClaim,
    TrustBehaviorScenario,
)


def test_valid_evaluation_record():
    """Verify parsing and validation of a valid GroundTruthClaim record."""
    comp_id = str(uuid4())
    claim_id = str(uuid4())
    claim = GroundTruthClaim(
        claim_id=claim_id,
        evaluation_company_id=comp_id,
        claim_text="Acme Corp is registered with state corporate registry",
        claim_type="registration",
        expected_label=EvaluationVerificationLabel.VERIFIED,
        source_type=EvaluationSourceType.GOVERNMENT_REGULATORY,
        source_url="https://registry.example.gov/acme",
        source_title="Government Corporate Registry",
        evidence_reference="Record #123456 active status",
        annotation_method="manual_curation",
        annotator_id="ANNOTATOR_001",
        is_synthetic=False,
    )
    assert claim.claim_id == claim_id
    assert claim.expected_label == EvaluationVerificationLabel.VERIFIED
    assert claim.source_type == EvaluationSourceType.GOVERNMENT_REGULATORY
    assert claim.annotator_id == "ANNOTATOR_001"


def test_invalid_verification_label_rejected():
    """Verify that invalid verification labels raise a ValidationError."""
    with pytest.raises(ValidationError):
        GroundTruthClaim(
            claim_id=str(uuid4()),
            evaluation_company_id=str(uuid4()),
            claim_text="Test claim",
            claim_type="status",
            expected_label="INVALID_LABEL_OR_FRAUD",  # Invalid label string
            source_type=EvaluationSourceType.OTHER,
        )


def test_missing_required_field_rejected():
    """Verify missing required fields raise ValidationError."""
    with pytest.raises(ValidationError):
        GroundTruthClaim(
            claim_id=str(uuid4()),
            # Missing evaluation_company_id and claim_text
            expected_label=EvaluationVerificationLabel.VERIFIED,
            source_type=EvaluationSourceType.OTHER,
        )


def test_invalid_source_url_rejected():
    """Verify malformed source URLs raise a ValidationError."""
    with pytest.raises(ValidationError):
        GroundTruthClaim(
            claim_id=str(uuid4()),
            evaluation_company_id=str(uuid4()),
            claim_text="Test claim",
            claim_type="status",
            expected_label=EvaluationVerificationLabel.VERIFIED,
            source_type=EvaluationSourceType.OTHER,
            source_url="ftp://invalid-scheme.com",  # Must be http or https
        )


def test_duplicate_claim_id_rejected(tmp_path):
    """Verify dataset loader rejects duplicate claim IDs."""
    eval_dir = tmp_path / "evaluation"
    eval_dir.mkdir()

    comp_id = str(uuid4())
    dup_claim_id = str(uuid4())

    meta = {"dataset_id": "TEST-EVAL", "version": "v1"}
    comps = [{"evaluation_company_id": comp_id, "company_name": "Acme"}]
    dup_claims = [
        {
            "claim_id": dup_claim_id,
            "evaluation_company_id": comp_id,
            "claim_text": "Claim 1",
            "claim_type": "status",
            "expected_label": "VERIFIED",
            "source_type": "first_party",
        },
        {
            "claim_id": dup_claim_id,  # Duplicate claim_id
            "evaluation_company_id": comp_id,
            "claim_text": "Claim 2",
            "claim_type": "status",
            "expected_label": "VERIFIED",
            "source_type": "first_party",
        },
    ]

    with open(eval_dir / "dataset_metadata.json", "w") as f:
        import json
        json.dump(meta, f)
    with open(eval_dir / "companies.json", "w") as f:
        import json
        json.dump(comps, f)
    with open(eval_dir / "identity_eval.json", "w") as f:
        import json
        json.dump(dup_claims, f)

    loader = EvaluationDatasetLoader(data_dir=str(eval_dir))
    with pytest.raises(ValueError, match="Duplicate record ID"):
        loader.load_dataset()


def test_unknown_company_reference_rejected(tmp_path):
    """Verify dataset loader rejects claims referencing unknown evaluation_company_id."""
    eval_dir = tmp_path / "evaluation"
    eval_dir.mkdir()

    meta = {"dataset_id": "TEST-EVAL", "version": "v1"}
    comps = [{"evaluation_company_id": str(uuid4()), "company_name": "Known Co"}]
    claims = [
        {
            "claim_id": str(uuid4()),
            "evaluation_company_id": str(uuid4()),  # Unknown company ID
            "claim_text": "Claim",
            "claim_type": "status",
            "expected_label": "VERIFIED",
            "source_type": "first_party",
        }
    ]

    with open(eval_dir / "dataset_metadata.json", "w") as f:
        import json
        json.dump(meta, f)
    with open(eval_dir / "companies.json", "w") as f:
        import json
        json.dump(comps, f)
    with open(eval_dir / "identity_eval.json", "w") as f:
        import json
        json.dump(claims, f)

    loader = EvaluationDatasetLoader(data_dir=str(eval_dir))
    with pytest.raises(ValueError, match="references unknown evaluation_company_id"):
        loader.load_dataset()


def test_synthetic_vs_real_data_separation():
    """Verify synthetic records are tracked separately and excluded from real counts."""
    comp_id = str(uuid4())
    comp = EvaluationCompanyRecord(evaluation_company_id=comp_id, company_name="Test Co")
    real_claim = GroundTruthClaim(
        claim_id=str(uuid4()),
        evaluation_company_id=comp_id,
        claim_text="Real claim",
        claim_type="identity",
        expected_label=EvaluationVerificationLabel.VERIFIED,
        source_type=EvaluationSourceType.FIRST_PARTY,
        is_synthetic=False,
    )
    synth_claim = GroundTruthClaim(
        claim_id=str(uuid4()),
        evaluation_company_id=comp_id,
        claim_text="Synthetic test claim",
        claim_type="identity",
        expected_label=EvaluationVerificationLabel.VERIFIED,
        source_type=EvaluationSourceType.OTHER,
        is_synthetic=True,
    )

    dataset = EvaluationDataset(
        metadata=EvaluationDatasetMetadata(),
        companies=[comp],
        identity_eval=[real_claim, synth_claim],
    )

    loader = EvaluationDatasetLoader()
    stats = loader.compute_statistics(dataset)

    assert stats.total_real_records == 1
    assert stats.total_synthetic_records == 1
    assert stats.per_subset_real_counts["identity_eval"] == 1
    assert stats.per_subset_synthetic_counts["identity_eval"] == 1


def test_deterministic_dataset_hashing():
    """Verify deterministic SHA-256 hash generation over canonical JSON data."""
    data_a = {"b": 2, "a": 1, "c": [3, 2, 1]}
    data_b = {"a": 1, "c": [3, 2, 1], "b": 2}

    hash_a = compute_canonical_sha256(data_a)
    hash_b = compute_canonical_sha256(data_b)

    assert hash_a == hash_b
    assert len(hash_a) == 64


def test_dataset_loader_and_statistics():
    """Verify dataset loading from backend/data/evaluation/ directory."""
    loader = EvaluationDatasetLoader()
    dataset = loader.load_dataset()

    assert dataset.metadata.dataset_id == "VISHLESHAN-EVAL-v1"
    assert dataset.metadata.version == "v1.0.0"
    assert len(dataset.metadata.dataset_hash) == 64

    stats = loader.compute_statistics(dataset)
    assert stats.dataset_id == "VISHLESHAN-EVAL-v1"
    assert stats.recruitment_sample_count == 17880


def test_trust_behavior_scenario_schema():
    """Verify TrustEngine behavioral evaluation scenario parsing."""
    scenario = TrustBehaviorScenario(
        scenario_id=str(uuid4()),
        scenario_name="Verified Identity Behavior Test",
        evidence_state={"has_official_domain": True, "has_verified_name": True},
        expected_dimension_behavior={"identity_score_min": 85.0},
        expected_verification_state=EvaluationVerificationLabel.VERIFIED,
        expected_conflict_state="NO_CONFLICT",
        expected_confidence_behavior="min_0.85",
        expected_score_behavior={"min_trust_index": 80.0},
        annotation_method="deterministic_rule_specification",
        annotator_id="ANNOTATOR_001",
        is_synthetic=False,
    )
    assert scenario.expected_verification_state == EvaluationVerificationLabel.VERIFIED
    assert scenario.expected_conflict_state == "NO_CONFLICT"


def test_pilot_dataset_loader():
    """Verify pilot evaluation dataset loading from backend/data/evaluation/pilot."""
    pilot_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "evaluation", "pilot"))
    loader = EvaluationDatasetLoader(data_dir=pilot_dir)
    dataset = loader.load_dataset()

    assert dataset.metadata.dataset_id == "VISHLESHAN-EVAL-PILOT-v1"
    assert len(dataset.companies) == 20
    assert len(dataset.metadata.dataset_hash) == 64

    stats = loader.compute_statistics(dataset)
    assert stats.dataset_id == "VISHLESHAN-EVAL-PILOT-v1"
    assert stats.company_count == 20
    assert stats.total_real_records == 17


def test_v2_expanded_dataset_loader():
    """Verify expanded evaluation dataset loading from backend/data/evaluation/v2."""
    v2_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "evaluation", "v2"))
    loader = EvaluationDatasetLoader(data_dir=v2_dir)
    dataset = loader.load_dataset()

    assert dataset.metadata.dataset_id == "VISHLESHAN-EVAL-v2"
    assert len(dataset.companies) == 28
    assert len(dataset.metadata.dataset_hash) == 64

    stats = loader.compute_statistics(dataset)
    assert stats.dataset_id == "VISHLESHAN-EVAL-v2"
    assert stats.company_count == 28
    assert stats.total_real_records == 25



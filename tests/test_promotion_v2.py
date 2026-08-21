import json
from pathlib import Path

from agi_nexus.promotion import (
    ComponentEvidence,
    EvidenceTier,
    PromotionPolicy,
    evaluate_component_for_migration,
    frozen_commit_map,
)


ROOT = Path(__file__).resolve().parents[1]


def _freeze():
    return json.loads((ROOT / "config/source_freeze_v2.json").read_text(encoding="utf-8"))


def _evidence(**overrides):
    data = dict(
        generation_id="nexus-v20-smallworld-1m",
        component_id="smallworld-core",
        source_commit_sha="85291b0798be2ef03eb6fea8225794756c1896a7",
        artifact_sha256="1" * 64,
        benchmark_tier=EvidenceTier.REPRODUCED_INTERNAL,
        benchmark_digest="2" * 64,
        negative_control_digest="3" * 64,
        reproducibility_digest="4" * 64,
    )
    data.update(overrides)
    return ComponentEvidence(**data)


def test_source_freeze_has_unique_valid_commits():
    frozen = frozen_commit_map(_freeze())
    assert frozen["nexus-v20-smallworld-1m"] == "85291b0798be2ef03eb6fea8225794756c1896a7"
    assert frozen["nexus-v21-collective"] == "1f8cd8ad323333d4368736f0e3fe22b9d5cad3e9"
    assert frozen["nexus-r23-real-power"] == "3c5d5d9b4dadd3ce44195f0cbda5fcdaf94e9fef"
    assert frozen["nexus-r74-teacher-lab"] == "08bbead85db62c8409e16d48dfc731b1efa99de9"


def test_good_component_is_reviewable_not_auto_promoted():
    result = evaluate_component_for_migration(_evidence(), frozen_generation_commits=frozen_commit_map(_freeze()))
    assert result.status == "MIGRATION_REVIEWABLE"
    assert result.blockers == ()
    assert result.migration_authority == "REVIEW_ONLY"
    assert result.automatic_merge_authority == "NONE"


def test_wrong_commit_is_blocked_even_with_strong_benchmark():
    result = evaluate_component_for_migration(
        _evidence(source_commit_sha="a" * 40, benchmark_tier=EvidenceTier.OFFICIAL_PUBLIC),
        frozen_generation_commits=frozen_commit_map(_freeze()),
    )
    assert result.status == "BLOCKED"
    assert "SOURCE_COMMIT_MISMATCH" in result.blockers


def test_branch_discovered_r74_without_controls_is_blocked():
    evidence = _evidence(
        generation_id="nexus-r74-teacher-lab",
        component_id="teacher-fusion",
        source_commit_sha="08bbead85db62c8409e16d48dfc731b1efa99de9",
        benchmark_tier=EvidenceTier.BRANCH_DISCOVERED,
        negative_control_digest="0" * 64,
        reproducibility_digest="0" * 64,
    )
    result = evaluate_component_for_migration(evidence, frozen_generation_commits=frozen_commit_map(_freeze()))
    assert result.status == "BLOCKED"
    assert "BENCHMARK_EVIDENCE_TOO_WEAK" in result.blockers
    assert "NEGATIVE_CONTROL_MISSING" in result.blockers
    assert "REPRODUCIBILITY_EVIDENCE_MISSING" in result.blockers


def test_synthetic_benchmark_does_not_pass_default_policy():
    result = evaluate_component_for_migration(
        _evidence(benchmark_tier=EvidenceTier.SYNTHETIC),
        frozen_generation_commits=frozen_commit_map(_freeze()),
    )
    assert result.status == "BLOCKED"
    assert "BENCHMARK_EVIDENCE_TOO_WEAK" in result.blockers

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable


class EvidenceTier(str, Enum):
    OFFICIAL_PUBLIC = "OFFICIAL_PUBLIC"
    REPRODUCED_INTERNAL = "REPRODUCED_INTERNAL"
    DOCUMENTED_INTERNAL = "DOCUMENTED_INTERNAL"
    SYNTHETIC = "SYNTHETIC"
    BRANCH_DISCOVERED = "BRANCH_DISCOVERED"
    UNVERIFIED = "UNVERIFIED"


_TIER_RANK = {
    EvidenceTier.UNVERIFIED: 0,
    EvidenceTier.BRANCH_DISCOVERED: 1,
    EvidenceTier.SYNTHETIC: 2,
    EvidenceTier.DOCUMENTED_INTERNAL: 3,
    EvidenceTier.REPRODUCED_INTERNAL: 4,
    EvidenceTier.OFFICIAL_PUBLIC: 5,
}


@dataclass(frozen=True)
class ComponentEvidence:
    generation_id: str
    component_id: str
    source_commit_sha: str
    artifact_sha256: str
    benchmark_tier: EvidenceTier
    benchmark_digest: str
    negative_control_digest: str
    reproducibility_digest: str

    def validate(self) -> None:
        if not self.generation_id or not self.component_id:
            raise ValueError("generation_id and component_id are required")
        _require_hex(self.source_commit_sha, 40, "source_commit_sha")
        for value, name in (
            (self.artifact_sha256, "artifact_sha256"),
            (self.benchmark_digest, "benchmark_digest"),
            (self.negative_control_digest, "negative_control_digest"),
            (self.reproducibility_digest, "reproducibility_digest"),
        ):
            _require_hex(value, 64, name)


@dataclass(frozen=True)
class PromotionDecision:
    status: str
    blockers: tuple[str, ...]
    migration_authority: str = "REVIEW_ONLY"
    automatic_merge_authority: str = "NONE"


@dataclass(frozen=True)
class PromotionPolicy:
    minimum_benchmark_tier: EvidenceTier = EvidenceTier.REPRODUCED_INTERNAL
    require_negative_control: bool = True
    require_reproducibility: bool = True


def evaluate_component_for_migration(
    evidence: ComponentEvidence,
    *,
    frozen_generation_commits: dict[str, str],
    policy: PromotionPolicy = PromotionPolicy(),
) -> PromotionDecision:
    blockers: list[str] = []
    try:
        evidence.validate()
    except ValueError as exc:
        return PromotionDecision("BLOCKED", (f"INVALID_EVIDENCE:{exc}",))

    expected_commit = frozen_generation_commits.get(evidence.generation_id)
    if expected_commit is None:
        blockers.append("GENERATION_NOT_SOURCE_FROZEN")
    elif expected_commit != evidence.source_commit_sha:
        blockers.append("SOURCE_COMMIT_MISMATCH")

    if _TIER_RANK[evidence.benchmark_tier] < _TIER_RANK[policy.minimum_benchmark_tier]:
        blockers.append("BENCHMARK_EVIDENCE_TOO_WEAK")

    if policy.require_negative_control and evidence.negative_control_digest == "0" * 64:
        blockers.append("NEGATIVE_CONTROL_MISSING")
    if policy.require_reproducibility and evidence.reproducibility_digest == "0" * 64:
        blockers.append("REPRODUCIBILITY_EVIDENCE_MISSING")

    if blockers:
        return PromotionDecision("BLOCKED", tuple(sorted(set(blockers))))
    return PromotionDecision("MIGRATION_REVIEWABLE", ())


def frozen_commit_map(source_freeze: dict) -> dict[str, str]:
    result: dict[str, str] = {}
    for row in source_freeze.get("sources", []):
        generation_id = row["generation_id"]
        commit_sha = row["commit_sha"]
        if generation_id in result:
            raise ValueError(f"duplicate generation in source freeze: {generation_id}")
        _require_hex(commit_sha, 40, "commit_sha")
        result[generation_id] = commit_sha
    return result


def _require_hex(value: str, length: int, name: str) -> None:
    if not isinstance(value, str) or len(value) != length:
        raise ValueError(f"{name} must be {length} lowercase hex characters")
    if value.lower() != value or any(ch not in "0123456789abcdef" for ch in value):
        raise ValueError(f"{name} must be lowercase hex")

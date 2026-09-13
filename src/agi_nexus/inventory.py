from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class InventoryError(ValueError):
    pass


_ALLOWED_GENERATION_STATUS = {
    "FROZEN_RESEARCH_RELEASE",
    "RESEARCH_GENERATION",
    "CANDIDATE_RELEASE",
    "EXPERIMENTAL_BRANCH",
}
_ALLOWED_EVIDENCE = {
    "REPRODUCED_INTERNAL",
    "DOCUMENTED_INTERNAL",
    "BRANCH_DISCOVERED",
}
_ALLOWED_TIERS = {"OFFICIAL_PUBLIC", "REPRODUCED_INTERNAL", "SYNTHETIC", "UNVERIFIED"}


def load_json(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise InventoryError("root must be an object")
    return value


def _unique_nonempty(values: list[str], label: str) -> None:
    if any(not isinstance(value, str) or not value.strip() for value in values):
        raise InventoryError(f"{label} contains an empty/non-string value")
    if len(values) != len(set(values)):
        raise InventoryError(f"{label} contains duplicates")


def validate_generation_inventory(payload: dict[str, Any]) -> None:
    if payload.get("schema") != "nexus.generation-inventory/v1":
        raise InventoryError("unexpected generation inventory schema")
    if payload.get("source_repository") != "Shtenco/agi_olga":
        raise InventoryError("v1 inventory must point at the preserved source lineage")
    generations = payload.get("generations")
    if not isinstance(generations, list) or not generations:
        raise InventoryError("generations must be a non-empty list")
    ids = [entry.get("id") for entry in generations]
    refs = [entry.get("source_ref") for entry in generations]
    _unique_nonempty(ids, "generation ids")
    _unique_nonempty(refs, "source refs")
    for entry in generations:
        if set(entry) != {"id", "source_ref", "status", "evidence", "evidence_paths"}:
            raise InventoryError(f"unexpected generation shape: {entry.get('id')}")
        if entry["status"] not in _ALLOWED_GENERATION_STATUS:
            raise InventoryError(f"invalid generation status: {entry['id']}")
        if entry["evidence"] not in _ALLOWED_EVIDENCE:
            raise InventoryError(f"invalid generation evidence: {entry['id']}")
        paths = entry["evidence_paths"]
        if not isinstance(paths, list) or any(not isinstance(path, str) or not path for path in paths):
            raise InventoryError(f"invalid evidence_paths: {entry['id']}")
        if entry["evidence"] == "REPRODUCED_INTERNAL" and not paths:
            raise InventoryError(f"reproduced generation without evidence paths: {entry['id']}")
        if entry["evidence"] == "BRANCH_DISCOVERED" and paths:
            raise InventoryError(f"branch-only evidence must not masquerade as artifacts: {entry['id']}")
    rules = payload.get("rules")
    required_rules = {
        "larger_version_is_not_better_by_default",
        "branch_name_is_not_benchmark_evidence",
        "official_private_score_requires_official_evidence",
        "migration_requires_reproducible_artifact",
    }
    if not isinstance(rules, dict) or set(rules) != required_rules or not all(rules.values()):
        raise InventoryError("all generation safety rules must be explicitly enabled")


def validate_benchmark_registry(payload: dict[str, Any]) -> None:
    if payload.get("schema") != "nexus.benchmark-registry/v1":
        raise InventoryError("unexpected benchmark registry schema")
    tiers = payload.get("claim_tiers")
    if set(tiers or []) != _ALLOWED_TIERS:
        raise InventoryError("claim tier set drifted")
    benchmarks = payload.get("benchmarks")
    if not isinstance(benchmarks, list) or not benchmarks:
        raise InventoryError("benchmarks must be a non-empty list")
    ids = [entry.get("id") for entry in benchmarks]
    _unique_nonempty(ids, "benchmark ids")
    for entry in benchmarks:
        if set(entry) != {"id", "family", "tier", "official_private", "required_artifacts"}:
            raise InventoryError(f"unexpected benchmark shape: {entry.get('id')}")
        if entry["tier"] not in _ALLOWED_TIERS:
            raise InventoryError(f"unknown claim tier: {entry['id']}")
        if entry["official_private"] is not False:
            raise InventoryError("v1 registry contains no verified official-private benchmark")
        artifacts = entry["required_artifacts"]
        if not isinstance(artifacts, list) or not artifacts:
            raise InventoryError(f"benchmark lacks required artifacts: {entry['id']}")
        _unique_nonempty(artifacts, f"required artifacts for {entry['id']}")
        if entry["tier"] == "OFFICIAL_PUBLIC" and "raw_results" not in artifacts:
            raise InventoryError(f"official-public benchmark must retain raw results: {entry['id']}")
    prohibited = payload.get("prohibited_claims")
    if not isinstance(prohibited, list) or len(prohibited) < 4:
        raise InventoryError("prohibited claim policy is incomplete")

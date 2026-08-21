from __future__ import annotations

import json
from pathlib import Path
import shutil

import pytest

from agi_nexus.service_build_recipe_v1 import (
    EXPECTED_RECIPE_DIGEST,
    ServiceBuildError,
    build_service_archive,
    verify_recipe,
    verify_source_tree,
)


ROOT = Path(__file__).resolve().parents[1]
RECIPE_PATH = ROOT / "config" / "smallworld_service_build_recipe_v1.json"


def _recipe() -> dict:
    return json.loads(RECIPE_PATH.read_text(encoding="utf-8"))


def test_recipe_is_exact_and_dependency_lock_remains_blocking() -> None:
    recipe = verify_recipe(_recipe())
    assert recipe["recipe_digest"] == EXPECTED_RECIPE_DIGEST
    assert recipe["dependency_lock_status"] == "RANGE_ONLY_BLOCKS_BUILD_VERIFICATION"
    assert recipe["execution_authority"] == "NONE"


def test_current_service_source_matches_frozen_blob_identities() -> None:
    files = verify_source_tree(ROOT, _recipe())
    assert [item.path for item in files] == [item["path"] for item in _recipe()["include_files"]]
    assert all(item.size > 0 for item in files)


def test_two_builds_are_byte_identical(tmp_path: Path) -> None:
    first = tmp_path / "first.zip"
    second = tmp_path / "second.zip"
    e1 = build_service_archive(ROOT, _recipe(), first)
    e2 = build_service_archive(ROOT, _recipe(), second)
    assert first.read_bytes() == second.read_bytes()
    assert e1 == e2
    assert e1["build_status"] == "ARTIFACT_BUILT_DEPENDENCY_LOCK_AND_TEST_EVIDENCE_PENDING"
    assert e1["test_evidence_status"] == "NOT_ATTESTED"
    assert e1["execution_authority"] == "NONE"


def test_source_tamper_is_rejected_even_if_recipe_is_unchanged(tmp_path: Path) -> None:
    shadow = tmp_path / "repo"
    for item in _recipe()["include_files"]:
        src = ROOT / item["path"]
        dst = shadow / item["path"]
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
    target = shadow / "src" / "agi_nexus" / "smallworld_v1.py"
    target.write_bytes(target.read_bytes() + b"\n# tamper\n")
    with pytest.raises(ServiceBuildError, match="source blob drift"):
        verify_source_tree(shadow, _recipe())


def test_fresh_hash_cannot_remove_dependency_lock_blocker() -> None:
    recipe = _recipe()
    recipe["dependency_lock_status"] = "LOCKED"
    recipe["recipe_digest"] = "0" * 64
    with pytest.raises(ServiceBuildError):
        verify_recipe(recipe)

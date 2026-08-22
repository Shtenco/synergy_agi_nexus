from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

import pytest

from agi_nexus.service_build_recipe_v2 import (
    FIXED_ZIP_TIME,
    ServiceBuildV2Error,
    build_service_archive_v2,
    canonical_json,
    verify_build_evidence_v2,
    verify_recipe_v2,
)


ROOT = Path(__file__).resolve().parents[1]
RECIPE_PATH = ROOT / "config" / "smallworld_exact_build_recipe_v2.json"
FIXTURE_PATH = ROOT / "fixtures" / "smallworld_exact_v2" / "canonical_8node_response.json"
EXPECTED_ARCHIVE_PATHS = [
    "agi_nexus/__init__.py",
    "agi_nexus/compute_service_v2.py",
    "agi_nexus/inventory.py",
    "agi_nexus/smallworld_exact_v2.py",
    "service_descriptor.json",
]


def _recipe() -> dict:
    return json.loads(RECIPE_PATH.read_text(encoding="utf-8"))


def _digest_without(payload: dict, field: str) -> str:
    body = dict(payload)
    body.pop(field, None)
    return hashlib.sha256(canonical_json(body)).hexdigest()


def test_recipe_is_frozen_stdlib_only_and_non_executing() -> None:
    recipe = _recipe()
    assert verify_recipe_v2(recipe) == recipe
    assert recipe["recipe_digest"] == "3e255804dbd420492fc5481fe11d6333be2a50c8834bd4a8e3896de726f44089"
    assert recipe["dependency_contract"] == "PYTHON_STDLIB_ONLY"
    assert recipe["dependency_lock_status"] == "STDLIB_ONLY_NO_THIRD_PARTY_RUNTIME_DEPENDENCIES"
    assert recipe["execution_authority"] == "NONE"
    assert [item["archive_path"] for item in recipe["include_files"]] == EXPECTED_ARCHIVE_PATHS


def test_repeated_builds_are_byte_identical_and_evidence_identical(tmp_path: Path) -> None:
    recipe = _recipe()
    first = tmp_path / "first.zip"
    second = tmp_path / "second.zip"
    evidence_first = build_service_archive_v2(ROOT, recipe, first)
    evidence_second = build_service_archive_v2(ROOT, recipe, second)

    assert first.read_bytes() == second.read_bytes()
    assert evidence_first == evidence_second
    assert evidence_first["artifact_sha256"] == hashlib.sha256(first.read_bytes()).hexdigest()
    assert evidence_first["test_evidence_status"] == "NOT_ATTESTED"
    assert evidence_first["build_status"] == "ARTIFACT_BUILT_TEST_EVIDENCE_PENDING"
    assert evidence_first["execution_authority"] == "NONE"
    assert verify_build_evidence_v2(evidence_first, recipe, artifact_bytes=first.read_bytes()) == evidence_first


def test_archive_layout_metadata_and_file_evidence_are_exact(tmp_path: Path) -> None:
    recipe = _recipe()
    output = tmp_path / "service.zip"
    evidence = build_service_archive_v2(ROOT, recipe, output)

    with zipfile.ZipFile(output, "r") as archive:
        infos = archive.infolist()
        assert [item.filename for item in infos] == EXPECTED_ARCHIVE_PATHS
        for info, file_evidence in zip(infos, evidence["files"], strict=True):
            assert info.date_time == FIXED_ZIP_TIME
            assert info.compress_type == zipfile.ZIP_STORED
            assert info.create_system == 3
            assert ((info.external_attr >> 16) & 0o777) == 0o644
            assert info.extra == b""
            assert info.comment == b""
            raw = archive.read(info.filename)
            assert len(raw) == file_evidence["size"]
            assert hashlib.sha256(raw).hexdigest() == file_evidence["sha256"]


def test_built_artifact_runs_exact_service_from_extracted_root(tmp_path: Path) -> None:
    recipe = _recipe()
    output = tmp_path / "service.zip"
    evidence = build_service_archive_v2(ROOT, recipe, output)
    verify_build_evidence_v2(evidence, recipe, artifact_bytes=output.read_bytes())

    extracted = tmp_path / "extracted"
    extracted.mkdir()
    with zipfile.ZipFile(output, "r") as archive:
        archive.extractall(extracted)

    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    request_line = json.dumps(
        fixture["request"], ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8") + b"\n"
    completed = subprocess.run(
        [sys.executable, "-m", "agi_nexus.compute_service_v2"],
        cwd=extracted,
        input=request_line,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=10,
    )
    assert completed.returncode == 0, completed.stderr.decode("utf-8", errors="replace")
    lines = completed.stdout.splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0].decode("utf-8")) == fixture["response"]


def test_builder_cannot_self_promote_to_build_verified_even_with_fresh_digest(tmp_path: Path) -> None:
    recipe = _recipe()
    output = tmp_path / "service.zip"
    evidence = build_service_archive_v2(ROOT, recipe, output)

    tampered = dict(evidence)
    tampered["test_evidence_status"] = "PASSED"
    tampered["build_status"] = "BUILD_VERIFIED"
    tampered["evidence_digest"] = _digest_without(tampered, "evidence_digest")
    with pytest.raises(ServiceBuildV2Error):
        verify_build_evidence_v2(tampered, recipe, artifact_bytes=output.read_bytes())


def test_file_evidence_tamper_with_fresh_outer_digest_is_rejected(tmp_path: Path) -> None:
    recipe = _recipe()
    output = tmp_path / "service.zip"
    evidence = build_service_archive_v2(ROOT, recipe, output)

    tampered = json.loads(json.dumps(evidence))
    tampered["files"][0]["sha256"] = "0" * 64
    tampered["evidence_digest"] = _digest_without(tampered, "evidence_digest")
    with pytest.raises(ServiceBuildV2Error):
        verify_build_evidence_v2(tampered, recipe, artifact_bytes=output.read_bytes())


def test_source_blob_drift_fails_before_build(tmp_path: Path) -> None:
    recipe = _recipe()
    for item in recipe["include_files"]:
        source = ROOT / item["source_path"]
        target = tmp_path / item["source_path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    target = tmp_path / recipe["include_files"][0]["source_path"]
    target.write_bytes(target.read_bytes() + b"\n# tamper\n")

    with pytest.raises(ServiceBuildV2Error):
        build_service_archive_v2(tmp_path, recipe, tmp_path / "bad.zip")


def test_unsafe_or_duplicate_archive_paths_fail_closed() -> None:
    recipe = _recipe()
    tampered = json.loads(json.dumps(recipe))
    tampered["include_files"][0]["archive_path"] = "../escape.py"
    with pytest.raises(ServiceBuildV2Error):
        verify_recipe_v2(tampered)

    tampered = json.loads(json.dumps(recipe))
    tampered["include_files"][1]["archive_path"] = tampered["include_files"][0]["archive_path"]
    with pytest.raises(ServiceBuildV2Error):
        verify_recipe_v2(tampered)

import importlib.util
import json
from pathlib import Path
import shutil
import zipfile
import io

import pytest

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "build_source_capsule_v1.py"
spec = importlib.util.spec_from_file_location("nexus_source_capsule_v1", TOOL)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)


def test_recipe_is_fixed_non_executable_and_dependency_range_is_disclosed():
    recipe = module.load_and_verify_recipe(ROOT)
    assert recipe["recipe_digest"] == "a75b05124ed358960a5313b34be38434564f5bcd40db102104516a58a89ccbd9"
    assert recipe["artifact_kind"] == "NON_EXECUTABLE_DETERMINISTIC_SOURCE_CAPSULE"
    assert recipe["dependency_lock_status"] == "RANGE_NOT_RUNTIME_LOCKED"
    assert recipe["build_evidence_status"] == "NOT_EXECUTED"
    assert recipe["execution_authority"] == "NONE"


def test_two_builds_are_byte_identical_and_self_verify():
    first, first_manifest = module.build_capsule_bytes(ROOT)
    second, second_manifest = module.build_capsule_bytes(ROOT)
    assert first == second
    assert first_manifest == second_manifest
    verified = module.verify_capsule_bytes(first)
    assert verified == first_manifest


def test_zip_entries_are_sorted_stored_and_fixed_timestamp():
    capsule, manifest = module.build_capsule_bytes(ROOT)
    with zipfile.ZipFile(io.BytesIO(capsule), "r") as archive:
        infos = archive.infolist()
        names = [info.filename for info in infos]
        assert names == sorted(names)
        assert names[0] == "CAPSULE_MANIFEST.json"
        assert all(info.date_time == module.FIXED_ZIP_DATETIME for info in infos)
        assert all(info.compress_type == zipfile.ZIP_STORED for info in infos)
        source_names = {record["path"] for record in manifest["files"]}
        assert source_names | {"CAPSULE_MANIFEST.json"} == set(names)


def test_manifest_hashes_every_source_byte_exactly():
    capsule, manifest = module.build_capsule_bytes(ROOT)
    with zipfile.ZipFile(io.BytesIO(capsule), "r") as archive:
        for record in manifest["files"]:
            data = archive.read(record["path"])
            assert len(data) == record["bytes"]
            assert module._sha256(data) == record["sha256"]
            assert data == (ROOT / record["path"]).read_bytes()


def test_path_traversal_and_absolute_paths_are_rejected():
    for value in ("../secret", "/tmp/secret", "a/../../secret", "a\\b"):
        with pytest.raises(module.CapsuleBuildError):
            module._validate_relative_path(value)


def test_symlink_source_is_rejected(tmp_path):
    recipe = module.load_and_verify_recipe(ROOT)
    for relative in recipe["source_paths"]:
        destination = tmp_path / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, destination)
    outside = tmp_path / "outside.txt"
    outside.write_text("not part of capsule", encoding="utf-8")
    dependency = tmp_path / "requirements-smallworld-v1.txt"
    dependency.unlink()
    try:
        dependency.symlink_to(outside)
    except (OSError, NotImplementedError):
        pytest.skip("symlink creation unavailable")
    with pytest.raises(module.CapsuleBuildError, match="symlink source forbidden"):
        module.build_capsule_bytes(tmp_path)


def test_fresh_recipe_hash_cannot_claim_executable_or_locked_runtime(tmp_path):
    recipe = json.loads((ROOT / "config/nexus_source_capsule_recipe_v1.json").read_text(encoding="utf-8"))
    recipe["artifact_kind"] = "EXECUTABLE"
    recipe["dependency_lock_status"] = "FULLY_LOCKED"
    recipe["execution_authority"] = "RUN"
    recipe["recipe_digest"] = module._recipe_digest(recipe)
    target = tmp_path / "config/nexus_source_capsule_recipe_v1.json"
    target.parent.mkdir(parents=True)
    target.write_text(json.dumps(recipe), encoding="utf-8")
    with pytest.raises(module.CapsuleBuildError):
        module.load_and_verify_recipe(tmp_path)

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path, PurePosixPath
import zipfile
from typing import Any


class ServiceBuildV2Error(ValueError):
    pass


EXPECTED_RECIPE_DIGEST = "3e255804dbd420492fc5481fe11d6333be2a50c8834bd4a8e3896de726f44089"
EXPECTED_SOURCE_COMMIT = "2ee8f2a29ad2497afca6c7386375a296cd0bdbcf"
FIXED_ZIP_TIME = (1980, 1, 1, 0, 0, 0)


def canonical_json(value: Any) -> bytes:
    def check(item: Any) -> None:
        if item is None or isinstance(item, (str, bool)):
            return
        if isinstance(item, int) and not isinstance(item, bool):
            if abs(item) > 2**53 - 1:
                raise ServiceBuildV2Error("unsafe integer")
            return
        if isinstance(item, float):
            raise ServiceBuildV2Error("floats forbidden")
        if isinstance(item, list):
            for child in item:
                check(child)
            return
        if isinstance(item, dict):
            if any(not isinstance(key, str) for key in item):
                raise ServiceBuildV2Error("object keys must be strings")
            for child in item.values():
                check(child)
            return
        raise ServiceBuildV2Error(f"unsupported canonical value: {type(item)!r}")

    check(value)
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _digest_without(payload: dict[str, Any], field: str) -> str:
    body = dict(payload)
    body.pop(field, None)
    return hashlib.sha256(canonical_json(body)).hexdigest()


def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def _safe_relpath(value: str, label: str) -> PurePosixPath:
    if not isinstance(value, str) or not value:
        raise ServiceBuildV2Error(f"empty {label}")
    path = PurePosixPath(value)
    if path.is_absolute() or "." in path.parts or ".." in path.parts:
        raise ServiceBuildV2Error(f"unsafe {label}")
    return path


def verify_recipe_v2(payload: dict[str, Any]) -> dict[str, Any]:
    expected = {
        "schema", "recipe_id", "source_repository", "source_commit",
        "service_descriptor_source_path", "runtime_entrypoint", "include_files",
        "archive_profile", "dependency_contract", "dependency_lock_status",
        "artifact_semantics", "numeric_semantics", "build_authority",
        "execution_authority", "recipe_digest",
    }
    if not isinstance(payload, dict) or set(payload) != expected:
        raise ServiceBuildV2Error("unexpected recipe shape")
    if payload["schema"] != "nexus.service-build-recipe/v2":
        raise ServiceBuildV2Error("unexpected recipe schema")
    if payload["recipe_id"] != "NEXUS_SMALLWORLD_EXACT_STDLIB_BUILD_RECIPE_V2":
        raise ServiceBuildV2Error("unexpected recipe id")
    if payload["source_repository"] != "Shtenco/agi_nexus" or payload["source_commit"] != EXPECTED_SOURCE_COMMIT:
        raise ServiceBuildV2Error("source identity drift")
    if payload["service_descriptor_source_path"] != "config/smallworld_compute_service_v2.json":
        raise ServiceBuildV2Error("service descriptor drift")
    if payload["runtime_entrypoint"] != {
        "kind": "PYTHON_MODULE",
        "pythonpath": ".",
        "module": "agi_nexus.compute_service_v2",
    }:
        raise ServiceBuildV2Error("runtime entrypoint drift")
    if payload["dependency_contract"] != "PYTHON_STDLIB_ONLY":
        raise ServiceBuildV2Error("unexpected dependency contract")
    if payload["dependency_lock_status"] != "STDLIB_ONLY_NO_THIRD_PARTY_RUNTIME_DEPENDENCIES":
        raise ServiceBuildV2Error("unexpected dependency lock status")
    if payload["artifact_semantics"] != "EXECUTABLE_SOURCE_PACKAGE_CANDIDATE":
        raise ServiceBuildV2Error("artifact semantics drift")
    if payload["numeric_semantics"] != "EXACT_RATIONAL_METROPOLIS_V2":
        raise ServiceBuildV2Error("numeric semantics drift")
    if payload["build_authority"] != "SOURCE_REPOSITORY_ONLY" or payload["execution_authority"] != "NONE":
        raise ServiceBuildV2Error("forbidden authority")
    if payload["archive_profile"] != {
        "format": "ZIP_STORED",
        "entry_order": "LEXICOGRAPHIC_ARCHIVE_PATH",
        "fixed_timestamp": "1980-01-01T00:00:00Z",
        "file_mode": "0644",
        "strip_extra_fields": True,
    }:
        raise ServiceBuildV2Error("archive profile drift")

    files = payload["include_files"]
    if not isinstance(files, list) or not files:
        raise ServiceBuildV2Error("include_files required")
    source_paths: list[str] = []
    archive_paths: list[str] = []
    descriptor_archive_path: str | None = None
    for item in files:
        if not isinstance(item, dict) or set(item) != {"source_path", "archive_path", "git_blob_sha"}:
            raise ServiceBuildV2Error("unexpected include-file shape")
        source_path = str(_safe_relpath(item["source_path"], "source_path"))
        archive_path = str(_safe_relpath(item["archive_path"], "archive_path"))
        sha = item["git_blob_sha"]
        if not isinstance(sha, str) or len(sha) != 40 or sha.lower() != sha:
            raise ServiceBuildV2Error("git blob sha must be lowercase sha1")
        try:
            int(sha, 16)
        except ValueError as exc:
            raise ServiceBuildV2Error("git blob sha must be hex") from exc
        source_paths.append(source_path)
        archive_paths.append(archive_path)
        if source_path == payload["service_descriptor_source_path"]:
            descriptor_archive_path = archive_path

    if archive_paths != sorted(archive_paths) or len(archive_paths) != len(set(archive_paths)):
        raise ServiceBuildV2Error("include_files must be sorted by unique archive_path")
    if len(source_paths) != len(set(source_paths)):
        raise ServiceBuildV2Error("source paths must be unique")
    if descriptor_archive_path != "service_descriptor.json":
        raise ServiceBuildV2Error("descriptor must map to service_descriptor.json")
    if _digest_without(payload, "recipe_digest") != payload["recipe_digest"]:
        raise ServiceBuildV2Error("recipe digest mismatch")
    if payload["recipe_digest"] != EXPECTED_RECIPE_DIGEST:
        raise ServiceBuildV2Error("unexpected canonical recipe generation")
    canonical_json(payload)
    return payload


@dataclass(frozen=True)
class VerifiedSourceFileV2:
    source_path: str
    archive_path: str
    size: int
    sha256: str
    git_blob_sha: str
    data: bytes


def verify_source_tree_v2(root: Path, recipe: dict[str, Any]) -> tuple[VerifiedSourceFileV2, ...]:
    verify_recipe_v2(recipe)
    root = root.resolve()
    verified: list[VerifiedSourceFileV2] = []
    for item in recipe["include_files"]:
        source_rel = _safe_relpath(item["source_path"], "source_path")
        archive_rel = _safe_relpath(item["archive_path"], "archive_path")
        candidate = root.joinpath(*source_rel.parts)
        if candidate.is_symlink() or not candidate.is_file():
            raise ServiceBuildV2Error(f"missing or unsafe source file: {source_rel}")
        resolved = candidate.resolve()
        try:
            resolved.relative_to(root)
        except ValueError as exc:
            raise ServiceBuildV2Error(f"source path escapes build root: {source_rel}") from exc
        data = resolved.read_bytes()
        blob = git_blob_sha(data)
        if blob != item["git_blob_sha"]:
            raise ServiceBuildV2Error(f"source blob drift: {source_rel}")
        verified.append(
            VerifiedSourceFileV2(
                source_path=str(source_rel),
                archive_path=str(archive_rel),
                size=len(data),
                sha256=hashlib.sha256(data).hexdigest(),
                git_blob_sha=blob,
                data=data,
            )
        )
    return tuple(verified)


def build_service_archive_v2(root: Path, recipe: dict[str, Any], output: Path) -> dict[str, Any]:
    files = verify_source_tree_v2(root, recipe)
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_STORED, strict_timestamps=True) as archive:
        for item in files:
            info = zipfile.ZipInfo(item.archive_path, date_time=FIXED_ZIP_TIME)
            info.create_system = 3
            info.compress_type = zipfile.ZIP_STORED
            info.external_attr = 0o100644 << 16
            info.extra = b""
            info.comment = b""
            archive.writestr(info, item.data)

    artifact = output.read_bytes()
    evidence: dict[str, Any] = {
        "schema": "nexus.service-build-artifact/v2",
        "recipe_digest": recipe["recipe_digest"],
        "source_repository": recipe["source_repository"],
        "source_commit": recipe["source_commit"],
        "runtime_entrypoint": recipe["runtime_entrypoint"],
        "artifact_sha256": hashlib.sha256(artifact).hexdigest(),
        "artifact_bytes": len(artifact),
        "files": [
            {
                "source_path": item.source_path,
                "archive_path": item.archive_path,
                "size": item.size,
                "sha256": item.sha256,
                "git_blob_sha": item.git_blob_sha,
            }
            for item in files
        ],
        "dependency_lock_status": recipe["dependency_lock_status"],
        "numeric_semantics": recipe["numeric_semantics"],
        "test_evidence_status": "NOT_ATTESTED",
        "build_status": "ARTIFACT_BUILT_TEST_EVIDENCE_PENDING",
        "execution_authority": "NONE",
    }
    evidence["evidence_digest"] = hashlib.sha256(canonical_json(evidence)).hexdigest()
    return evidence


def verify_build_evidence_v2(
    payload: dict[str, Any],
    recipe: dict[str, Any],
    *,
    artifact_bytes: bytes | None = None,
) -> dict[str, Any]:
    verify_recipe_v2(recipe)
    expected = {
        "schema", "recipe_digest", "source_repository", "source_commit", "runtime_entrypoint",
        "artifact_sha256", "artifact_bytes", "files", "dependency_lock_status", "numeric_semantics",
        "test_evidence_status", "build_status", "execution_authority", "evidence_digest",
    }
    if not isinstance(payload, dict) or set(payload) != expected:
        raise ServiceBuildV2Error("unexpected build evidence shape")
    if payload["schema"] != "nexus.service-build-artifact/v2":
        raise ServiceBuildV2Error("unexpected build evidence schema")
    for field in ("recipe_digest", "source_repository", "source_commit", "runtime_entrypoint", "dependency_lock_status", "numeric_semantics"):
        expected_value = recipe[field]
        if payload[field] != expected_value:
            raise ServiceBuildV2Error(f"build evidence drift: {field}")
    if payload["test_evidence_status"] != "NOT_ATTESTED":
        raise ServiceBuildV2Error("v2 builder does not attest tests")
    if payload["build_status"] != "ARTIFACT_BUILT_TEST_EVIDENCE_PENDING":
        raise ServiceBuildV2Error("v2 builder cannot claim BUILD_VERIFIED")
    if payload["execution_authority"] != "NONE":
        raise ServiceBuildV2Error("build evidence grants forbidden execution authority")
    artifact_sha = payload["artifact_sha256"]
    if not isinstance(artifact_sha, str) or len(artifact_sha) != 64 or artifact_sha.lower() != artifact_sha:
        raise ServiceBuildV2Error("invalid artifact sha256")
    try:
        int(artifact_sha, 16)
    except ValueError as exc:
        raise ServiceBuildV2Error("artifact sha256 must be hex") from exc
    if isinstance(payload["artifact_bytes"], bool) or not isinstance(payload["artifact_bytes"], int) or payload["artifact_bytes"] <= 0:
        raise ServiceBuildV2Error("artifact_bytes must be positive integer")
    if not isinstance(payload["files"], list) or len(payload["files"]) != len(recipe["include_files"]):
        raise ServiceBuildV2Error("build evidence file set drift")
    if _digest_without(payload, "evidence_digest") != payload["evidence_digest"]:
        raise ServiceBuildV2Error("build evidence digest mismatch")
    if artifact_bytes is not None:
        if len(artifact_bytes) != payload["artifact_bytes"] or hashlib.sha256(artifact_bytes).hexdigest() != artifact_sha:
            raise ServiceBuildV2Error("artifact bytes do not match build evidence")
    canonical_json(payload)
    return payload

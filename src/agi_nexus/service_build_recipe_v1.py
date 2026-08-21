from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path, PurePosixPath
import zipfile
from typing import Any


class ServiceBuildError(ValueError):
    pass


EXPECTED_RECIPE_DIGEST = "6ec5a878dadf7794f673ef21688e1e0e29d88b534a5f9ac304ee32103b5eb21a"
EXPECTED_SOURCE_COMMIT = "ef1a6e3675e53fda4bf91566aec61f1b62fa9336"
FIXED_ZIP_TIME = (1980, 1, 1, 0, 0, 0)


def canonical_json(value: Any) -> bytes:
    def check(v: Any) -> None:
        if v is None or isinstance(v, (str, bool)):
            return
        if isinstance(v, int) and not isinstance(v, bool):
            if abs(v) > 2**53 - 1:
                raise ServiceBuildError("unsafe integer")
            return
        if isinstance(v, float):
            raise ServiceBuildError("floats are forbidden")
        if isinstance(v, list):
            for item in v:
                check(item)
            return
        if isinstance(v, dict):
            if any(not isinstance(k, str) for k in v):
                raise ServiceBuildError("object keys must be strings")
            for item in v.values():
                check(item)
            return
        raise ServiceBuildError(f"unsupported value: {type(v)!r}")

    check(value)
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _digest_without(payload: dict[str, Any], field: str) -> str:
    body = dict(payload)
    body.pop(field, None)
    return hashlib.sha256(canonical_json(body)).hexdigest()


def git_blob_sha(data: bytes) -> str:
    prefix = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(prefix + data).hexdigest()


def _safe_relpath(value: str) -> PurePosixPath:
    if not isinstance(value, str) or not value:
        raise ServiceBuildError("empty build path")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or "." in path.parts:
        raise ServiceBuildError("unsafe build path")
    return path


def verify_recipe(payload: dict[str, Any]) -> dict[str, Any]:
    expected = {
        "schema", "recipe_id", "source_repository", "source_commit",
        "service_descriptor_path", "include_files", "archive_profile",
        "dependency_contract", "dependency_lock_status", "artifact_semantics",
        "build_authority", "execution_authority", "recipe_digest",
    }
    if not isinstance(payload, dict) or set(payload) != expected:
        raise ServiceBuildError("unexpected recipe shape")
    if payload["schema"] != "nexus.service-build-recipe/v1":
        raise ServiceBuildError("unexpected recipe schema")
    if payload["source_repository"] != "Shtenco/agi_nexus":
        raise ServiceBuildError("unexpected source repository")
    if payload["source_commit"] != EXPECTED_SOURCE_COMMIT:
        raise ServiceBuildError("source commit drift")
    if payload["service_descriptor_path"] != "config/smallworld_compute_service_v1.json":
        raise ServiceBuildError("service descriptor drift")
    if payload["dependency_lock_status"] != "RANGE_ONLY_BLOCKS_BUILD_VERIFICATION":
        raise ServiceBuildError("v1 must remain dependency-range blocked")
    if payload["artifact_semantics"] != "EXECUTABLE_SOURCE_PACKAGE_CANDIDATE":
        raise ServiceBuildError("unexpected artifact semantics")
    if payload["build_authority"] != "SOURCE_REPOSITORY_ONLY" or payload["execution_authority"] != "NONE":
        raise ServiceBuildError("recipe grants forbidden authority")
    profile = payload["archive_profile"]
    required_profile = {
        "format": "ZIP_STORED",
        "entry_order": "LEXICOGRAPHIC_PATH",
        "fixed_timestamp": "1980-01-01T00:00:00Z",
        "file_mode": "0644",
        "strip_extra_fields": True,
    }
    if profile != required_profile:
        raise ServiceBuildError("archive profile drift")
    files = payload["include_files"]
    if not isinstance(files, list) or not files:
        raise ServiceBuildError("include_files required")
    paths: list[str] = []
    for item in files:
        if not isinstance(item, dict) or set(item) != {"path", "git_blob_sha"}:
            raise ServiceBuildError("unexpected include file shape")
        path = str(_safe_relpath(item["path"]))
        sha = item["git_blob_sha"]
        if not isinstance(sha, str) or len(sha) != 40 or sha.lower() != sha:
            raise ServiceBuildError("git blob sha must be lowercase sha1")
        try:
            int(sha, 16)
        except ValueError as exc:
            raise ServiceBuildError("git blob sha must be hex") from exc
        paths.append(path)
    if paths != sorted(paths) or len(paths) != len(set(paths)):
        raise ServiceBuildError("include_files must be sorted and unique")
    if payload["service_descriptor_path"] not in set(paths):
        raise ServiceBuildError("service descriptor must be packaged")
    if _digest_without(payload, "recipe_digest") != payload["recipe_digest"]:
        raise ServiceBuildError("recipe digest mismatch")
    if payload["recipe_digest"] != EXPECTED_RECIPE_DIGEST:
        raise ServiceBuildError("unexpected canonical recipe generation")
    canonical_json(payload)
    return payload


@dataclass(frozen=True)
class VerifiedSourceFile:
    path: str
    size: int
    sha256: str
    git_blob_sha: str
    data: bytes


def verify_source_tree(root: Path, recipe: dict[str, Any]) -> tuple[VerifiedSourceFile, ...]:
    verify_recipe(recipe)
    root = root.resolve()
    verified: list[VerifiedSourceFile] = []
    for item in recipe["include_files"]:
        rel = _safe_relpath(item["path"])
        candidate = root.joinpath(*rel.parts)
        if candidate.is_symlink():
            raise ServiceBuildError(f"symlink forbidden: {rel}")
        if not candidate.is_file():
            raise ServiceBuildError(f"missing regular file: {rel}")
        resolved = candidate.resolve()
        try:
            resolved.relative_to(root)
        except ValueError as exc:
            raise ServiceBuildError(f"path escapes build root: {rel}") from exc
        data = resolved.read_bytes()
        blob = git_blob_sha(data)
        if blob != item["git_blob_sha"]:
            raise ServiceBuildError(f"source blob drift: {rel}")
        verified.append(
            VerifiedSourceFile(
                path=str(rel),
                size=len(data),
                sha256=hashlib.sha256(data).hexdigest(),
                git_blob_sha=blob,
                data=data,
            )
        )
    return tuple(verified)


def build_service_archive(root: Path, recipe: dict[str, Any], output: Path) -> dict[str, Any]:
    files = verify_source_tree(root, recipe)
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_STORED, strict_timestamps=True) as zf:
        for item in files:
            info = zipfile.ZipInfo(item.path, date_time=FIXED_ZIP_TIME)
            info.create_system = 3
            info.compress_type = zipfile.ZIP_STORED
            info.external_attr = 0o100644 << 16
            info.extra = b""
            info.comment = b""
            zf.writestr(info, item.data)
    artifact = output.read_bytes()
    evidence = {
        "schema": "nexus.service-build-artifact/v1",
        "recipe_digest": recipe["recipe_digest"],
        "source_repository": recipe["source_repository"],
        "source_commit": recipe["source_commit"],
        "artifact_sha256": hashlib.sha256(artifact).hexdigest(),
        "artifact_bytes": len(artifact),
        "files": [
            {"path": f.path, "size": f.size, "sha256": f.sha256, "git_blob_sha": f.git_blob_sha}
            for f in files
        ],
        "dependency_lock_status": recipe["dependency_lock_status"],
        "test_evidence_status": "NOT_ATTESTED",
        "build_status": "ARTIFACT_BUILT_DEPENDENCY_LOCK_AND_TEST_EVIDENCE_PENDING",
        "execution_authority": "NONE",
    }
    evidence["evidence_digest"] = hashlib.sha256(canonical_json(evidence)).hexdigest()
    return evidence

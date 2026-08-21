from __future__ import annotations

import hashlib
import json
import re
from typing import Any


class BuildReadinessError(ValueError):
    pass


_HEX40 = re.compile(r"^[0-9a-f]{40}$")
_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_EXPECTED_DIGEST = "0e29504a9448c970fd5057123300000aca8c3d88e84f524bed2041cb881aec9a"
_EXPECTED_ARTIFACTS = [
    {"path":"requirements-smallworld-v1.txt","git_blob_sha":"726a10393c7435c8a28afb5b6c3335831d9441a2","role":"DEPENDENCY_RANGE"},
    {"path":"src/agi_nexus/smallworld_v1.py","git_blob_sha":"5354e07cc87fa992f445dc6400313816003a2c69","role":"RUNTIME_COMPONENT"},
]


def _canonical(value: Any) -> bytes:
    if isinstance(value, float):
        raise BuildReadinessError("floats forbidden")
    if isinstance(value, int) and not isinstance(value, bool) and abs(value) > 2**53 - 1:
        raise BuildReadinessError("unsafe integer")
    if isinstance(value, list):
        for item in value:
            _canonical(item)
    elif isinstance(value, dict):
        if any(not isinstance(k, str) for k in value):
            raise BuildReadinessError("keys must be strings")
        for item in value.values():
            _canonical(item)
    elif value is not None and not isinstance(value, (str, bool, int)):
        raise BuildReadinessError("unsupported value")
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def readiness_digest(payload: dict[str, Any]) -> str:
    body = dict(payload)
    body.pop("readiness_digest", None)
    return hashlib.sha256(_canonical(body)).hexdigest()


def verify_smallworld_build_readiness(payload: dict[str, Any]) -> dict[str, Any]:
    expected = {"schema","component_id","source_repository","source_commit","source_ref","source_artifacts","artifact_kind","service_entrypoint","python_versions","dependency_lock_status","service_readiness","build_artifact_digest","execution_authority","readiness_digest"}
    if not isinstance(payload, dict) or set(payload) != expected:
        raise BuildReadinessError("unexpected build-readiness shape")
    if payload["schema"] != "nexus.build-readiness/v1" or payload["component_id"] != "NEXUS_SMALLWORLD_KERNEL_V1":
        raise BuildReadinessError("unexpected build-readiness identity")
    if payload["source_repository"] != "Shtenco/agi_nexus" or payload["source_commit"] != "cbc06e83f7f9e242719667e446a090894e11eef1":
        raise BuildReadinessError("source identity drifted")
    if not _HEX40.fullmatch(payload["source_commit"]):
        raise BuildReadinessError("source commit must be lowercase git sha")
    if payload["source_ref"] != "feat/smallworld-kernel-migration-v1-20260821":
        raise BuildReadinessError("source ref drifted")
    if payload["source_artifacts"] != _EXPECTED_ARTIFACTS:
        raise BuildReadinessError("source artifact identity drifted")
    for item in payload["source_artifacts"]:
        if not _HEX40.fullmatch(item["git_blob_sha"]):
            raise BuildReadinessError("git blob sha invalid")
    if payload["artifact_kind"] != "PYTHON_LIBRARY_COMPONENT" or payload["service_entrypoint"] is not None:
        raise BuildReadinessError("v1 must remain a non-service component")
    if payload["python_versions"] != ["3.11", "3.12"]:
        raise BuildReadinessError("python version contract drifted")
    if payload["dependency_lock_status"] != "RANGE_ONLY_NOT_REPRODUCIBLE_LOCK":
        raise BuildReadinessError("dependency lock status overclaims reproducibility")
    if payload["service_readiness"] != "COMPONENT_ONLY_NOT_NODE_SERVICE":
        raise BuildReadinessError("service readiness overclaims deployability")
    if payload["build_artifact_digest"] is not None:
        raise BuildReadinessError("unbuilt component cannot claim artifact digest")
    if payload["execution_authority"] != "NONE":
        raise BuildReadinessError("build-readiness artifact cannot execute")
    digest = payload["readiness_digest"]
    if not isinstance(digest, str) or not _HEX64.fullmatch(digest):
        raise BuildReadinessError("readiness digest invalid")
    if readiness_digest(payload) != digest or digest != _EXPECTED_DIGEST:
        raise BuildReadinessError("build-readiness digest mismatch")
    return payload

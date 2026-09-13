from __future__ import annotations

import hashlib
import json
from typing import Any


class ServiceSpecV2Error(ValueError):
    pass


_RUNTIME_SOURCE = "4915872c60117bbac0001a0f792f2a8f3a12899a"
_R710_FREEZE = "fc8a32bc949947a42ab5038de0a3e55fa9921e64"
_SPEC_DIGEST = "c01a22e4dbd5a1e4e6f2b9a3fbc9e49f559a43f1575cd4e6a6f4c22420f3121b"
_OPERATIONS = ["STATUS", "FORMAL_REASON", "SMALLWORLD_EXACT_DIGESTS", "CYBER_STEP"]


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def spec_digest(payload: dict[str, Any]) -> str:
    body = dict(payload)
    body.pop("spec_digest", None)
    return hashlib.sha256(_canonical(body)).hexdigest()


def verify_service_spec_v2(payload: dict[str, Any]) -> dict[str, Any]:
    expected = {
        "schema", "service_id", "kind", "repository", "runtime_source_commit", "r710_freeze_commit",
        "required_capabilities", "runtime_form", "entrypoint", "health_probe", "lifecycle_protocol",
        "wire_protocol", "operations", "interface_status", "neural_hypothesis_status",
        "build_artifact_digest", "build_evidence_digest", "execution_authority", "spec_digest",
    }
    if not isinstance(payload, dict) or set(payload) != expected:
        raise ServiceSpecV2Error("unexpected ServiceSpec shape")
    checks = {
        "schema": "synergy.service-spec/v2",
        "service_id": "nexus",
        "kind": "NEXUS",
        "repository": "Shtenco/agi_nexus",
        "runtime_source_commit": _RUNTIME_SOURCE,
        "r710_freeze_commit": _R710_FREEZE,
        "required_capabilities": ["NEXUS_COMPUTE"],
        "runtime_form": "PYTHON_STDLIB_SERVICE",
        "entrypoint": "python -m agi_nexus.nexus_service_v3",
        "health_probe": "STATUS_EXPECT_READY",
        "lifecycle_protocol": "STDIN_EOF_OR_SUPERVISOR_SIGNAL",
        "wire_protocol": "nexus.runtime-wire/v3",
        "operations": _OPERATIONS,
        "interface_status": "SERVICE_INTERFACE_IMPLEMENTED_SOURCE_ONLY",
        "neural_hypothesis_status": "NOT_MIGRATED_NOT_REQUIRED_FOR_EXACT_CORE",
        "build_artifact_digest": None,
        "build_evidence_digest": None,
        "execution_authority": "NONE",
    }
    for field, value in checks.items():
        if payload[field] != value:
            raise ServiceSpecV2Error(f"{field} drifted")
    recomputed = spec_digest(payload)
    if payload["spec_digest"] != recomputed or recomputed != _SPEC_DIGEST:
        raise ServiceSpecV2Error("ServiceSpec digest mismatch")
    return payload

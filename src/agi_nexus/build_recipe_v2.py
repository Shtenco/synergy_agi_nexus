from __future__ import annotations

import hashlib
import json
from typing import Any


class BuildRecipeV2Error(ValueError):
    pass


_SOURCE_COMMIT = "0cf581fe6ac6e79bcf39c9ed4833e2d5719ddd6f"
_SERVICE_SPEC_DIGEST = "c01a22e4dbd5a1e4e6f2b9a3fbc9e49f559a43f1575cd4e6a6f4c22420f3121b"
_RECIPE_DIGEST = "46e874b075c52ee81e4996c6ce3fc027078f54ad4c4824a869d92b597821fe90"


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def recipe_digest(payload: dict[str, Any]) -> str:
    body = dict(payload)
    body.pop("recipe_digest", None)
    return hashlib.sha256(_canonical(body)).hexdigest()


def verify_build_recipe_v2(payload: dict[str, Any]) -> dict[str, Any]:
    expected = {
        "schema", "recipe_id", "repository", "source_commit", "source_role", "service_spec_digest",
        "artifact_kind", "package_name", "package_version", "python_requires", "build_backend",
        "build_system_requirements", "runtime_requirements", "build_toolchain", "reproducibility_status",
        "artifact_digest", "build_evidence_digest", "execution_authority", "recipe_digest",
    }
    if not isinstance(payload, dict) or set(payload) != expected:
        raise BuildRecipeV2Error("unexpected BuildRecipe shape")
    checks = {
        "schema": "synergy.build-recipe/v2",
        "recipe_id": "AGI_NEXUS_PROOF_CORE_SOURCE_CANDIDATE_20260822",
        "repository": "Shtenco/agi_nexus",
        "source_commit": _SOURCE_COMMIT,
        "source_role": "NEXUS_PROOF_FIRST_MINIMAL_CORE_V3",
        "service_spec_digest": _SERVICE_SPEC_DIGEST,
        "artifact_kind": "PYTHON_WHEEL",
        "package_name": "agi-nexus",
        "package_version": "0.1.0",
        "python_requires": ">=3.11",
        "build_backend": "setuptools.build_meta",
        "build_system_requirements": ["setuptools>=68"],
        "runtime_requirements": [],
        "build_toolchain": {"status": "NOT_FROZEN", "lock_digest": None},
        "reproducibility_status": "NOT_REPRODUCIBLE_TOOLCHAIN_NOT_FROZEN",
        "artifact_digest": None,
        "build_evidence_digest": None,
        "execution_authority": "NONE",
    }
    for field, value in checks.items():
        if payload[field] != value:
            raise BuildRecipeV2Error(f"{field} drifted")
    recomputed = recipe_digest(payload)
    if payload["recipe_digest"] != recomputed or recomputed != _RECIPE_DIGEST:
        raise BuildRecipeV2Error("BuildRecipe digest mismatch")
    return payload

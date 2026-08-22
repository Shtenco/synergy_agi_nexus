from __future__ import annotations

import hashlib
import json
import re
from typing import Any


class BuildRecipeError(ValueError):
    pass


_SOURCE_COMMIT = "cbc06e83f7f9e242719667e446a090894e11eef1"
_RECIPE_DIGEST = "b262c98666843da80f37bcfae4d8b2105aa3b52b758a3a50406b198afc1a15be"
_HEX40 = re.compile(r"^[0-9a-f]{40}$")
_HEX64 = re.compile(r"^[0-9a-f]{64}$")


def _canonical(value: Any) -> bytes:
    def check(item: Any) -> None:
        if item is None or isinstance(item, (str, bool)):
            return
        if isinstance(item, int) and not isinstance(item, bool):
            if abs(item) > 2**53 - 1:
                raise BuildRecipeError("unsafe integer")
            return
        if isinstance(item, float):
            raise BuildRecipeError("floating point values are forbidden")
        if isinstance(item, list):
            for child in item:
                check(child)
            return
        if isinstance(item, dict):
            if any(not isinstance(key, str) for key in item):
                raise BuildRecipeError("object keys must be strings")
            for child in item.values():
                check(child)
            return
        raise BuildRecipeError("unsupported build-recipe value")

    check(value)
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def recipe_digest(payload: dict[str, Any]) -> str:
    body = dict(payload)
    body.pop("recipe_digest", None)
    return hashlib.sha256(_canonical(body)).hexdigest()


def verify_build_recipe_v1(payload: dict[str, Any]) -> dict[str, Any]:
    expected = {
        "schema", "recipe_id", "repository", "source_commit", "source_role",
        "artifact_kind", "package_name", "package_version", "python_requires",
        "build_backend", "build_system_requirements", "runtime_requirements",
        "build_toolchain", "reproducibility_status", "artifact_digest",
        "execution_authority", "recipe_digest",
    }
    if not isinstance(payload, dict) or set(payload) != expected:
        raise BuildRecipeError("unexpected build-recipe shape")
    if payload["schema"] != "synergy.build-recipe/v1":
        raise BuildRecipeError("unexpected build recipe schema")
    if payload["recipe_id"] != "AGI_NEXUS_SMALLWORLD_WHEEL_SOURCE_CANDIDATE_20260822":
        raise BuildRecipeError("unexpected recipe id")
    if payload["repository"] != "Shtenco/agi_nexus":
        raise BuildRecipeError("wrong repository")
    if payload["source_commit"] != _SOURCE_COMMIT or not _HEX40.fullmatch(payload["source_commit"]):
        raise BuildRecipeError("source commit drifted")
    if payload["source_role"] != "NEXUS_SMALLWORLD_KERNEL_CANDIDATE":
        raise BuildRecipeError("source role drifted")
    if payload["artifact_kind"] != "PYTHON_WHEEL":
        raise BuildRecipeError("unexpected artifact kind")
    if payload["package_name"] != "agi-nexus" or payload["package_version"] != "0.1.0":
        raise BuildRecipeError("package identity drifted")
    if payload["python_requires"] != ">=3.11":
        raise BuildRecipeError("python requirement drifted")
    if payload["build_backend"] != "setuptools.build_meta":
        raise BuildRecipeError("build backend drifted")
    if payload["build_system_requirements"] != ["setuptools>=68"]:
        raise BuildRecipeError("build-system requirements drifted")
    if payload["runtime_requirements"] != [{"requirement": "numpy>=1.26,<3", "locked": False}]:
        raise BuildRecipeError("runtime dependency disclosure drifted")
    if payload["build_toolchain"] != {"status": "NOT_FROZEN", "lock_digest": None}:
        raise BuildRecipeError("v1 must disclose an unfrozen build toolchain")
    if payload["reproducibility_status"] != "NOT_REPRODUCIBLE_TOOLCHAIN_NOT_FROZEN":
        raise BuildRecipeError("v1 cannot claim reproducible build status")
    if payload["artifact_digest"] is not None:
        raise BuildRecipeError("v1 cannot claim a built artifact digest")
    if payload["execution_authority"] != "NONE":
        raise BuildRecipeError("build recipe cannot grant execution authority")
    supplied = payload["recipe_digest"]
    if not isinstance(supplied, str) or not _HEX64.fullmatch(supplied):
        raise BuildRecipeError("invalid recipe digest")
    recomputed = recipe_digest(payload)
    if supplied != recomputed or recomputed != _RECIPE_DIGEST:
        raise BuildRecipeError("recipe digest mismatch")
    return payload

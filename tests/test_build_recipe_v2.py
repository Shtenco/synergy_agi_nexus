from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from agi_nexus.build_recipe_v2 import BuildRecipeV2Error, recipe_digest, verify_build_recipe_v2


ROOT = Path(__file__).resolve().parents[1]


def _recipe() -> dict:
    return json.loads((ROOT / "config/build_recipe_v2.json").read_text(encoding="utf-8"))


def test_recipe_binds_new_nexus_service_without_build_overclaim() -> None:
    recipe = _recipe()
    assert verify_build_recipe_v2(recipe) == recipe
    assert recipe["service_spec_digest"] == "c01a22e4dbd5a1e4e6f2b9a3fbc9e49f559a43f1575cd4e6a6f4c22420f3121b"
    assert recipe["runtime_requirements"] == []
    assert recipe["build_toolchain"] == {"status": "NOT_FROZEN", "lock_digest": None}
    assert recipe["artifact_digest"] is None
    assert recipe["build_evidence_digest"] is None


def test_fresh_hash_cannot_invent_frozen_toolchain_or_artifact() -> None:
    recipe = copy.deepcopy(_recipe())
    recipe["build_toolchain"] = {"status": "FROZEN", "lock_digest": "1" * 64}
    recipe["reproducibility_status"] = "REPRODUCIBLE"
    recipe["artifact_digest"] = "2" * 64
    recipe["build_evidence_digest"] = "3" * 64
    recipe["recipe_digest"] = recipe_digest(recipe)
    with pytest.raises(BuildRecipeV2Error):
        verify_build_recipe_v2(recipe)


def test_fresh_hash_cannot_bind_different_service_spec() -> None:
    recipe = copy.deepcopy(_recipe())
    recipe["service_spec_digest"] = "4" * 64
    recipe["recipe_digest"] = recipe_digest(recipe)
    with pytest.raises(BuildRecipeV2Error):
        verify_build_recipe_v2(recipe)

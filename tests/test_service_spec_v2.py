from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from agi_nexus.service_spec_v2 import ServiceSpecV2Error, spec_digest, verify_service_spec_v2


ROOT = Path(__file__).resolve().parents[1]


def _spec() -> dict:
    return json.loads((ROOT / "config/service_spec_v2.json").read_text(encoding="utf-8"))


def test_real_nexus_service_interface_is_source_implemented_only() -> None:
    spec = _spec()
    assert verify_service_spec_v2(spec) == spec
    assert spec["runtime_form"] == "PYTHON_STDLIB_SERVICE"
    assert spec["entrypoint"] == "python -m agi_nexus.nexus_service_v3"
    assert spec["interface_status"] == "SERVICE_INTERFACE_IMPLEMENTED_SOURCE_ONLY"
    assert spec["build_artifact_digest"] is None
    assert spec["build_evidence_digest"] is None
    assert spec["execution_authority"] == "NONE"


def test_fresh_hash_cannot_claim_build_verified_or_execution() -> None:
    spec = copy.deepcopy(_spec())
    spec["interface_status"] = "RUNNABLE"
    spec["build_artifact_digest"] = "1" * 64
    spec["build_evidence_digest"] = "2" * 64
    spec["execution_authority"] = "PROCESS_EXECUTION"
    spec["spec_digest"] = spec_digest(spec)
    with pytest.raises(ServiceSpecV2Error):
        verify_service_spec_v2(spec)


def test_fresh_hash_cannot_swap_runtime_source() -> None:
    spec = copy.deepcopy(_spec())
    spec["runtime_source_commit"] = "0" * 40
    spec["spec_digest"] = spec_digest(spec)
    with pytest.raises(ServiceSpecV2Error):
        verify_service_spec_v2(spec)


def test_fresh_hash_cannot_invent_neural_checkpoint() -> None:
    spec = copy.deepcopy(_spec())
    spec["neural_hypothesis_status"] = "OMEGA_R5_PRODUCTION_READY"
    spec["spec_digest"] = spec_digest(spec)
    with pytest.raises(ServiceSpecV2Error):
        verify_service_spec_v2(spec)

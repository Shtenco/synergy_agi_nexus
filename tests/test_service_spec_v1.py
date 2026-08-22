from __future__ import annotations

import copy
import json
from pathlib import Path

import jsonschema
import pytest

from agi_nexus.service_spec_v1 import ServiceSpecError, spec_digest, verify_service_spec_v1


ROOT = Path(__file__).resolve().parents[1]


def _spec() -> dict:
    return json.loads((ROOT / "config/service_spec_v1.json").read_text())


def test_current_nexus_spec_is_valid_but_not_runnable() -> None:
    spec = _spec()
    assert verify_service_spec_v1(spec) == spec
    assert spec["entrypoint"] is None
    assert spec["readiness_status"] == "SERVICE_INTERFACE_NOT_IMPLEMENTED"
    schema = json.loads((ROOT / "schemas/synergy_service_spec_v1.schema.json").read_text())
    jsonschema.validate(spec, schema)


def test_fresh_hash_cannot_invent_entrypoint_or_readiness() -> None:
    spec = copy.deepcopy(_spec())
    spec["runtime_form"] = "PYTHON_SERVICE"
    spec["entrypoint"] = "agi_nexus.runtime:main"
    spec["health_probe"] = "HEALTH_V1"
    spec["lifecycle_protocol"] = "META_OS_SERVICE_V1"
    spec["wire_protocol"] = "NEXUS_RPC_V1"
    spec["readiness_status"] = "RUNNABLE"
    spec["spec_digest"] = spec_digest(spec)
    with pytest.raises(ServiceSpecError):
        verify_service_spec_v1(spec)


def test_execution_authority_is_not_part_of_service_description() -> None:
    spec = copy.deepcopy(_spec())
    spec["execution_authority"] = "PROCESS_EXECUTION"
    spec["spec_digest"] = spec_digest(spec)
    with pytest.raises(ServiceSpecError):
        verify_service_spec_v1(spec)

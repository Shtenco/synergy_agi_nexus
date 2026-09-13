from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from agi_nexus.cyber_state_v1 import initial_state, step, verify_state, CyberStateError
from agi_nexus.nexus_service_v3 import handle, NexusServiceError
from agi_nexus.smallworld_core_v2 import exact_digests

ROOT = Path(__file__).resolve().parents[1]


def test_runtime_source_contract_is_non_authorizing() -> None:
    cfg = json.loads((ROOT / "config/nexus_runtime_source_v3.json").read_text(encoding="utf-8"))
    assert cfg["entrypoint"] == "python -m agi_nexus.nexus_service_v3"
    assert cfg["operations"] == ["STATUS", "FORMAL_REASON", "SMALLWORLD_EXACT_DIGESTS", "CYBER_STEP"]
    assert cfg["network_access"] == "NONE"
    assert cfg["process_execution_authority"] == "NONE"
    assert cfg["financial_authority"] == "NONE"
    assert cfg["build_artifact_digest"] is None
    assert cfg["execution_authority"] == "NONE"


def test_status_exposes_exact_core_not_fake_neural_runtime() -> None:
    response = handle({"request_id": "status-1", "operation": "STATUS"})
    payload = response["payload"]
    assert payload["status"] == "READY"
    assert payload["components"] == ["R710_FORMAL_PROOF", "EXACT_SMALLWORLD", "BOUNDED_CYBER_STATE"]
    assert payload["neural_hypothesis"] == "NOT_MIGRATED_NOT_REQUIRED_FOR_EXACT_CORE"
    assert response["execution_authority"] == "NONE"


def test_r710_formal_verified_http_and_numeric_float() -> None:
    http = handle({
        "request_id": "formal-http",
        "operation": "FORMAL_REASON",
        "item": {"q": "Что означает HTTP 404?", "options": {"A":"Успешно","B":"Ресурс не найден","C":"Запрещено","D":"Ошибка сервера"}},
    })
    assert http["payload"]["status"] == "VERIFIED"
    assert http["payload"]["answer"] == "B"
    assert http["payload"]["authority"] == "FORMAL_VERIFIED"

    division = handle({
        "request_id": "formal-div",
        "operation": "FORMAL_REASON",
        "item": {"q": "Сколько будет 5 / 2?", "options": {"A":"1.5","B":"2","C":"2.5","D":"3"}},
    })
    assert division["payload"]["status"] == "VERIFIED"
    assert division["payload"]["answer"] == "C"


def test_unknown_question_abstains_instead_of_guessing() -> None:
    response = handle({
        "request_id": "unknown-1",
        "operation": "FORMAL_REASON",
        "item": {"q": "Кто выиграет матч завтра?", "options": {"A":"A","B":"B","C":"C","D":"D"}},
    })
    assert response["payload"]["status"] == "UNKNOWN"
    assert response["payload"]["answer"] is None
    assert response["payload"]["authority"] == "NONE"


def test_smallworld_exact_canonical_vector() -> None:
    assert exact_digests(8, 4, 2, "NEXUS-V20") == (
        "9c4f6f4c890877688bf88caa6b4b18b129f56b038d8c5401955c4d200e2d97a9",
        "67c2a7f94c32d9f81d6f94af76146519cc7d40a3f1476685929ac196d41d0001",
    )


def test_cyber_state_is_bounded_hash_chained_and_non_executing() -> None:
    state0 = initial_state("session-1")
    state1 = step(state0, {"kind":"OBSERVE","updates":{"context":"датчик","goal":"держать уставку"},"formal_status":"UNKNOWN"})
    state2 = step(state1, {"kind":"FORMAL_RESULT","updates":{"effect":"negative feedback"},"formal_status":"VERIFIED"})
    assert verify_state(state2) == state2
    assert state2["previous_state_digest"] == state1["state_digest"]
    assert state2["authority"] == "FORMAL_VERIFIED"
    tampered = copy.deepcopy(state2)
    tampered["nodes"]["action"] = "run shell"
    with pytest.raises(CyberStateError):
        verify_state(tampered)


def test_wire_rejects_extra_host_path_or_command_fields() -> None:
    with pytest.raises(NexusServiceError):
        handle({"request_id":"x","operation":"STATUS","host":"evil.example"})
    with pytest.raises(NexusServiceError):
        handle({"request_id":"x","operation":"FORMAL_REASON","item":{"q":"x","options":{"A":"a","B":"b","C":"c","D":"d"}},"path":"/tmp/x"})
    with pytest.raises(NexusServiceError):
        handle({"request_id":"x","operation":"STATUS","command":"sh"})

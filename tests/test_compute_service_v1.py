import io
import json
from pathlib import Path

import pytest

from agi_nexus.compute_service_v1 import (
    ComputeServiceError,
    handle_request,
    serve_jsonl,
    verify_request,
    verify_response,
)

ROOT = Path(__file__).resolve().parents[1]


def load_json(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def canonical_request():
    return load_json("fixtures/compute_service/smallworld_request_v1.json")


def test_canonical_request_reproduces_exact_legacy_parity_response():
    request = canonical_request()
    response = handle_request(request)
    assert response == load_json("fixtures/compute_service/smallworld_response_v1.json")
    assert response["adjacency_digest"] == "62be4b397971b14b315288f9d9e7ff106b73cec3b58fd10a9fcc7e963053373a"
    assert response["metropolis_digest"] == "6657268c1f13ed7b57038f35614ecc25bd870d147bdf7ff210f025a75f7c6fc2"
    assert response["execution_authority"] == "NONE"
    verify_response(response, request)


def test_bool_and_unsafe_or_oversized_nodes_are_rejected():
    request = canonical_request()
    request["nodes"] = True
    with pytest.raises(ComputeServiceError, match="nodes"):
        verify_request(request)
    request = canonical_request()
    request["nodes"] = 1025
    with pytest.raises(ComputeServiceError, match="nodes"):
        verify_request(request)
    request = canonical_request()
    request["nodes"] = 2**53
    with pytest.raises(ComputeServiceError, match="nodes"):
        verify_request(request)


def test_unknown_operation_is_fail_closed():
    request = canonical_request()
    request["operation"] = "PYTHON_EVAL"
    with pytest.raises(ComputeServiceError, match="allowlisted"):
        verify_request(request)


def test_fresh_hash_cannot_change_service_scope_or_computation():
    request = canonical_request()
    response = handle_request(request)
    response["service_scope"] = "FULL_NEXUS"
    # Even if an attacker invents a new internally consistent-looking outer hash,
    # verification re-runs the deterministic computation from the request.
    body = dict(response)
    body.pop("response_digest")
    import hashlib
    response["response_digest"] = hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
    with pytest.raises(ComputeServiceError, match="does not match"):
        verify_response(response, request)


def test_jsonl_invalid_request_emits_bounded_error_without_authority():
    reader = io.BytesIO(b'{"schema":"nexus.compute-request/v1","operation":"PYTHON_EVAL"}\n')
    writer = io.BytesIO()
    assert serve_jsonl(reader, writer) == 0
    line = writer.getvalue().splitlines()[0]
    payload = json.loads(line.decode("utf-8"))
    assert payload == {
        "schema": "nexus.compute-error/v1",
        "code": "INVALID_REQUEST",
        "execution_authority": "NONE",
    }


def test_jsonl_oversized_frame_is_rejected_and_terminates():
    reader = io.BytesIO(b"x" * (64 * 1024 + 1) + b"\n")
    writer = io.BytesIO()
    assert serve_jsonl(reader, writer) == 2
    payload = json.loads(writer.getvalue().splitlines()[0].decode("utf-8"))
    assert payload["code"] == "INVALID_FRAME"
    assert payload["execution_authority"] == "NONE"

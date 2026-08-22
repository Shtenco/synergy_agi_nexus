from __future__ import annotations

import hashlib
import json
import sys
from typing import Any, BinaryIO

from .smallworld_exact_v2 import (
    MAX_NODES_V2,
    MAX_SHORTCUTS_V2,
    SmallWorldExactError,
    canonical_json,
    exact_semantic_digests_v2,
)


class ComputeServiceV2Error(ValueError):
    pass


_MAX_REQUEST_BYTES = 64 * 1024
_MAX_SEED_BYTES = 128


def _digest(payload: dict[str, Any], digest_field: str | None = None) -> str:
    body = dict(payload)
    if digest_field is not None:
        body.pop(digest_field, None)
    return hashlib.sha256(canonical_json(body)).hexdigest()


def _integer(value: object, name: str, minimum: int, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not (minimum <= value <= maximum):
        raise ComputeServiceV2Error(f"invalid {name}")
    return value


def verify_request_v2(payload: dict[str, Any]) -> dict[str, Any]:
    expected = {"schema", "request_id", "operation", "nodes", "local_degree", "shortcuts", "seed"}
    if not isinstance(payload, dict) or set(payload) != expected:
        raise ComputeServiceV2Error("unexpected compute request shape")
    if payload["schema"] != "nexus.compute-request/v2":
        raise ComputeServiceV2Error("unexpected request schema")
    if not isinstance(payload["request_id"], str) or not payload["request_id"] or len(payload["request_id"].encode("utf-8")) > 128:
        raise ComputeServiceV2Error("invalid request_id")
    if payload["operation"] != "SMALLWORLD_EXACT_DIGESTS":
        raise ComputeServiceV2Error("operation is not allowlisted")
    _integer(payload["nodes"], "nodes", 1, MAX_NODES_V2)
    _integer(payload["local_degree"], "local_degree", 0, MAX_NODES_V2)
    shortcuts = payload["shortcuts"]
    if shortcuts is not None:
        _integer(shortcuts, "shortcuts", 0, MAX_SHORTCUTS_V2)
    seed = payload["seed"]
    if not isinstance(seed, str) or not seed or len(seed.encode("utf-8")) > _MAX_SEED_BYTES:
        raise ComputeServiceV2Error("invalid seed")
    canonical_json(payload)
    return payload


def handle_request_v2(payload: dict[str, Any]) -> dict[str, Any]:
    request = verify_request_v2(payload)
    adjacency_digest, metropolis_digest = exact_semantic_digests_v2(
        request["nodes"],
        local_degree=request["local_degree"],
        shortcuts=request["shortcuts"],
        seed=request["seed"],
    )
    response = {
        "schema": "nexus.compute-response/v2",
        "request_id": request["request_id"],
        "operation": request["operation"],
        "request_digest": _digest(request),
        "service_scope": "SMALLWORLD_EXACT_KERNEL_ONLY",
        "status": "OK",
        "nodes": request["nodes"],
        "numeric_semantics": "EXACT_RATIONAL_METROPOLIS_V2",
        "topology_semantics": "V20_RING_PLUS_SHA256_SHORTCUT_SELECTION",
        "adjacency_semantic_digest": adjacency_digest,
        "metropolis_semantic_digest": metropolis_digest,
        "model_authority": "NONE",
        "execution_authority": "NONE",
    }
    response["response_digest"] = _digest(response)
    return response


def verify_response_v2(payload: dict[str, Any], request: dict[str, Any]) -> dict[str, Any]:
    expected = {
        "schema", "request_id", "operation", "request_digest", "service_scope", "status", "nodes",
        "numeric_semantics", "topology_semantics", "adjacency_semantic_digest", "metropolis_semantic_digest",
        "model_authority", "execution_authority", "response_digest",
    }
    if not isinstance(payload, dict) or set(payload) != expected:
        raise ComputeServiceV2Error("unexpected compute response shape")
    rebuilt = handle_request_v2(request)
    if payload != rebuilt:
        raise ComputeServiceV2Error("response does not match deterministic exact computation")
    return payload


def serve_jsonl_v2(reader: BinaryIO, writer: BinaryIO) -> int:
    while True:
        line = reader.readline(_MAX_REQUEST_BYTES + 1)
        if not line:
            return 0
        if len(line) > _MAX_REQUEST_BYTES or not line.endswith(b"\n"):
            error = {"schema": "nexus.compute-error/v2", "code": "INVALID_FRAME", "execution_authority": "NONE"}
            writer.write(canonical_json(error) + b"\n")
            writer.flush()
            return 2
        try:
            request = json.loads(line.decode("utf-8"))
            response = handle_request_v2(request)
        except (UnicodeDecodeError, json.JSONDecodeError, ComputeServiceV2Error, SmallWorldExactError, ValueError):
            response = {"schema": "nexus.compute-error/v2", "code": "INVALID_REQUEST", "execution_authority": "NONE"}
        writer.write(canonical_json(response) + b"\n")
        writer.flush()


def main() -> int:
    return serve_jsonl_v2(sys.stdin.buffer, sys.stdout.buffer)


if __name__ == "__main__":
    raise SystemExit(main())

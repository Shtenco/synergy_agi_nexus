from __future__ import annotations

import hashlib
import json
import sys
from typing import Any, BinaryIO

from .smallworld_v1 import deterministic_small_world, metropolis


class ComputeServiceError(ValueError):
    pass


_MAX_REQUEST_BYTES = 64 * 1024
_MAX_SERVICE_NODES = 1024


def _canonical(value: Any) -> bytes:
    def check(item: Any) -> None:
        if item is None or isinstance(item, (str, bool)):
            return
        if isinstance(item, int) and not isinstance(item, bool):
            if abs(item) > 2**53 - 1:
                raise ComputeServiceError("unsafe integer")
            return
        if isinstance(item, float):
            raise ComputeServiceError("floats forbidden in service protocol")
        if isinstance(item, list):
            for child in item:
                check(child)
            return
        if isinstance(item, dict):
            if any(not isinstance(k, str) for k in item):
                raise ComputeServiceError("object keys must be strings")
            for child in item.values():
                check(child)
            return
        raise ComputeServiceError("unsupported service-protocol value")
    check(value)
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _digest(payload: dict[str, Any], digest_field: str | None = None) -> str:
    body = dict(payload)
    if digest_field is not None:
        body.pop(digest_field, None)
    return hashlib.sha256(_canonical(body)).hexdigest()


def _integer(value: object, name: str, minimum: int, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not (minimum <= value <= maximum):
        raise ComputeServiceError(f"invalid {name}")
    return value


def verify_request(payload: dict[str, Any]) -> dict[str, Any]:
    expected = {"schema", "request_id", "operation", "nodes", "local_degree", "shortcuts", "seed"}
    if not isinstance(payload, dict) or set(payload) != expected:
        raise ComputeServiceError("unexpected compute request shape")
    if payload["schema"] != "nexus.compute-request/v1":
        raise ComputeServiceError("unexpected request schema")
    if not isinstance(payload["request_id"], str) or not payload["request_id"] or len(payload["request_id"].encode("utf-8")) > 128:
        raise ComputeServiceError("invalid request_id")
    if payload["operation"] != "SMALLWORLD_DIGESTS":
        raise ComputeServiceError("operation is not allowlisted")
    _integer(payload["nodes"], "nodes", 1, _MAX_SERVICE_NODES)
    _integer(payload["local_degree"], "local_degree", 0, _MAX_SERVICE_NODES)
    shortcuts = payload["shortcuts"]
    if shortcuts is not None:
        _integer(shortcuts, "shortcuts", 0, _MAX_SERVICE_NODES * _MAX_SERVICE_NODES)
    seed = payload["seed"]
    if not isinstance(seed, str) or not seed or len(seed.encode("utf-8")) > 128:
        raise ComputeServiceError("invalid seed")
    _canonical(payload)
    return payload


def handle_request(payload: dict[str, Any]) -> dict[str, Any]:
    request = verify_request(payload)
    adjacency = deterministic_small_world(
        request["nodes"],
        local_degree=request["local_degree"],
        shortcuts=request["shortcuts"],
        seed=request["seed"],
    )
    transition = metropolis(adjacency)
    response = {
        "schema": "nexus.compute-response/v1",
        "request_id": request["request_id"],
        "operation": request["operation"],
        "request_digest": _digest(request),
        "service_scope": "SMALLWORLD_KERNEL_ONLY",
        "status": "OK",
        "nodes": request["nodes"],
        "adjacency_digest": hashlib.sha256(adjacency.tobytes(order="C")).hexdigest(),
        "metropolis_digest": hashlib.sha256(transition.tobytes(order="C")).hexdigest(),
        "model_authority": "NONE",
        "execution_authority": "NONE",
    }
    response["response_digest"] = _digest(response)
    return response


def verify_response(payload: dict[str, Any], request: dict[str, Any]) -> dict[str, Any]:
    expected = {"schema", "request_id", "operation", "request_digest", "service_scope", "status", "nodes", "adjacency_digest", "metropolis_digest", "model_authority", "execution_authority", "response_digest"}
    if not isinstance(payload, dict) or set(payload) != expected:
        raise ComputeServiceError("unexpected compute response shape")
    rebuilt = handle_request(request)
    if payload != rebuilt:
        raise ComputeServiceError("response does not match deterministic computation")
    return payload


def serve_jsonl(reader: BinaryIO, writer: BinaryIO) -> int:
    while True:
        line = reader.readline(_MAX_REQUEST_BYTES + 1)
        if not line:
            return 0
        if len(line) > _MAX_REQUEST_BYTES or not line.endswith(b"\n"):
            error = {"schema":"nexus.compute-error/v1","code":"INVALID_FRAME","execution_authority":"NONE"}
            writer.write(_canonical(error) + b"\n")
            writer.flush()
            return 2
        try:
            request = json.loads(line.decode("utf-8"))
            response = handle_request(request)
        except (UnicodeDecodeError, json.JSONDecodeError, ComputeServiceError, ValueError):
            response = {"schema":"nexus.compute-error/v1","code":"INVALID_REQUEST","execution_authority":"NONE"}
        writer.write(_canonical(response) + b"\n")
        writer.flush()


def main() -> int:
    return serve_jsonl(sys.stdin.buffer, sys.stdout.buffer)


if __name__ == "__main__":
    raise SystemExit(main())

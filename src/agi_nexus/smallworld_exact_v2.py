from __future__ import annotations

from fractions import Fraction
import hashlib
import heapq
import json
import struct
from typing import Any


class SmallWorldExactError(ValueError):
    pass


MAX_NODES_V2 = 1024
MAX_SHORTCUTS_V2 = 4096


def _int(value: object, name: str, *, minimum: int = 0, maximum: int | None = None) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise SmallWorldExactError(f"{name} must be an integer")
    if value < minimum or (maximum is not None and value > maximum):
        raise SmallWorldExactError(f"{name} out of range")
    return value


def canonical_json(value: Any) -> bytes:
    def check(item: Any) -> None:
        if item is None or isinstance(item, (str, bool)):
            return
        if isinstance(item, int) and not isinstance(item, bool):
            if abs(item) > 2**53 - 1:
                raise SmallWorldExactError("unsafe integer")
            return
        if isinstance(item, float):
            raise SmallWorldExactError("floats forbidden in exact semantics")
        if isinstance(item, list):
            for child in item:
                check(child)
            return
        if isinstance(item, dict):
            if any(not isinstance(key, str) for key in item):
                raise SmallWorldExactError("object keys must be strings")
            for child in item.values():
                check(child)
            return
        raise SmallWorldExactError(f"unsupported canonical value: {type(item)!r}")

    check(value)
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def semantic_digest(value: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest()


def deterministic_topology_v2(
    nodes: int,
    local_degree: int = 4,
    shortcuts: int | None = None,
    seed: str = "NEXUS-V20",
) -> tuple[tuple[int, ...], ...]:
    nodes = _int(nodes, "nodes", minimum=1, maximum=MAX_NODES_V2)
    local_degree = _int(local_degree, "local_degree", minimum=0, maximum=MAX_NODES_V2)
    if shortcuts is not None:
        shortcuts = _int(shortcuts, "shortcuts", minimum=0, maximum=MAX_SHORTCUTS_V2)
    if not isinstance(seed, str) or not seed or len(seed.encode("utf-8")) > 256:
        raise SmallWorldExactError("seed must be a non-empty UTF-8 string <=256 bytes")

    neighbors: list[set[int]] = [{index} for index in range(nodes)]
    if nodes == 1:
        return ((0,),)

    local_degree = min(local_degree, nodes - 1)
    if local_degree % 2:
        local_degree -= 1
    local_degree = max(2 if nodes > 2 else nodes - 1, local_degree)
    radius = max(1, local_degree // 2)

    for left in range(nodes):
        for distance in range(1, radius + 1):
            right = (left + distance) % nodes
            neighbors[left].add(right)
            neighbors[right].add(left)

    missing_count = sum(
        1
        for left in range(nodes)
        for right in range(left + 1, nodes)
        if right not in neighbors[left]
    )
    wanted = max(1, nodes // 4) if shortcuts is None else shortcuts
    wanted = min(wanted, missing_count)

    if wanted:
        def candidates():
            for left in range(nodes):
                for right in range(left + 1, nodes):
                    if right not in neighbors[left]:
                        digest = hashlib.sha256(f"{seed}:{nodes}:{left}:{right}".encode("utf-8")).digest()
                        yield digest, left, right

        for _, left, right in heapq.nsmallest(wanted, candidates()):
            neighbors[left].add(right)
            neighbors[right].add(left)

    topology = tuple(tuple(sorted(row)) for row in neighbors)
    validate_topology_v2(topology)
    return topology


def validate_topology_v2(topology: tuple[tuple[int, ...], ...]) -> None:
    if not isinstance(topology, tuple) or not topology or len(topology) > MAX_NODES_V2:
        raise SmallWorldExactError("topology must be a non-empty bounded tuple")
    nodes = len(topology)
    for left, row in enumerate(topology):
        if not isinstance(row, tuple) or tuple(sorted(set(row))) != row:
            raise SmallWorldExactError("topology rows must be sorted unique tuples")
        if left not in row:
            raise SmallWorldExactError("self loops are required")
        for right in row:
            if isinstance(right, bool) or not isinstance(right, int) or not (0 <= right < nodes):
                raise SmallWorldExactError("invalid neighbor index")
            if left not in topology[right]:
                raise SmallWorldExactError("topology must be symmetric")


def adjacency_semantics_v2(topology: tuple[tuple[int, ...], ...]) -> dict[str, Any]:
    validate_topology_v2(topology)
    edges: list[list[int]] = []
    for left, row in enumerate(topology):
        for right in row:
            if left <= right:
                edges.append([left, right])
    return {
        "schema": "nexus.smallworld-adjacency-semantics/v2",
        "nodes": len(topology),
        "edges": edges,
    }


def metropolis_semantics_v2(topology: tuple[tuple[int, ...], ...]) -> dict[str, Any]:
    validate_topology_v2(topology)
    nodes = len(topology)
    degree = [len(row) - 1 for row in topology]
    rows: list[dict[str, Any]] = []

    for left, row in enumerate(topology):
        weights: list[dict[str, int]] = []
        off_diagonal = Fraction(0, 1)
        for right in row:
            if right == left:
                continue
            weight = Fraction(1, 1 + max(degree[left], degree[right]))
            off_diagonal += weight
            weights.append({"col": right, "num": weight.numerator, "den": weight.denominator})

        diagonal = Fraction(1, 1) - off_diagonal
        if diagonal < 0:
            raise SmallWorldExactError("negative exact Metropolis diagonal")
        weights.append({"col": left, "num": diagonal.numerator, "den": diagonal.denominator})
        weights.sort(key=lambda item: item["col"])

        total = sum((Fraction(item["num"], item["den"]) for item in weights), Fraction(0, 1))
        if total != 1:
            raise SmallWorldExactError("exact Metropolis row must sum to one")
        rows.append({"row": left, "weights": weights})

    return {
        "schema": "nexus.smallworld-metropolis-semantics/v2",
        "nodes": nodes,
        "rows": rows,
    }


def exact_semantic_digests_v2(
    nodes: int,
    local_degree: int = 4,
    shortcuts: int | None = None,
    seed: str = "NEXUS-V20",
) -> tuple[str, str]:
    topology = deterministic_topology_v2(nodes, local_degree=local_degree, shortcuts=shortcuts, seed=seed)
    adjacency = adjacency_semantics_v2(topology)
    metropolis = metropolis_semantics_v2(topology)
    return semantic_digest(adjacency), semantic_digest(metropolis)


def legacy_little_endian_float32_adjacency_digest_v2(topology: tuple[tuple[int, ...], ...]) -> str:
    """Compatibility witness for the V20/v1 adjacency only.

    Adjacency values are exactly 0/1, so explicit little-endian IEEE754 float32 bytes
    are stable without importing NumPy. This does NOT attempt to reproduce NumPy's
    Metropolis reduction bytes; v2 uses exact rational semantics for that matrix.
    """
    validate_topology_v2(topology)
    out = bytearray()
    for left, row in enumerate(topology):
        membership = set(row)
        for right in range(len(topology)):
            out.extend(struct.pack("<f", 1.0 if right in membership else 0.0))
    return hashlib.sha256(bytes(out)).hexdigest()

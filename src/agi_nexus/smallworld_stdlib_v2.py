from __future__ import annotations

import hashlib
import struct
from typing import Iterable, Sequence


class SmallWorldStdlibV2Error(ValueError):
    pass


MAX_NODES_V2 = 1024
PAIRWISE_BLOCK_SIZE = 128


def _integer(value: object, name: str, *, minimum: int = 0, maximum: int | None = None) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise SmallWorldStdlibV2Error(f"{name} must be an integer")
    if value < minimum or (maximum is not None and value > maximum):
        raise SmallWorldStdlibV2Error(f"{name} out of range")
    return value


def f32(value: float | int) -> float:
    """Round one operation result to IEEE-754 binary32, little-endian stable."""
    return struct.unpack("<f", struct.pack("<f", float(value)))[0]


def numpy_float32_pairwise_sum(values: Sequence[float]) -> float:
    """Reproduce NumPy's contiguous float32 pairwise reduction semantics.

    This mirrors the historical reduction shape used by the migrated V20
    `np.ndarray.sum()` calls: direct accumulation for n<8, eight partial
    accumulators up to block size 128, and recursively split blocks above 128.
    Every arithmetic operation is rounded to float32.
    """
    vals = [f32(value) for value in values]
    n = len(vals)
    if n < 8:
        result = f32(-0.0)
        for value in vals:
            result = f32(result + value)
        return result
    if n <= PAIRWISE_BLOCK_SIZE:
        partial = vals[:8]
        index = 8
        while index < n - 7:
            for lane in range(8):
                partial[lane] = f32(partial[lane] + vals[index + lane])
            index += 8
        p01 = f32(partial[0] + partial[1])
        p23 = f32(partial[2] + partial[3])
        p45 = f32(partial[4] + partial[5])
        p67 = f32(partial[6] + partial[7])
        left = f32(p01 + p23)
        right = f32(p45 + p67)
        result = f32(left + right)
        while index < n:
            result = f32(result + vals[index])
            index += 1
        return result
    half = n // 2
    half -= half % 8
    return f32(
        numpy_float32_pairwise_sum(vals[:half])
        + numpy_float32_pairwise_sum(vals[half:])
    )


def deterministic_small_world(
    nodes: int,
    local_degree: int = 4,
    shortcuts: int | None = None,
    seed: str = "NEXUS-V20",
) -> tuple[tuple[float, ...], ...]:
    nodes = _integer(nodes, "nodes", minimum=1, maximum=MAX_NODES_V2)
    local_degree = _integer(local_degree, "local_degree", minimum=0, maximum=MAX_NODES_V2)
    if shortcuts is not None:
        shortcuts = _integer(shortcuts, "shortcuts", minimum=0, maximum=MAX_NODES_V2 * MAX_NODES_V2)
    if not isinstance(seed, str) or not seed or len(seed.encode("utf-8")) > 256:
        raise SmallWorldStdlibV2Error("seed must be a non-empty UTF-8 string <=256 bytes")

    if nodes == 1:
        return ((f32(1.0),),)

    local_degree = min(local_degree, nodes - 1)
    if local_degree % 2:
        local_degree -= 1
    local_degree = max(2 if nodes > 2 else nodes - 1, local_degree)

    matrix = [[f32(0.0) for _ in range(nodes)] for _ in range(nodes)]
    for index in range(nodes):
        matrix[index][index] = f32(1.0)

    radius = max(1, local_degree // 2)
    for left in range(nodes):
        for distance in range(1, radius + 1):
            right = (left + distance) % nodes
            matrix[left][right] = matrix[right][left] = f32(1.0)

    candidates: list[tuple[bytes, int, int]] = []
    for left in range(nodes):
        for right in range(left + 1, nodes):
            if matrix[left][right] == 0.0:
                digest = hashlib.sha256(f"{seed}:{nodes}:{left}:{right}".encode("utf-8")).digest()
                candidates.append((digest, left, right))

    wanted = max(1, nodes // 4) if shortcuts is None else shortcuts
    for _, left, right in sorted(candidates)[:wanted]:
        matrix[left][right] = matrix[right][left] = f32(1.0)

    frozen = tuple(tuple(row) for row in matrix)
    validate_adjacency(frozen)
    return frozen


def validate_adjacency(matrix: Sequence[Sequence[float]]) -> None:
    if not isinstance(matrix, (tuple, list)) or not matrix:
        raise SmallWorldStdlibV2Error("adjacency must be non-empty")
    nodes = len(matrix)
    if nodes > MAX_NODES_V2:
        raise SmallWorldStdlibV2Error("adjacency exceeds v2 node bound")
    for row in matrix:
        if not isinstance(row, (tuple, list)) or len(row) != nodes:
            raise SmallWorldStdlibV2Error("adjacency must be square")
    for left in range(nodes):
        if matrix[left][left] <= 0.0:
            raise SmallWorldStdlibV2Error("self loops are required")
        for right in range(nodes):
            value = matrix[left][right]
            if not isinstance(value, (int, float)) or value != value or value in (float("inf"), float("-inf")) or value < 0.0:
                raise SmallWorldStdlibV2Error("adjacency must be finite and non-negative")
            if f32(value) != f32(matrix[right][left]):
                raise SmallWorldStdlibV2Error("adjacency must be symmetric")


def metropolis(matrix: Sequence[Sequence[float]]) -> tuple[tuple[float, ...], ...]:
    validate_adjacency(matrix)
    nodes = len(matrix)
    support = [
        [f32(1.0) if matrix[left][right] > 0.0 else f32(0.0) for right in range(nodes)]
        for left in range(nodes)
    ]
    degree = [f32(numpy_float32_pairwise_sum(row) - 1.0) for row in support]
    transition = [[f32(0.0) for _ in range(nodes)] for _ in range(nodes)]
    for left in range(nodes):
        for right in range(nodes):
            if left != right and support[left][right] > 0.0:
                transition[left][right] = f32(
                    1.0 / (1.0 + max(float(degree[left]), float(degree[right])))
                )
        row_sum = numpy_float32_pairwise_sum(transition[left])
        transition[left][left] = f32(1.0 - float(row_sum))

    frozen = tuple(tuple(row) for row in transition)
    for row in frozen:
        if any(value != value or value in (float("inf"), float("-inf")) or value < -1e-7 for value in row):
            raise SmallWorldStdlibV2Error("invalid Metropolis transition")
        if abs(float(numpy_float32_pairwise_sum(row)) - 1.0) > 1e-6:
            raise SmallWorldStdlibV2Error("Metropolis rows must sum to one")
    return frozen


def float32_matrix_bytes(matrix: Sequence[Sequence[float]]) -> bytes:
    return b"".join(struct.pack("<f", f32(value)) for row in matrix for value in row)


def matrix_digest(matrix: Sequence[Sequence[float]]) -> str:
    return hashlib.sha256(float32_matrix_bytes(matrix)).hexdigest()


def topology_digests(
    nodes: int,
    local_degree: int = 4,
    shortcuts: int | None = None,
    seed: str = "NEXUS-V20",
) -> tuple[str, str]:
    adjacency = deterministic_small_world(nodes, local_degree, shortcuts, seed)
    transition = metropolis(adjacency)
    return matrix_digest(adjacency), matrix_digest(transition)

from __future__ import annotations

import hashlib
import math

import numpy as np


class SmallWorldInvariantError(ValueError):
    pass


MAX_NODES_V1 = 4096


def _int(value: object, name: str, *, minimum: int = 0, maximum: int | None = None) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise SmallWorldInvariantError(f"{name} must be an integer")
    if value < minimum or (maximum is not None and value > maximum):
        raise SmallWorldInvariantError(f"{name} out of range")
    return value


def deterministic_small_world(
    nodes: int,
    local_degree: int = 4,
    shortcuts: int | None = None,
    seed: str = "NEXUS-V20",
) -> np.ndarray:
    nodes = _int(nodes, "nodes", minimum=1, maximum=MAX_NODES_V1)
    local_degree = _int(local_degree, "local_degree", minimum=0, maximum=MAX_NODES_V1)
    if shortcuts is not None:
        shortcuts = _int(shortcuts, "shortcuts", minimum=0, maximum=MAX_NODES_V1 * MAX_NODES_V1)
    if not isinstance(seed, str) or not seed or len(seed.encode("utf-8")) > 256:
        raise SmallWorldInvariantError("seed must be a non-empty UTF-8 string <=256 bytes")

    if nodes == 1:
        return np.ones((1, 1), dtype=np.float32)
    local_degree = min(local_degree, nodes - 1)
    if local_degree % 2:
        local_degree -= 1
    local_degree = max(2 if nodes > 2 else nodes - 1, local_degree)
    adjacency = np.eye(nodes, dtype=np.float32)
    radius = max(1, local_degree // 2)
    for left in range(nodes):
        for distance in range(1, radius + 1):
            right = (left + distance) % nodes
            adjacency[left, right] = adjacency[right, left] = 1.0

    candidates: list[tuple[bytes, int, int]] = []
    for left in range(nodes):
        for right in range(left + 1, nodes):
            if not adjacency[left, right]:
                digest = hashlib.sha256(f"{seed}:{nodes}:{left}:{right}".encode("utf-8")).digest()
                candidates.append((digest, left, right))
    wanted = max(1, nodes // 4) if shortcuts is None else shortcuts
    for _, left, right in sorted(candidates)[:wanted]:
        adjacency[left, right] = adjacency[right, left] = 1.0
    validate_adjacency(adjacency)
    return adjacency


def validate_adjacency(adjacency: np.ndarray) -> None:
    values = np.asarray(adjacency)
    if values.ndim != 2 or values.shape[0] != values.shape[1] or values.shape[0] == 0:
        raise SmallWorldInvariantError("adjacency must be non-empty square matrix")
    if values.shape[0] > MAX_NODES_V1:
        raise SmallWorldInvariantError("adjacency exceeds v1 node bound")
    if not np.isfinite(values).all() or (values < 0).any():
        raise SmallWorldInvariantError("adjacency must be finite and non-negative")
    if not np.array_equal(values, values.T):
        raise SmallWorldInvariantError("adjacency must be symmetric")
    if not np.all(np.diag(values) > 0):
        raise SmallWorldInvariantError("self loops are required")


def metropolis(adjacency: np.ndarray) -> np.ndarray:
    validate_adjacency(adjacency)
    support = np.asarray(np.asarray(adjacency) > 0, dtype=np.float32)
    degree = support.sum(axis=-1) - 1.0
    transition = np.zeros_like(support)
    nodes = support.shape[0]
    for left in range(nodes):
        for right in range(nodes):
            if left != right and support[left, right]:
                transition[left, right] = 1.0 / (1.0 + max(float(degree[left]), float(degree[right])))
        transition[left, left] = 1.0 - transition[left].sum()
    if not np.isfinite(transition).all() or (transition < -1e-7).any():
        raise SmallWorldInvariantError("invalid Metropolis transition")
    if not np.allclose(transition.sum(axis=1), 1.0, rtol=0.0, atol=1e-6):
        raise SmallWorldInvariantError("Metropolis rows must sum to one")
    return transition.astype(np.float32, copy=False)


def layer_norm(values: np.ndarray, scale: np.ndarray, bias: np.ndarray) -> np.ndarray:
    mean = values.mean(axis=-1, keepdims=True)
    variance = ((values - mean) ** 2).mean(axis=-1, keepdims=True)
    return (values - mean) / np.sqrt(variance + 1e-5) * scale + bias


def gelu(values: np.ndarray) -> np.ndarray:
    return 0.5 * values * (1.0 + np.tanh(math.sqrt(2.0 / math.pi) * (values + 0.044715 * values**3)))


def sigmoid(values: np.ndarray) -> np.ndarray:
    clipped = np.clip(values, -30.0, 30.0)
    return 1.0 / (1.0 + np.exp(-clipped))


def softmax(values: np.ndarray, axis: int = -1) -> np.ndarray:
    shifted = values - values.max(axis=axis, keepdims=True)
    exp = np.exp(shifted)
    return exp / np.maximum(exp.sum(axis=axis, keepdims=True), 1e-12)

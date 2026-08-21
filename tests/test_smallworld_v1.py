import hashlib

import numpy as np
import pytest

from agi_nexus.smallworld_v1 import (
    MAX_NODES_V1,
    SmallWorldInvariantError,
    deterministic_small_world,
    metropolis,
)


def _digest(values: np.ndarray) -> str:
    return hashlib.sha256(np.asarray(values, dtype=np.float32).tobytes(order="C")).hexdigest()


def test_v20_legacy_parity_vector_8_nodes():
    adjacency = deterministic_small_world(8, local_degree=4, shortcuts=2, seed="NEXUS-V20")
    transition = metropolis(adjacency)
    assert _digest(adjacency) == "62be4b397971b14b315288f9d9e7ff106b73cec3b58fd10a9fcc7e963053373a"
    assert _digest(transition) == "6657268c1f13ed7b57038f35614ecc25bd870d147bdf7ff210f025a75f7c6fc2"


def test_v20_legacy_parity_vector_16_nodes_default_shortcuts():
    adjacency = deterministic_small_world(16, local_degree=4, shortcuts=None, seed="NEXUS-V20")
    transition = metropolis(adjacency)
    assert _digest(adjacency) == "67b1eae1ee2730fd8fd513db5c356faa317a96e42213199f1686afb58993e9cb"
    assert _digest(transition) == "1df1ddc1f68a8504d4714bce09fcb764ffcd27cf3fab87a5835a9b0444b13548"


def test_topology_invariants_and_determinism():
    a = deterministic_small_world(32, local_degree=4, shortcuts=8, seed="stable")
    b = deterministic_small_world(32, local_degree=4, shortcuts=8, seed="stable")
    assert np.array_equal(a, b)
    assert np.array_equal(a, a.T)
    assert np.all(np.diag(a) == 1.0)
    assert set(np.unique(a)).issubset({0.0, 1.0})


def test_metropolis_is_row_stochastic_non_negative():
    transition = metropolis(deterministic_small_world(24, local_degree=6, shortcuts=5))
    assert np.isfinite(transition).all()
    assert (transition >= -1e-7).all()
    assert np.allclose(transition.sum(axis=1), 1.0, rtol=0.0, atol=1e-6)


@pytest.mark.parametrize("bad", [True, 0, -1, MAX_NODES_V1 + 1])
def test_nodes_are_bounded_safe_integers(bad):
    with pytest.raises(SmallWorldInvariantError):
        deterministic_small_world(bad)


def test_bad_shortcuts_and_seed_are_rejected():
    with pytest.raises(SmallWorldInvariantError):
        deterministic_small_world(8, shortcuts=True)
    with pytest.raises(SmallWorldInvariantError):
        deterministic_small_world(8, shortcuts=-1)
    with pytest.raises(SmallWorldInvariantError):
        deterministic_small_world(8, seed="")


def test_adjacency_tampering_is_rejected():
    bad = deterministic_small_world(8)
    bad[0, 1] = 0.0
    bad[1, 0] = 1.0
    with pytest.raises(SmallWorldInvariantError):
        metropolis(bad)

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agi_nexus.smallworld_stdlib_v2 import (
    SmallWorldStdlibV2Error,
    deterministic_small_world,
    matrix_digest,
    metropolis,
    numpy_float32_pairwise_sum,
    topology_digests,
    validate_adjacency,
)

ROOT = Path(__file__).resolve().parents[1]
VECTORS = ROOT / "fixtures/smallworld_parity/stdlib_v2_legacy_numpy_vectors.json"


def test_all_legacy_numpy_golden_vectors_match_exact_bytes():
    payload = json.loads(VECTORS.read_text(encoding="utf-8"))
    assert payload["semantics"] == "NUMPY_FLOAT32_PAIRWISE_COMPAT"
    assert payload["pairwise_block_size"] == 128
    assert len(payload["vectors"]) == 10
    for vector in payload["vectors"]:
        adjacency, transition = topology_digests(
            vector["nodes"], vector["local_degree"], vector["shortcuts"], vector["seed"]
        )
        assert adjacency == vector["adjacency_digest"]
        assert transition == vector["metropolis_digest"]


def test_block_boundary_vectors_127_128_129_are_distinct_and_stable():
    payload = json.loads(VECTORS.read_text(encoding="utf-8"))
    selected = {v["nodes"]: v for v in payload["vectors"] if v["nodes"] in {127,128,129}}
    assert set(selected) == {127,128,129}
    for nodes in (127,128,129):
        assert topology_digests(nodes, 4, None, "NEXUS-V20") == (
            selected[nodes]["adjacency_digest"], selected[nodes]["metropolis_digest"]
        )


def test_pairwise_reduction_preserves_legacy_one_ulp_difference_from_naive_sum():
    # This is the exact shape of the historical 8-node row 5 before the diagonal
    # is filled: six 1/7 weights and two zero slots. NumPy's float32 pairwise
    # reduction differs by one ULP from naive left-to-right accumulation here.
    values = [0.0, 1.0 / 7.0, 1.0 / 7.0, 1.0 / 7.0, 1.0 / 7.0, 0.0, 1.0 / 7.0, 1.0 / 7.0]
    reference = numpy_float32_pairwise_sum(values)
    from agi_nexus.smallworld_stdlib_v2 import f32
    naive = f32(0.0)
    for value in values:
        naive = f32(naive + f32(value))
    assert reference != naive
    assert reference == f32(0.8571429252624512)
    assert naive == f32(0.8571428656578064)


def test_invalid_inputs_fail_closed():
    with pytest.raises(SmallWorldStdlibV2Error):
        deterministic_small_world(True)
    with pytest.raises(SmallWorldStdlibV2Error):
        deterministic_small_world(1025)
    with pytest.raises(SmallWorldStdlibV2Error):
        deterministic_small_world(8, shortcuts=-1)
    with pytest.raises(SmallWorldStdlibV2Error):
        deterministic_small_world(8, seed="")


def test_adjacency_validation_rejects_shape_symmetry_and_nonfinite_values():
    with pytest.raises(SmallWorldStdlibV2Error):
        validate_adjacency(((1.0, 1.0),))
    with pytest.raises(SmallWorldStdlibV2Error):
        validate_adjacency(((1.0, 1.0), (0.0, 1.0)))
    with pytest.raises(SmallWorldStdlibV2Error):
        validate_adjacency(((1.0, float("nan")), (float("nan"), 1.0)))


def test_metropolis_is_deterministic_and_row_stochastic_under_reference_reduction():
    adjacency = deterministic_small_world(33, local_degree=4, shortcuts=None, seed="ALT-SEED")
    first = metropolis(adjacency)
    second = metropolis(adjacency)
    assert first == second
    assert matrix_digest(first) == "5bb726d23d10086f8da3d35d204c62f81c7da8056043ac84b073139f065b620c"
    for row in first:
        assert abs(float(numpy_float32_pairwise_sum(row)) - 1.0) <= 1e-6

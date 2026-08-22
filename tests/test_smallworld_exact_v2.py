from __future__ import annotations

from fractions import Fraction
import hashlib
import json
from pathlib import Path

import pytest

from agi_nexus.compute_service_v2 import (
    ComputeServiceV2Error,
    handle_request_v2,
    verify_request_v2,
    verify_response_v2,
)
from agi_nexus.smallworld_exact_v2 import (
    SmallWorldExactError,
    adjacency_semantics_v2,
    deterministic_topology_v2,
    exact_semantic_digests_v2,
    legacy_little_endian_float32_adjacency_digest_v2,
    metropolis_semantics_v2,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "fixtures" / "smallworld_exact_v2" / "canonical_8node_response.json"


def test_v2_preserves_known_v20_adjacency_bytes_without_numpy() -> None:
    topology_8 = deterministic_topology_v2(8, local_degree=4, shortcuts=2, seed="NEXUS-V20")
    topology_16 = deterministic_topology_v2(16, local_degree=4, shortcuts=None, seed="NEXUS-V20")
    assert legacy_little_endian_float32_adjacency_digest_v2(topology_8) == (
        "62be4b397971b14b315288f9d9e7ff106b73cec3b58fd10a9fcc7e963053373a"
    )
    assert legacy_little_endian_float32_adjacency_digest_v2(topology_16) == (
        "67b1eae1ee2730fd8fd513db5c356faa317a96e42213199f1686afb58993e9cb"
    )


def test_exact_semantic_vectors_are_frozen() -> None:
    adjacency_digest, metropolis_digest = exact_semantic_digests_v2(
        8, local_degree=4, shortcuts=2, seed="NEXUS-V20"
    )
    assert adjacency_digest == "9c4f6f4c890877688bf88caa6b4b18b129f56b038d8c5401955c4d200e2d97a9"
    assert metropolis_digest == "67c2a7f94c32d9f81d6f94af76146519cc7d40a3f1476685929ac196d41d0001"

    adjacency_16, metropolis_16 = exact_semantic_digests_v2(16, seed="NEXUS-V20")
    assert adjacency_16 == "202b385ec0dfeb78936c56eee50c327a5a8e16e0c861dab8424a0d8170d51ddc"
    assert metropolis_16 == "5dd3c4bcfe19bf824b8e0041d55be0a8a7613a90207217fa12a45d56b02d4078"


def test_exact_metropolis_rows_sum_to_one_without_tolerance() -> None:
    topology = deterministic_topology_v2(64, local_degree=8, shortcuts=17, seed="exact-test")
    semantics = metropolis_semantics_v2(topology)
    for row in semantics["rows"]:
        total = sum(
            (Fraction(item["num"], item["den"]) for item in row["weights"]),
            Fraction(0, 1),
        )
        assert total == Fraction(1, 1)
        assert all(item["den"] > 0 and item["num"] >= 0 for item in row["weights"])


def test_adjacency_semantics_are_sparse_sorted_and_complete() -> None:
    topology = deterministic_topology_v2(8, local_degree=4, shortcuts=2)
    semantics = adjacency_semantics_v2(topology)
    assert semantics["nodes"] == 8
    assert semantics["edges"] == sorted(semantics["edges"])
    assert all(left <= right for left, right in semantics["edges"])
    assert [[index, index] for index in range(8)] == [
        edge for edge in semantics["edges"] if edge[0] == edge[1]
    ]


def test_service_matches_canonical_fixture_exactly() -> None:
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert handle_request_v2(fixture["request"]) == fixture["response"]
    assert verify_response_v2(fixture["response"], fixture["request"]) == fixture["response"]


def test_fresh_hash_cannot_legalize_semantic_or_authority_tamper() -> None:
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    response = dict(fixture["response"])
    response["execution_authority"] = "BROKER"
    body = dict(response)
    body.pop("response_digest")
    response["response_digest"] = hashlib.sha256(
        json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    with pytest.raises(ComputeServiceV2Error):
        verify_response_v2(response, fixture["request"])

    response = dict(fixture["response"])
    response["metropolis_semantic_digest"] = "0" * 64
    body = dict(response)
    body.pop("response_digest")
    response["response_digest"] = hashlib.sha256(
        json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    with pytest.raises(ComputeServiceV2Error):
        verify_response_v2(response, fixture["request"])


def test_v2_bounds_and_type_checks_fail_closed() -> None:
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))["request"]

    bad = dict(fixture)
    bad["nodes"] = True
    with pytest.raises(ComputeServiceV2Error):
        verify_request_v2(bad)

    bad = dict(fixture)
    bad["nodes"] = 1025
    with pytest.raises(ComputeServiceV2Error):
        verify_request_v2(bad)

    bad = dict(fixture)
    bad["shortcuts"] = 4097
    with pytest.raises(ComputeServiceV2Error):
        verify_request_v2(bad)

    with pytest.raises(SmallWorldExactError):
        deterministic_topology_v2(8, shortcuts=4097)


def test_v2_core_has_no_numpy_runtime_dependency() -> None:
    core = (ROOT / "src" / "agi_nexus" / "smallworld_exact_v2.py").read_text(encoding="utf-8")
    service = (ROOT / "src" / "agi_nexus" / "compute_service_v2.py").read_text(encoding="utf-8")
    assert "import numpy" not in core
    assert "import numpy" not in service
    assert "from numpy" not in core
    assert "from numpy" not in service

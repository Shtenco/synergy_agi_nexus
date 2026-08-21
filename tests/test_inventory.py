from copy import deepcopy
from pathlib import Path

import pytest

from agi_nexus import InventoryError, load_json, validate_benchmark_registry, validate_generation_inventory

ROOT = Path(__file__).resolve().parents[1]


def test_generation_inventory_is_valid():
    payload = load_json(ROOT / "config/nexus_generation_inventory_v1.json")
    validate_generation_inventory(payload)
    ids = {item["id"] for item in payload["generations"]}
    assert {"smallworld-v11.3", "nexus-600k", "nexus-v20-smallworld-1m", "nexus-r74-teacher-lab"} <= ids


def test_branch_discovery_cannot_claim_reproduced_evidence():
    payload = load_json(ROOT / "config/nexus_generation_inventory_v1.json")
    broken = deepcopy(payload)
    item = next(x for x in broken["generations"] if x["evidence"] == "BRANCH_DISCOVERED")
    item["evidence"] = "REPRODUCED_INTERNAL"
    with pytest.raises(InventoryError):
        validate_generation_inventory(broken)


def test_duplicate_generation_id_is_rejected():
    payload = load_json(ROOT / "config/nexus_generation_inventory_v1.json")
    broken = deepcopy(payload)
    broken["generations"].append(deepcopy(broken["generations"][0]))
    with pytest.raises(InventoryError):
        validate_generation_inventory(broken)


def test_benchmark_registry_is_valid_and_has_no_private_official_claim():
    payload = load_json(ROOT / "config/benchmark_registry_v1.json")
    validate_benchmark_registry(payload)
    assert all(item["official_private"] is False for item in payload["benchmarks"])


def test_synthetic_benchmark_cannot_be_silently_relabelled_official_private():
    payload = load_json(ROOT / "config/benchmark_registry_v1.json")
    broken = deepcopy(payload)
    item = next(x for x in broken["benchmarks"] if x["tier"] == "SYNTHETIC")
    item["official_private"] = True
    with pytest.raises(InventoryError):
        validate_benchmark_registry(broken)

import json
from pathlib import Path

import pytest

from agi_nexus.build_readiness_v1 import BuildReadinessError, readiness_digest, verify_smallworld_build_readiness

ROOT = Path(__file__).resolve().parents[1]


def load_payload():
    return json.loads((ROOT / "config/smallworld_build_readiness_v1.json").read_text(encoding="utf-8"))


def test_canonical_readiness_is_source_frozen_but_not_service_ready():
    payload = load_payload()
    verify_smallworld_build_readiness(payload)
    assert payload["readiness_digest"] == "0e29504a9448c970fd5057123300000aca8c3d88e84f524bed2041cb881aec9a"
    assert payload["service_entrypoint"] is None
    assert payload["build_artifact_digest"] is None
    assert payload["service_readiness"] == "COMPONENT_ONLY_NOT_NODE_SERVICE"


def test_fresh_hash_cannot_invent_service_entrypoint():
    payload = load_payload()
    payload["service_entrypoint"] = "agi_nexus.smallworld_v1:main"
    payload["readiness_digest"] = readiness_digest(payload)
    with pytest.raises(BuildReadinessError, match="non-service component"):
        verify_smallworld_build_readiness(payload)


def test_fresh_hash_cannot_claim_build_artifact():
    payload = load_payload()
    payload["build_artifact_digest"] = "f" * 64
    payload["readiness_digest"] = readiness_digest(payload)
    with pytest.raises(BuildReadinessError, match="cannot claim artifact"):
        verify_smallworld_build_readiness(payload)


def test_source_commit_and_blob_identity_are_immutable():
    payload = load_payload()
    payload["source_artifacts"][1]["git_blob_sha"] = "0" * 40
    payload["readiness_digest"] = readiness_digest(payload)
    with pytest.raises(BuildReadinessError, match="source artifact identity drifted"):
        verify_smallworld_build_readiness(payload)

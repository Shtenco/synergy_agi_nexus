import pytest

from agi_nexus import NexusContractError, NexusPolicyProposal


def test_unknown_cannot_claim_high_confidence():
    with pytest.raises(NexusContractError):
        NexusPolicyProposal(
            proposal_id="p1",
            domain="finance",
            objective="decide",
            recommended_action="defer",
            confidence=0.9,
            epistemic_state="UNKNOWN",
        )


def test_nexus_has_no_execution_authority():
    proposal = NexusPolicyProposal(
        proposal_id="p1",
        domain="finance",
        objective="evaluate",
        recommended_action="request approval",
        confidence=0.8,
        epistemic_state="INFERRED",
        constraints=("no-direct-execution",),
        risk_flags=("capital-at-risk",),
    )
    assert proposal.execution_authority == "NONE"
    assert proposal.as_payload()["recommended_action"] == "request approval"

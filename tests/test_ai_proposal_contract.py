from uuid import UUID
import pytest

from contracts.ai_proposal_v1 import CONTRACT_ID, ai_proposal_payload


def test_nexus_contract_is_proposal_not_authorization():
    p=ai_proposal_payload(
        proposal_id=UUID("11111111-1111-4111-8111-111111111111"),
        task_type="trading",
        model_id="nexus-v18:test",
        proposal={"action":"consider EURUSD long"},
        confidence=0.6,
        limitations=["research inference only"],
    )
    assert CONTRACT_ID=="synergy.ai.proposal/v1"
    assert p["requires_human_authorization"] is True


def test_nexus_contract_requires_limitations():
    with pytest.raises(ValueError):
        ai_proposal_payload(
            proposal_id="11111111-1111-4111-8111-111111111111",
            task_type="general",model_id="nexus-v18",
            proposal={},confidence=0.5,limitations=[],
        )

from __future__ import annotations
from typing import Any
from uuid import UUID


CONTRACT_ID = "synergy.ai.proposal/v1"
AUTHORITY = "nexus_core"
TASK_TYPES = {"TRADING","SCIENCE","ECONOMY","ENGINEERING","GENERAL"}


def ai_proposal_payload(
    *,
    proposal_id: UUID | str,
    task_type: str,
    model_id: str,
    proposal: dict[str, Any],
    confidence: float,
    limitations: list[str],
    benchmark_refs: list[str] | None = None,
    requires_human_authorization: bool = True,
) -> dict[str, Any]:
    task = task_type.upper()
    if task not in TASK_TYPES:
        raise ValueError("unsupported task_type")
    if not 0.0 <= confidence <= 1.0:
        raise ValueError("confidence must be within [0,1]")
    if not model_id.strip():
        raise ValueError("model_id is required")
    if not limitations:
        raise ValueError("limitations must be explicit")
    return {
        "proposal_id": str(proposal_id),
        "task_type": task,
        "model_id": model_id,
        "proposal": dict(proposal),
        "confidence": float(confidence),
        "limitations": list(limitations),
        "benchmark_refs": list(benchmark_refs or []),
        "requires_human_authorization": bool(requires_human_authorization),
    }

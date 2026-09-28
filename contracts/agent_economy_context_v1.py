from __future__ import annotations
from decimal import Decimal
from typing import Any

UPSTREAM_CONTRACT_ID = "synergy.agent.economy-simulation/v1"


def consume_agent_economy_simulation(payload: dict[str, Any]) -> dict[str, Any]:
    mode = str(payload.get("mandate_mode", "")).lower()
    if mode not in {"simulation", "shadow", "live"}:
        raise ValueError("invalid mandate mode")
    if bool(payload.get("payment_authority")) or bool(payload.get("accounting_authority")):
        raise ValueError("agent economy evidence cannot self-promote authority")
    ext = Decimal(str(payload.get("external_assets", "0")))
    internal = Decimal(str(payload.get("internal_assets", "0")))
    revenue = Decimal(str(payload.get("external_revenue", "0")))
    if min(ext, internal, revenue) < 0:
        raise ValueError("negative simulation metric")
    return {
        "kind": "AGENT_ECONOMY_SIMULATION",
        "run_id": str(payload["run_id"]),
        "tick": int(payload["tick"]),
        "active_agents": int(payload["active_agents"]),
        "external_assets": str(ext),
        "internal_assets": str(internal),
        "external_revenue": str(revenue),
        "simulation_context_only": True,
        "authorization": False,
    }

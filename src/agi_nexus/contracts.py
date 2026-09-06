from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Literal


class NexusContractError(ValueError):
    pass


@dataclass(frozen=True)
class NexusPolicyProposal:
    proposal_id: str
    domain: str
    objective: str
    recommended_action: str
    confidence: float
    epistemic_state: Literal["KNOWN", "LEARNED", "INFERRED", "UNKNOWN"]
    constraints: tuple[str, ...] = field(default_factory=tuple)
    risk_flags: tuple[str, ...] = field(default_factory=tuple)
    expires_at: str | None = None

    execution_authority: str = "NONE"

    def __post_init__(self) -> None:
        if not 0 <= self.confidence <= 1:
            raise NexusContractError("confidence must be within [0, 1]")
        if not self.domain or not self.objective or not self.recommended_action:
            raise NexusContractError("domain, objective and recommended_action are required")
        if self.epistemic_state == "UNKNOWN" and self.confidence > 0.25:
            raise NexusContractError("UNKNOWN state cannot carry high confidence")

    def as_payload(self) -> dict:
        payload = asdict(self)
        payload.pop("execution_authority")
        payload.pop("epistemic_state")
        payload["constraints"] = list(self.constraints)
        payload["risk_flags"] = list(self.risk_flags)
        return payload

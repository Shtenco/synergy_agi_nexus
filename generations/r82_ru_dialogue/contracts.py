from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence, Tuple


class EpistemicState(str, Enum):
    KNOWN = "KNOWN"
    LEARNED_NOW = "LEARNED_NOW"
    DERIVED = "DERIVED"
    UNKNOWN = "UNKNOWN"
    HYPOTHESIS = "HYPOTHESIS"
    REJECTED = "REJECTED"


class Provenance(str, Enum):
    VERIFIED_NATIVE = "VERIFIED_NATIVE"
    USER_ASSERTED = "USER_ASSERTED"
    DERIVED = "DERIVED"
    TRUSTED_KNOWLEDGE = "TRUSTED_KNOWLEDGE"
    QUARANTINE_TEACHER = "QUARANTINE_TEACHER"
    GRAPH_RETRIEVAL = "GRAPH_RETRIEVAL"
    SYNTHETIC_TRAINING = "SYNTHETIC_TRAINING"
    UNKNOWN = "UNKNOWN"


class Relation(str, Enum):
    SUPPORTS = "SUPPORTS"
    CONTRADICTS = "CONTRADICTS"
    CAUSES = "CAUSES"
    REQUIRES = "REQUIRES"
    PRECEDES = "PRECEDES"
    MEASURED_BY = "MEASURED_BY"
    CONSTRAINED_BY = "CONSTRAINED_BY"
    REFERS_TO = "REFERS_TO"
    REVISES = "REVISES"
    DERIVED_FROM = "DERIVED_FROM"


@dataclass(frozen=True)
class Claim:
    claim_id: str
    subject: str
    predicate: str
    value: Any
    epistemic: EpistemicState
    provenance: Provenance
    confidence: float = 1.0
    source_id: Optional[str] = None
    lineage_id: Optional[str] = None
    valid_from_turn: Optional[int] = None
    supersedes: Tuple[str, ...] = ()


@dataclass(frozen=True)
class Evidence:
    evidence_id: str
    claim_id: str
    source_id: str
    lineage_id: str
    provenance: Provenance
    confidence: float
    verified: bool = False
    payload: Optional[Dict[str, Any]] = None


@dataclass(frozen=True)
class ClaimEdge:
    source_claim_id: str
    relation: Relation
    target_claim_id: str
    weight: float = 1.0


@dataclass
class HypothesisSet:
    hypothesis_ids: List[str] = field(default_factory=list)
    discriminating_question: Optional[str] = None
    resolved: bool = False


@dataclass(frozen=True)
class SemanticSegment:
    segment_id: str
    text: str
    entities: Tuple[str, ...] = ()
    metrics: Tuple[str, ...] = ()
    constraints: Tuple[str, ...] = ()
    temporal_markers: Tuple[str, ...] = ()


@dataclass
class ContextFrame:
    session_id: str
    turn_index: int = 0
    topic_id: Optional[str] = None
    validated_claim_ids: List[str] = field(default_factory=list)
    pending_slots: Dict[str, Any] = field(default_factory=dict)
    suspended_frames: List[Dict[str, Any]] = field(default_factory=list)
    unresolved_hypotheses: List[str] = field(default_factory=list)
    user_goal: Optional[str] = None
    short_summary: str = ""
    hard_boundary_epoch: int = 0


@dataclass(frozen=True)
class ReasoningTraceSummary:
    trajectory: str
    proposed_claim_ids: Tuple[str, ...]
    activated_node_ids: Tuple[int, ...] = ()
    proof_ids: Tuple[str, ...] = ()
    confidence: float = 0.0
    abstained: bool = False


@dataclass
class AnswerPlan:
    intent: str
    answerable: bool
    claim_ids: List[str] = field(default_factory=list)
    derived_values: List[Dict[str, Any]] = field(default_factory=list)
    unknowns: List[str] = field(default_factory=list)
    required_questions: List[str] = field(default_factory=list)
    recommended_structure: List[str] = field(default_factory=list)
    tone: str = "neutral"
    confidence: float = 0.0
    provenance_ids: List[str] = field(default_factory=list)
    allowed_entities: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class SurfaceDraft:
    text: str
    asserted_claim_ids: Tuple[str, ...]
    new_unmapped_assertions: Tuple[str, ...] = ()


@dataclass(frozen=True)
class VerificationResult:
    accepted: bool
    unsupported_assertions: Tuple[str, ...] = ()
    contradicted_claim_ids: Tuple[str, ...] = ()
    grammar_score: Optional[float] = None
    style_score: Optional[float] = None
    semantic_completeness: Optional[float] = None
    reason: str = ""


@dataclass
class DialogueResult:
    text: str
    answer_plan: AnswerPlan
    claims: List[Claim]
    reasoning_summaries: List[ReasoningTraceSummary]
    verification: VerificationResult
    context: ContextFrame


SOVEREIGN_PROVENANCE = {
    Provenance.VERIFIED_NATIVE,
}


def can_override(existing: Claim, incoming: Claim) -> bool:
    """Conservative authority rule.

    A non-sovereign incoming claim may not overwrite a verified-native claim.
    Explicit revision of user/session facts is handled by the epistemic memory,
    not by teacher or surface-model confidence.
    """
    if existing.provenance in SOVEREIGN_PROVENANCE:
        return incoming.provenance in SOVEREIGN_PROVENANCE
    if incoming.provenance == Provenance.QUARANTINE_TEACHER:
        return False
    return incoming.confidence >= existing.confidence


def independent_lineage_count(evidence: Sequence[Evidence]) -> int:
    """Correlated clones count as one lineage, not multiple witnesses."""
    return len({e.lineage_id for e in evidence})

from __future__ import annotations

"""Sovereign cybernetic-logical stack for NEXUS R8.2.

Promoted mechanisms, with their authority boundaries preserved:

R7.10  Proof-First / independent verification
R7.13  Hypothesis -> Test -> Feedback -> Hypothesis
R7.16  adaptive query / value-of-information scheduling
R7.17  recurrent workspace (state only; never truth authority)
R7.18  evidence credit and source contribution
R7.19  Safe AST / Program IR + stepwise exact verification
R7.21  structural world model + typed relation execution
R7.22  proof completeness
R7.23  typed graph semantics + algorithm/attribute completeness
R7.24  capability synthesis + capability proof
R7.25  prediction/error/revision/counterfactual loop
R7.26  semantic-obligation completeness
R7.27  abductive/probabilistic hypotheses (advisory)
R7.28  semantic applicability/full-utterance gate
R7.32  teacher-as-evidence sovereign Society-of-Minds
R7.33  claim/correlation-aware arbitration
R7.36  explicit epistemic states; conflict may remain UNKNOWN

No component in this module commits final truth. The result is a better
Claim/Evidence pool for the independent EpistemicGovernor in runtime.py.
"""

from dataclasses import dataclass, field
import ast
import math
from typing import Dict, List, Mapping, Optional, Protocol, Sequence, Tuple

from .contracts import (
    Claim,
    ContextFrame,
    EpistemicState,
    Evidence,
    Provenance,
    ReasoningTraceSummary,
)


class ReasoningOrganLike(Protocol):
    name: str

    def reason(
        self,
        graph_state: Dict[str, object],
        context: ContextFrame,
    ) -> tuple[Sequence[Claim], Sequence[Evidence], ReasoningTraceSummary]: ...


class ProofVerifierLike(Protocol):
    def verify_claim(self, claim: Claim, graph_state: Dict[str, object]) -> bool: ...


class AbductiveExpanderLike(Protocol):
    """Optional R7.27-style hypothesis expansion; proposals are never proofs."""

    def expand(
        self,
        claims: Sequence[Claim],
        evidence: Sequence[Evidence],
        graph_state: Dict[str, object],
        context: ContextFrame,
    ) -> Sequence[Claim]: ...


@dataclass(frozen=True)
class CompletenessCertificate:
    """R7.21-R7.28 promotion gates compressed into one explicit certificate.

    A certificate is deliberately strict. A runtime may omit it for legacy
    compatibility, but once supplied it becomes binding: evidence confidence
    cannot override a missing semantic/proof/capability obligation.
    """

    parse_complete: bool = False
    operators_consumed_fraction: float = 0.0
    state_consistent: bool = False
    unique_answer: bool = False
    world_type_known: bool = False
    attributes_consumed_fraction: float = 0.0
    objective_consumed_fraction: float = 0.0
    algorithm_matches_type: bool = False
    capabilities_available: bool = False
    plan_fully_executed: bool = False
    capability_proof_complete: bool = False
    semantic_obligation_coverage: float = 0.0
    domain_recognized: bool = False
    full_utterance_parsed: bool = False
    intent_parsed: bool = False
    no_unconsumed_semantic_content: bool = False
    world_model_complete: bool = False
    prediction_checked: bool = False
    no_open_contradiction: bool = False
    counterfactual_checked: bool = False

    @classmethod
    def from_graph_state(cls, graph_state: Mapping[str, object]) -> Optional["CompletenessCertificate"]:
        raw = graph_state.get("_completeness")
        if raw is None:
            return None
        if isinstance(raw, cls):
            return raw
        if isinstance(raw, Mapping):
            allowed = cls.__dataclass_fields__.keys()
            kwargs = {k: raw[k] for k in allowed if k in raw}
            return cls(**kwargs)
        raise TypeError("_completeness must be a mapping or CompletenessCertificate")

    def missing(self) -> Tuple[str, ...]:
        failed: List[str] = []
        boolean_checks = (
            "parse_complete",
            "state_consistent",
            "unique_answer",
            "world_type_known",
            "algorithm_matches_type",
            "capabilities_available",
            "plan_fully_executed",
            "capability_proof_complete",
            "domain_recognized",
            "full_utterance_parsed",
            "intent_parsed",
            "no_unconsumed_semantic_content",
            "world_model_complete",
            "prediction_checked",
            "no_open_contradiction",
            "counterfactual_checked",
        )
        for name in boolean_checks:
            if not bool(getattr(self, name)):
                failed.append(name)
        fraction_checks = (
            "operators_consumed_fraction",
            "attributes_consumed_fraction",
            "objective_consumed_fraction",
            "semantic_obligation_coverage",
        )
        for name in fraction_checks:
            if float(getattr(self, name)) < 1.0:
                failed.append(name)
        return tuple(failed)

    @property
    def verified_eligible(self) -> bool:
        return not self.missing()


@dataclass(frozen=True)
class EvidenceCredit:
    evidence_id: str
    claim_id: str
    raw_confidence: float
    provenance_weight: float
    lineage_weight: float
    verification_weight: float
    counterfactual_weight: float
    credit: float


@dataclass(frozen=True)
class TestProposal:
    target_claim_ids: Tuple[str, ...]
    instruction: str
    expected_information_gain: float
    reason: str


@dataclass
class CyberRound:
    index: int
    claims: List[Claim] = field(default_factory=list)
    evidence: List[Evidence] = field(default_factory=list)
    credits: List[EvidenceCredit] = field(default_factory=list)
    traces: List[ReasoningTraceSummary] = field(default_factory=list)
    proposal: Optional[TestProposal] = None
    stop_reason: str = ""
    completeness_missing: Tuple[str, ...] = ()


@dataclass
class CyberRunResult:
    claims: List[Claim]
    evidence: List[Evidence]
    traces: List[ReasoningTraceSummary]
    rounds: List[CyberRound]
    stopped_by: str
    completeness: Optional[CompletenessCertificate] = None


_PROVENANCE_WEIGHT: Mapping[Provenance, float] = {
    Provenance.VERIFIED_NATIVE: 1.00,
    Provenance.DERIVED: 0.95,
    Provenance.USER_ASSERTED: 0.80,
    Provenance.TRUSTED_KNOWLEDGE: 0.78,
    Provenance.GRAPH_RETRIEVAL: 0.55,
    Provenance.QUARANTINE_TEACHER: 0.42,
    Provenance.SYNTHETIC_TRAINING: 0.20,
    Provenance.UNKNOWN: 0.10,
}


class EvidenceCreditScorer:
    """Correlation-aware evidence credit.

    Repeated evidence from one lineage shares a finite budget. A verified item
    can gain weight, but quarantined teacher confidence never becomes sovereign
    authority merely by repetition.
    """

    def score(self, evidence: Sequence[Evidence]) -> List[EvidenceCredit]:
        lineage_counts: Dict[str, int] = {}
        claim_counts: Dict[str, int] = {}
        for item in evidence:
            lineage_counts[item.lineage_id] = lineage_counts.get(item.lineage_id, 0) + 1
            claim_counts[item.claim_id] = claim_counts.get(item.claim_id, 0) + 1

        out: List[EvidenceCredit] = []
        for item in evidence:
            raw = min(1.0, max(0.0, float(item.confidence)))
            provenance = _PROVENANCE_WEIGHT.get(item.provenance, 0.10)
            lineage_weight = 1.0 / math.sqrt(max(1, lineage_counts[item.lineage_id]))
            verification = 1.12 if item.verified else 1.0
            counterfactual = 1.0 / math.sqrt(max(1, claim_counts[item.claim_id]))
            credit = raw * provenance * lineage_weight * verification * counterfactual
            out.append(
                EvidenceCredit(
                    evidence_id=item.evidence_id,
                    claim_id=item.claim_id,
                    raw_confidence=raw,
                    provenance_weight=provenance,
                    lineage_weight=lineage_weight,
                    verification_weight=verification,
                    counterfactual_weight=counterfactual,
                    credit=credit,
                )
            )
        return out


class ValueOfInformationPolicy:
    """R7.16-style decision: is another discriminating test worth its cost?"""

    def __init__(self, *, min_gain: float = 0.08) -> None:
        self.min_gain = float(min_gain)

    @staticmethod
    def _claim_scores(credits: Sequence[EvidenceCredit]) -> Dict[str, float]:
        scores: Dict[str, float] = {}
        for row in credits:
            scores[row.claim_id] = scores.get(row.claim_id, 0.0) + row.credit
        return scores

    def propose(
        self,
        claims: Sequence[Claim],
        evidence: Sequence[Evidence],
        credits: Sequence[EvidenceCredit],
        *,
        round_index: int,
        max_rounds: int,
    ) -> Optional[TestProposal]:
        if round_index + 1 >= max_rounds:
            return None
        scores = self._claim_scores(credits)
        ranked = sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))
        if not ranked:
            return TestProposal(
                target_claim_ids=tuple(c.claim_id for c in claims[:2]),
                instruction="Получить независимое проверяемое свидетельство для различения гипотез.",
                expected_information_gain=1.0,
                reason="no_scored_evidence",
            )

        top = ranked[0][1]
        second = ranked[1][1] if len(ranked) > 1 else 0.0
        margin = top - second
        lineages_by_claim: Dict[str, set[str]] = {}
        for item in evidence:
            lineages_by_claim.setdefault(item.claim_id, set()).add(item.lineage_id)
        top_lineages = len(lineages_by_claim.get(ranked[0][0], set()))
        ambiguity = max(0.0, 1.0 - min(1.0, margin))
        lineage_gap = 0.35 if top_lineages < 2 else 0.0
        expected_gain = min(1.0, 0.65 * ambiguity + lineage_gap)
        if expected_gain < self.min_gain:
            return None
        return TestProposal(
            target_claim_ids=tuple(k for k, _ in ranked[:2]),
            instruction=(
                "Собрать независимое evidence, которое различает конкурирующие гипотезы; "
                "предпочтительно другой lineage и проверяемый тест."
            ),
            expected_information_gain=expected_gain,
            reason="low_margin_or_insufficient_independent_lineage",
        )


class DefaultCyberneticSociety:
    """Iterative H -> T -> E -> H reasoning society with fail-closed gates."""

    def __init__(
        self,
        *,
        max_rounds: int = 3,
        min_independent_lineages: int = 2,
        stop_margin: float = 0.30,
        scorer: Optional[EvidenceCreditScorer] = None,
        voi_policy: Optional[ValueOfInformationPolicy] = None,
        abductive_expander: Optional[AbductiveExpanderLike] = None,
    ) -> None:
        self.max_rounds = max(1, int(max_rounds))
        self.min_independent_lineages = max(1, int(min_independent_lineages))
        self.stop_margin = float(stop_margin)
        self.scorer = scorer or EvidenceCreditScorer()
        self.voi = voi_policy or ValueOfInformationPolicy()
        self.abductive_expander = abductive_expander

    @staticmethod
    def _dedupe_claims(claims: Sequence[Claim]) -> List[Claim]:
        best: Dict[str, Claim] = {}
        for claim in claims:
            cur = best.get(claim.claim_id)
            if cur is None or claim.confidence > cur.confidence:
                best[claim.claim_id] = claim
        return list(best.values())

    @staticmethod
    def _dedupe_evidence(evidence: Sequence[Evidence]) -> List[Evidence]:
        best: Dict[str, Evidence] = {}
        for item in evidence:
            cur = best.get(item.evidence_id)
            if cur is None or item.confidence > cur.confidence:
                best[item.evidence_id] = item
        return list(best.values())

    @staticmethod
    def _has_sovereign(claims: Sequence[Claim]) -> bool:
        return any(c.provenance == Provenance.VERIFIED_NATIVE for c in claims)

    def _verified_claims(
        self,
        claims: Sequence[Claim],
        verifier: ProofVerifierLike,
        graph_state: Dict[str, object],
    ) -> List[Claim]:
        verified: List[Claim] = []
        for claim in claims:
            if claim.epistemic == EpistemicState.DERIVED:
                if verifier.verify_claim(claim, graph_state):
                    verified.append(claim)
            else:
                verified.append(claim)
        return verified

    def _enough_to_stop(
        self,
        claims: Sequence[Claim],
        evidence: Sequence[Evidence],
        credits: Sequence[EvidenceCredit],
        graph_state: Mapping[str, object],
    ) -> tuple[bool, str]:
        certificate = CompletenessCertificate.from_graph_state(graph_state)
        if certificate is not None and not certificate.verified_eligible:
            return False, "completeness_gate_open"
        if self._has_sovereign(claims):
            return True, "verified_native_authority"

        scores: Dict[str, float] = {}
        for row in credits:
            scores[row.claim_id] = scores.get(row.claim_id, 0.0) + row.credit
        if not scores:
            return False, "no_evidence"
        ranked = sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))
        top_id, top_score = ranked[0]
        second = ranked[1][1] if len(ranked) > 1 else 0.0
        independent = len({e.lineage_id for e in evidence if e.claim_id == top_id})
        if independent >= self.min_independent_lineages and top_score - second >= self.stop_margin:
            return True, "independent_margin"
        return False, "continue_for_information"

    @staticmethod
    def _completeness_proposal(
        certificate: CompletenessCertificate,
        claims: Sequence[Claim],
        *,
        round_index: int,
        max_rounds: int,
    ) -> Optional[TestProposal]:
        if round_index + 1 >= max_rounds:
            return None
        missing = certificate.missing()
        return TestProposal(
            target_claim_ids=tuple(c.claim_id for c in claims[:3]),
            instruction="Закрыть непокрытые обязательства: " + ", ".join(missing),
            expected_information_gain=1.0,
            reason="incomplete_semantic_or_proof_obligations",
        )

    def run(
        self,
        graph_state: Dict[str, object],
        context: ContextFrame,
        reasoning_organs: Sequence[ReasoningOrganLike],
        proof_verifier: ProofVerifierLike,
    ) -> CyberRunResult:
        state: Dict[str, object] = dict(graph_state)
        all_claims: List[Claim] = []
        all_evidence: List[Evidence] = []
        all_traces: List[ReasoningTraceSummary] = []
        history: List[CyberRound] = []
        stopped_by = "max_rounds"

        for round_index in range(self.max_rounds):
            round_claims: List[Claim] = []
            round_evidence: List[Evidence] = []
            round_traces: List[ReasoningTraceSummary] = []

            for organ in reasoning_organs:
                claims, evidence, trace = organ.reason(state, context)
                round_claims.extend(claims)
                round_evidence.extend(evidence)
                round_traces.append(trace)

            round_claims = self._verified_claims(round_claims, proof_verifier, state)
            accepted_ids = {c.claim_id for c in round_claims}
            round_evidence = [e for e in round_evidence if e.claim_id in accepted_ids]

            all_claims = self._dedupe_claims([*all_claims, *round_claims])
            all_evidence = self._dedupe_evidence([*all_evidence, *round_evidence])

            if self.abductive_expander is not None:
                expanded = list(self.abductive_expander.expand(all_claims, all_evidence, state, context))
                # R7.27 expansion is advisory: force generated candidates to
                # remain hypotheses even if a custom expander overclaims them.
                safe_expanded: List[Claim] = []
                for c in expanded:
                    safe_expanded.append(
                        Claim(
                            claim_id=c.claim_id,
                            subject=c.subject,
                            predicate=c.predicate,
                            value=c.value,
                            epistemic=EpistemicState.HYPOTHESIS,
                            provenance=(
                                c.provenance
                                if c.provenance != Provenance.VERIFIED_NATIVE
                                else Provenance.UNKNOWN
                            ),
                            confidence=min(float(c.confidence), 0.95),
                            dependencies=c.dependencies,
                        )
                    )
                all_claims = self._dedupe_claims([*all_claims, *safe_expanded])

            all_traces.extend(round_traces)
            credits = self.scorer.score(all_evidence)
            should_stop, reason = self._enough_to_stop(all_claims, all_evidence, credits, state)

            certificate = CompletenessCertificate.from_graph_state(state)
            proposal: Optional[TestProposal] = None
            if not should_stop:
                if reason == "completeness_gate_open" and certificate is not None:
                    proposal = self._completeness_proposal(
                        certificate,
                        all_claims,
                        round_index=round_index,
                        max_rounds=self.max_rounds,
                    )
                else:
                    proposal = self.voi.propose(
                        all_claims,
                        all_evidence,
                        credits,
                        round_index=round_index,
                        max_rounds=self.max_rounds,
                    )

            history.append(
                CyberRound(
                    index=round_index,
                    claims=list(round_claims),
                    evidence=list(round_evidence),
                    credits=list(credits),
                    traces=list(round_traces),
                    proposal=proposal,
                    stop_reason=reason if should_stop else "",
                    completeness_missing=certificate.missing() if certificate is not None else (),
                )
            )

            if should_stop:
                stopped_by = reason
                break
            if proposal is None:
                stopped_by = (
                    "incomplete_at_budget_limit"
                    if reason == "completeness_gate_open"
                    else "no_positive_value_of_information"
                )
                break

            state = dict(state)
            state["_cyber"] = {
                "round": round_index + 1,
                "target_claim_ids": proposal.target_claim_ids,
                "instruction": proposal.instruction,
                "expected_information_gain": proposal.expected_information_gain,
                "prior_claim_ids": tuple(c.claim_id for c in all_claims),
                "prior_evidence_ids": tuple(e.evidence_id for e in all_evidence),
            }

        return CyberRunResult(
            claims=all_claims,
            evidence=all_evidence,
            traces=all_traces,
            rounds=history,
            stopped_by=stopped_by,
            completeness=CompletenessCertificate.from_graph_state(state),
        )


# ---------------------------------------------------------------------------
# R7.19-inspired deterministic Program IR. Fail closed: this is an exact
# mechanism organ, not a natural-language parser and not a general Python VM.
# ---------------------------------------------------------------------------

_ALLOWED_BINOPS = {
    ast.Add: lambda a, b: a + b,
    ast.Sub: lambda a, b: a - b,
    ast.Mult: lambda a, b: a * b,
    ast.Div: lambda a, b: a / b,
    ast.FloorDiv: lambda a, b: a // b,
    ast.Mod: lambda a, b: a % b,
    ast.Pow: lambda a, b: a**b,
}
_ALLOWED_UNARY = {ast.UAdd: lambda a: +a, ast.USub: lambda a: -a}


class SafeArithmeticEvaluator:
    def __init__(self, *, max_nodes: int = 64, max_abs_exponent: int = 12) -> None:
        self.max_nodes = int(max_nodes)
        self.max_abs_exponent = int(max_abs_exponent)

    def evaluate(self, expression: str) -> float:
        tree = ast.parse(expression, mode="eval")
        if len(list(ast.walk(tree))) > self.max_nodes:
            raise ValueError("program too large")
        value = self._eval(tree.body)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError("non-numeric result")
        if not math.isfinite(float(value)):
            raise ValueError("non-finite result")
        return float(value)

    def _eval(self, node: ast.AST) -> float:
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
            return float(node.value)
        if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_UNARY:
            return float(_ALLOWED_UNARY[type(node.op)](self._eval(node.operand)))
        if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_BINOPS:
            left = self._eval(node.left)
            right = self._eval(node.right)
            if isinstance(node.op, ast.Pow) and abs(right) > self.max_abs_exponent:
                raise ValueError("exponent outside limit")
            return float(_ALLOWED_BINOPS[type(node.op)](left, right))
        raise ValueError(f"unsupported AST node: {type(node).__name__}")


@dataclass(frozen=True)
class ProgramStep:
    expression: str
    expected: float
    tolerance: float = 1e-9


class StepwiseProgramVerifier:
    def __init__(self, evaluator: Optional[SafeArithmeticEvaluator] = None) -> None:
        self.evaluator = evaluator or SafeArithmeticEvaluator()

    def verify(self, steps: Sequence[ProgramStep]) -> tuple[bool, Optional[float], int]:
        if not steps:
            return False, None, -1
        last: Optional[float] = None
        for index, step in enumerate(steps):
            try:
                value = self.evaluator.evaluate(step.expression)
            except Exception:
                return False, last, index
            if abs(value - float(step.expected)) > max(0.0, float(step.tolerance)):
                return False, value, index
            last = value
        return True, last, len(steps) - 1

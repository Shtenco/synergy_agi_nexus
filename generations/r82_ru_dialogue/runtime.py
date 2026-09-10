from __future__ import annotations

from dataclasses import replace
from typing import Dict, Iterable, List, Optional, Protocol, Sequence

from .contracts import (
    AnswerPlan,
    Claim,
    ContextFrame,
    DialogueResult,
    Evidence,
    ReasoningTraceSummary,
    SemanticSegment,
    SurfaceDraft,
    VerificationResult,
    independent_lineage_count,
)


class ContextBinder(Protocol):
    def bind(self, text: str, context: ContextFrame) -> ContextFrame: ...


class Segmenter(Protocol):
    def segment(self, text: str, context: ContextFrame) -> Sequence[SemanticSegment]: ...


class CognitiveGraphBrain(Protocol):
    def encode_segments(
        self,
        segments: Sequence[SemanticSegment],
        context: ContextFrame,
    ) -> Dict[str, object]: ...


class ReasoningOrgan(Protocol):
    name: str

    def reason(
        self,
        graph_state: Dict[str, object],
        context: ContextFrame,
    ) -> tuple[Sequence[Claim], Sequence[Evidence], ReasoningTraceSummary]: ...


class ProofVerifier(Protocol):
    def verify_claim(self, claim: Claim, graph_state: Dict[str, object]) -> bool: ...


class CyberneticSociety(Protocol):
    """Optional iterative H->T->E->H controller.

    It can run several reasoning rounds and request discriminating internal
    tests, but it is not the final truth authority. The returned pool is still
    passed through ProofVerifier and EpistemicGovernor.
    """

    def run(
        self,
        graph_state: Dict[str, object],
        context: ContextFrame,
        reasoning_organs: Sequence[ReasoningOrgan],
        proof_verifier: ProofVerifier,
    ) -> object: ...


class EpistemicGovernor(Protocol):
    def arbitrate(
        self,
        claims: Sequence[Claim],
        evidence: Sequence[Evidence],
        graph_state: Dict[str, object],
        context: ContextFrame,
    ) -> tuple[Sequence[Claim], AnswerPlan, ContextFrame]: ...


class SurfaceCortex(Protocol):
    def realize(
        self,
        plan: AnswerPlan,
        claims: Sequence[Claim],
        context: ContextFrame,
    ) -> SurfaceDraft: ...


class SurfaceVerifier(Protocol):
    def verify(
        self,
        draft: SurfaceDraft,
        plan: AnswerPlan,
        claims: Sequence[Claim],
        context: ContextFrame,
    ) -> VerificationResult: ...


class NexusR82:
    """Sovereign cognitive-dialogue runtime.

    The surface generator never receives authority to change the approved
    ClaimSet. A fluent answer is committed only after surface verification.

    When ``cybernetic_society`` is present, the reasoning phase is iterative:
    Hypothesis -> discriminating Test/Query -> Evidence -> revised Hypothesis.
    This restores the strongest R7.13/R7.16/R7.18/R7.19/R7.33 mechanism while
    keeping final authority in the verifier/governor path.
    """

    def __init__(
        self,
        *,
        context_binder: ContextBinder,
        segmenter: Segmenter,
        graph_brain: CognitiveGraphBrain,
        reasoning_organs: Sequence[ReasoningOrgan],
        proof_verifier: ProofVerifier,
        epistemic_governor: EpistemicGovernor,
        surface_cortex: SurfaceCortex,
        surface_verifier: SurfaceVerifier,
        cybernetic_society: Optional[CyberneticSociety] = None,
        max_surface_attempts: int = 3,
    ) -> None:
        if not reasoning_organs:
            raise ValueError("R8.2 requires at least one reasoning organ")
        self.context_binder = context_binder
        self.segmenter = segmenter
        self.graph_brain = graph_brain
        self.reasoning_organs = list(reasoning_organs)
        self.proof_verifier = proof_verifier
        self.epistemic_governor = epistemic_governor
        self.surface_cortex = surface_cortex
        self.surface_verifier = surface_verifier
        self.cybernetic_society = cybernetic_society
        self.max_surface_attempts = max(1, int(max_surface_attempts))

    def _reason(
        self,
        graph_state: Dict[str, object],
        context: ContextFrame,
    ) -> tuple[List[Claim], List[Evidence], List[ReasoningTraceSummary]]:
        if self.cybernetic_society is not None:
            result = self.cybernetic_society.run(
                graph_state,
                context,
                self.reasoning_organs,
                self.proof_verifier,
            )
            # Structural duck-typing keeps runtime independent of a particular
            # cybernetic implementation while preserving the public protocol.
            return list(result.claims), list(result.evidence), list(result.traces)

        all_claims: List[Claim] = []
        all_evidence: List[Evidence] = []
        traces: List[ReasoningTraceSummary] = []
        for organ in self.reasoning_organs:
            claims, evidence, trace = organ.reason(graph_state, context)
            all_claims.extend(claims)
            all_evidence.extend(evidence)
            traces.append(trace)
        return all_claims, all_evidence, traces

    def respond(self, text: str, context: ContextFrame) -> DialogueResult:
        if not text.strip():
            raise ValueError("empty user turn")

        bound = self.context_binder.bind(text, context)
        segments = list(self.segmenter.segment(text, bound))
        if not segments:
            raise RuntimeError("segmenter produced no semantic segments")

        graph_state = self.graph_brain.encode_segments(segments, bound)
        all_claims, all_evidence, traces = self._reason(graph_state, bound)

        # Proof-verifiable claims are checked again immediately before governor
        # promotion. The duplicate boundary is intentional defense-in-depth:
        # even a custom cybernetic society cannot bypass sovereign verification.
        verified_claims: List[Claim] = []
        for claim in all_claims:
            if claim.epistemic.value == "DERIVED":
                if self.proof_verifier.verify_claim(claim, graph_state):
                    verified_claims.append(claim)
            else:
                verified_claims.append(claim)

        accepted_ids = {claim.claim_id for claim in verified_claims}
        all_evidence = [e for e in all_evidence if e.claim_id in accepted_ids]

        approved_claims, plan, updated_context = self.epistemic_governor.arbitrate(
            verified_claims,
            all_evidence,
            graph_state,
            bound,
        )

        # Hard surface firewall: any unmapped factual assertion is a failure.
        last_verification = VerificationResult(
            accepted=False,
            reason="surface generation not attempted",
        )

        for _ in range(self.max_surface_attempts):
            draft = self.surface_cortex.realize(plan, approved_claims, updated_context)
            result = self.surface_verifier.verify(
                draft,
                plan,
                approved_claims,
                updated_context,
            )
            last_verification = result
            if result.accepted and not draft.new_unmapped_assertions:
                return DialogueResult(
                    text=draft.text,
                    answer_plan=plan,
                    claims=list(approved_claims),
                    reasoning_summaries=traces,
                    verification=result,
                    context=replace(updated_context, turn_index=updated_context.turn_index + 1),
                )

        # Fail closed. A pretty answer with unsupported claims is worse than an
        # explicit bounded failure/clarification request.
        fallback = self._safe_fallback(plan, last_verification)
        return DialogueResult(
            text=fallback,
            answer_plan=plan,
            claims=list(approved_claims),
            reasoning_summaries=traces,
            verification=last_verification,
            context=replace(updated_context, turn_index=updated_context.turn_index + 1),
        )

    @staticmethod
    def _safe_fallback(plan: AnswerPlan, verification: VerificationResult) -> str:
        if plan.required_questions:
            return plan.required_questions[0]
        if plan.unknowns:
            return "Для точного ответа пока не хватает проверяемой информации."
        if verification.unsupported_assertions:
            return "Я не буду добавлять непроверенные утверждения к подтверждённой части ответа."
        return "Не удалось сформулировать ответ без нарушения проверяемых ограничений."


def lineage_diversity(evidence: Iterable[Evidence]) -> int:
    """Public helper used by Society-of-Minds arbitration tests."""
    return independent_lineage_count(list(evidence))

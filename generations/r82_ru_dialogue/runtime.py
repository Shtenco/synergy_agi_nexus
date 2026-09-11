from __future__ import annotations

from dataclasses import replace
from typing import Dict, Iterable, List, Optional, Protocol, Sequence

from .contracts import (
    AnswerPlan,
    Claim,
    ContextFrame,
    DialogueResult,
    EpistemicState,
    Evidence,
    Provenance,
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


class ResearchBroker(Protocol):
    """R8.3 external research organ.

    The broker may search web/papers/datasets/repos and return candidate
    claims/evidence. Runtime sanitizes every returned object so research can
    never mint VERIFIED_NATIVE authority for itself.
    """

    def research(
        self,
        text: str,
        unknowns: Sequence[str],
        graph_state: Dict[str, object],
        context: ContextFrame,
    ) -> tuple[Sequence[Claim], Sequence[Evidence], Optional[ReasoningTraceSummary]]: ...


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

    When ``research_broker`` is present and the first epistemic pass exposes
    unresolved external unknowns, R8.2 may run exactly one bounded R8.3
    research cycle, ingest its claims as LEARNED_NOW/TRUSTED_KNOWLEDGE, and
    re-arbitrate. External research never receives VERIFIED_NATIVE authority.
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
        research_broker: Optional[ResearchBroker] = None,
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
        self.research_broker = research_broker
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

    def _proof_filter(
        self,
        claims: Sequence[Claim],
        evidence: Sequence[Evidence],
        graph_state: Dict[str, object],
    ) -> tuple[List[Claim], List[Evidence]]:
        verified_claims: List[Claim] = []
        for claim in claims:
            if claim.epistemic == EpistemicState.DERIVED:
                if self.proof_verifier.verify_claim(claim, graph_state):
                    verified_claims.append(claim)
            else:
                verified_claims.append(claim)
        accepted_ids = {claim.claim_id for claim in verified_claims}
        return verified_claims, [e for e in evidence if e.claim_id in accepted_ids]

    @staticmethod
    def _sanitize_research_claim(claim: Claim) -> Claim:
        # Web/research output can be learned evidence or a hypothesis, never a
        # self-minted sovereign fact. DERIVED is preserved so ProofVerifier can
        # still validate calculations reproduced by the research agent.
        epistemic = claim.epistemic
        if epistemic == EpistemicState.KNOWN:
            epistemic = EpistemicState.LEARNED_NOW
        provenance = claim.provenance
        if provenance == Provenance.VERIFIED_NATIVE:
            provenance = Provenance.TRUSTED_KNOWLEDGE
        return replace(
            claim,
            epistemic=epistemic,
            provenance=provenance,
            confidence=min(0.999, max(0.0, float(claim.confidence))),
        )

    @staticmethod
    def _sanitize_research_evidence(evidence: Evidence) -> Evidence:
        provenance = evidence.provenance
        if provenance == Provenance.VERIFIED_NATIVE:
            provenance = Provenance.TRUSTED_KNOWLEDGE
        return replace(
            evidence,
            provenance=provenance,
            confidence=min(0.999, max(0.0, float(evidence.confidence))),
            verified=False,
        )

    def _research_once(
        self,
        text: str,
        plan: AnswerPlan,
        graph_state: Dict[str, object],
        context: ContextFrame,
        claims: Sequence[Claim],
        evidence: Sequence[Evidence],
        traces: Sequence[ReasoningTraceSummary],
    ) -> tuple[List[Claim], List[Evidence], List[ReasoningTraceSummary]]:
        if self.research_broker is None:
            return list(claims), list(evidence), list(traces)
        unknowns = list(plan.unknowns) + list(plan.required_questions)
        if not unknowns:
            return list(claims), list(evidence), list(traces)

        r_claims, r_evidence, r_trace = self.research_broker.research(
            text,
            unknowns,
            graph_state,
            context,
        )
        safe_claims = [self._sanitize_research_claim(c) for c in r_claims]
        safe_evidence = [self._sanitize_research_evidence(e) for e in r_evidence]
        merged_claims, merged_evidence = self._proof_filter(
            [*claims, *safe_claims],
            [*evidence, *safe_evidence],
            graph_state,
        )
        merged_traces = list(traces)
        if r_trace is not None:
            merged_traces.append(r_trace)
        return merged_claims, merged_evidence, merged_traces

    def respond(self, text: str, context: ContextFrame) -> DialogueResult:
        if not text.strip():
            raise ValueError("empty user turn")

        bound = self.context_binder.bind(text, context)
        segments = list(self.segmenter.segment(text, bound))
        if not segments:
            raise RuntimeError("segmenter produced no semantic segments")

        graph_state = self.graph_brain.encode_segments(segments, bound)
        all_claims, all_evidence, traces = self._reason(graph_state, bound)
        verified_claims, all_evidence = self._proof_filter(all_claims, all_evidence, graph_state)

        approved_claims, plan, updated_context = self.epistemic_governor.arbitrate(
            verified_claims,
            all_evidence,
            graph_state,
            bound,
        )

        # External research is an active inquiry organ, not an answer bypass.
        # Run once only after the sovereign governor exposes concrete unknowns.
        if self.research_broker is not None and (plan.unknowns or plan.required_questions):
            researched_claims, researched_evidence, traces = self._research_once(
                text,
                plan,
                graph_state,
                updated_context,
                verified_claims,
                all_evidence,
                traces,
            )
            approved_claims, plan, updated_context = self.epistemic_governor.arbitrate(
                researched_claims,
                researched_evidence,
                graph_state,
                updated_context,
            )

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

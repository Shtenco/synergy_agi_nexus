from __future__ import annotations

import unittest

from .contracts import (
    AnswerPlan,
    Claim,
    ContextFrame,
    EpistemicState,
    Evidence,
    Provenance,
    ReasoningTraceSummary,
    SemanticSegment,
    SurfaceDraft,
    VerificationResult,
    can_override,
    independent_lineage_count,
)
from .runtime import NexusR82


class _Binder:
    def bind(self, text, context):
        return context


class _Segmenter:
    def segment(self, text, context):
        return [SemanticSegment("s1", text)]


class _Brain:
    def encode_segments(self, segments, context):
        return {"segments": list(segments)}


class _Organ:
    name = "proof-first"

    def reason(self, graph_state, context):
        claim = Claim(
            "approved", "result", "equals", 4,
            EpistemicState.DERIVED, Provenance.DERIVED, 1.0,
        )
        ev = Evidence(
            "ev", "approved", "native", "native",
            Provenance.VERIFIED_NATIVE, 1.0, verified=True,
        )
        tr = ReasoningTraceSummary("proof-first", ("approved",), confidence=1.0)
        return [claim], [ev], tr


class _Proof:
    def verify_claim(self, claim, graph_state):
        return claim.claim_id == "approved"


class _Governor:
    def arbitrate(self, claims, evidence, graph_state, context):
        plan = AnswerPlan(
            intent="answer",
            answerable=True,
            claim_ids=[c.claim_id for c in claims],
            confidence=1.0,
        )
        return list(claims), plan, context


class _BadSurface:
    def realize(self, plan, claims, context):
        return SurfaceDraft(
            text="Ответ 4. И ещё неподтверждённый факт.",
            asserted_claim_ids=("approved",),
            new_unmapped_assertions=("invented fact",),
        )


class _RejectUnsupported:
    def verify(self, draft, plan, claims, context):
        return VerificationResult(
            accepted=not draft.new_unmapped_assertions,
            unsupported_assertions=draft.new_unmapped_assertions,
            reason="unmapped factual assertion" if draft.new_unmapped_assertions else "ok",
        )


class RuntimeContracts(unittest.TestCase):
    def test_verified_native_cannot_be_overwritten_by_teacher(self):
        verified = Claim(
            "c1", "math", "equals", 4,
            EpistemicState.KNOWN, Provenance.VERIFIED_NATIVE, 1.0,
        )
        teacher = Claim(
            "c2", "math", "equals", 5,
            EpistemicState.HYPOTHESIS, Provenance.QUARANTINE_TEACHER, 0.999999,
        )
        self.assertFalse(can_override(verified, teacher))

    def test_correlated_clones_count_as_one_lineage(self):
        items = [
            Evidence("e1", "c", "teacher-a", "same-family", Provenance.QUARANTINE_TEACHER, 0.9),
            Evidence("e2", "c", "teacher-b", "same-family", Provenance.QUARANTINE_TEACHER, 0.95),
            Evidence("e3", "c", "teacher-c", "independent-family", Provenance.QUARANTINE_TEACHER, 0.8),
        ]
        self.assertEqual(independent_lineage_count(items), 2)

    def test_surface_generator_cannot_commit_unmapped_fact(self):
        nexus = NexusR82(
            context_binder=_Binder(),
            segmenter=_Segmenter(),
            graph_brain=_Brain(),
            reasoning_organs=[_Organ()],
            proof_verifier=_Proof(),
            epistemic_governor=_Governor(),
            surface_cortex=_BadSurface(),
            surface_verifier=_RejectUnsupported(),
            max_surface_attempts=1,
        )
        result = nexus.respond("Сколько 2+2?", ContextFrame("session"))
        self.assertFalse(result.verification.accepted)
        self.assertIn("не буду добавлять непроверенные", result.text)
        self.assertNotIn("неподтверждённый факт", result.text)


if __name__ == "__main__":
    unittest.main()

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
)
from .runtime import NexusR82


class Binder:
    def bind(self, text, context): return context


class Segmenter:
    def segment(self, text, context): return [SemanticSegment("s", text)]


class Brain:
    def encode_segments(self, segments, context): return {"segments": segments}


class EmptyOrgan:
    name = "empty"
    def reason(self, graph_state, context):
        return [], [], ReasoningTraceSummary("empty", (), abstained=True)


class Verifier:
    def verify_claim(self, claim, graph_state): return True


class Governor:
    def __init__(self): self.calls = 0
    def arbitrate(self, claims, evidence, graph_state, context):
        self.calls += 1
        if not claims:
            return [], AnswerPlan("research", False, unknowns=["external fact missing"]), context
        return list(claims), AnswerPlan("answer", True, claim_ids=[c.claim_id for c in claims]), context


class Broker:
    def __init__(self): self.calls = 0
    def research(self, text, unknowns, graph_state, context):
        self.calls += 1
        # Deliberately overclaim sovereign authority; runtime must demote it.
        c = Claim(
            "web-c", "external", "equals", "candidate",
            EpistemicState.KNOWN, Provenance.VERIFIED_NATIVE, 1.0,
            source_id="web-src", lineage_id="publisher-A",
        )
        e = Evidence(
            "web-e", "web-c", "web-src", "publisher-A",
            Provenance.VERIFIED_NATIVE, 1.0, verified=True,
        )
        t = ReasoningTraceSummary("r83-research", ("web-c",), confidence=1.0)
        return [c], [e], t


class Surface:
    def realize(self, plan, claims, context):
        return SurfaceDraft("Исследование вернуло кандидатное утверждение.", tuple(c.claim_id for c in claims))


class SurfaceVerifier:
    def verify(self, draft, plan, claims, context): return VerificationResult(True, reason="ok")


class ResearchBridgeContracts(unittest.TestCase):
    def test_research_runs_only_after_governor_exposes_unknown(self):
        broker = Broker()
        governor = Governor()
        nexus = NexusR82(
            context_binder=Binder(), segmenter=Segmenter(), graph_brain=Brain(),
            reasoning_organs=[EmptyOrgan()], proof_verifier=Verifier(),
            epistemic_governor=governor, surface_cortex=Surface(),
            surface_verifier=SurfaceVerifier(), research_broker=broker,
        )
        result = nexus.respond("Найди внешний факт", ContextFrame("s"))
        self.assertEqual(broker.calls, 1)
        self.assertEqual(governor.calls, 2)
        self.assertEqual(len(result.claims), 1)

    def test_research_cannot_mint_verified_native(self):
        broker = Broker()
        nexus = NexusR82(
            context_binder=Binder(), segmenter=Segmenter(), graph_brain=Brain(),
            reasoning_organs=[EmptyOrgan()], proof_verifier=Verifier(),
            epistemic_governor=Governor(), surface_cortex=Surface(),
            surface_verifier=SurfaceVerifier(), research_broker=broker,
        )
        result = nexus.respond("Найди внешний факт", ContextFrame("s"))
        claim = result.claims[0]
        self.assertEqual(claim.epistemic, EpistemicState.LEARNED_NOW)
        self.assertEqual(claim.provenance, Provenance.TRUSTED_KNOWLEDGE)
        self.assertLess(claim.confidence, 1.0)


if __name__ == "__main__":
    unittest.main()

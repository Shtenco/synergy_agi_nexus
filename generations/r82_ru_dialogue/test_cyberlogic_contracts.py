from __future__ import annotations

import unittest

from .contracts import Claim, ContextFrame, EpistemicState, Evidence, Provenance, ReasoningTraceSummary
from .cyberlogic import (
    CompletenessCertificate,
    DefaultCyberneticSociety,
    EvidenceCreditScorer,
    ProgramStep,
    SafeArithmeticEvaluator,
    StepwiseProgramVerifier,
)

CTX = ContextFrame(session_id="cyber-test")


def claim(cid, *, epistemic=EpistemicState.HYPOTHESIS, provenance=Provenance.TRUSTED_KNOWLEDGE, confidence=0.8):
    return Claim(cid, "task", "answer", cid, epistemic, provenance, confidence)


def evidence(eid, cid, lineage, confidence=0.8):
    return Evidence(eid, cid, eid, lineage, Provenance.TRUSTED_KNOWLEDGE, confidence, verified=False)


def complete_certificate(**overrides):
    values = dict(
        parse_complete=True, operators_consumed_fraction=1.0, state_consistent=True,
        unique_answer=True, world_type_known=True, attributes_consumed_fraction=1.0,
        objective_consumed_fraction=1.0, algorithm_matches_type=True,
        capabilities_available=True, plan_fully_executed=True,
        capability_proof_complete=True, semantic_obligation_coverage=1.0,
        domain_recognized=True, full_utterance_parsed=True, intent_parsed=True,
        no_unconsumed_semantic_content=True, world_model_complete=True,
        prediction_checked=True, no_open_contradiction=True, counterfactual_checked=True,
    )
    values.update(overrides)
    return CompletenessCertificate(**values)


class AcceptVerifier:
    def verify_claim(self, c, graph_state):
        return c.value != "false-proof"


class FixedOrgan:
    def __init__(self, name, claims, evidence_rows):
        self.name, self._claims, self._evidence, self.calls = name, list(claims), list(evidence_rows), 0
    def reason(self, graph_state, context):
        self.calls += 1
        return list(self._claims), list(self._evidence), ReasoningTraceSummary(
            trajectory=self.name,
            proposed_claim_ids=tuple(c.claim_id for c in self._claims),
            confidence=0.5,
        )


class AdaptiveOrgan:
    name = "adaptive"
    def __init__(self): self.calls = 0
    def reason(self, graph_state, context):
        self.calls += 1
        if "_cyber" not in graph_state:
            return (
                [claim("H_A", confidence=0.55), claim("H_B", confidence=0.54)],
                [evidence("e-a", "H_A", "L1", 0.55), evidence("e-b", "H_B", "L2", 0.54)],
                ReasoningTraceSummary("adaptive", ("H_A", "H_B"), confidence=0.55),
            )
        return (
            [claim("H_A", confidence=0.90)],
            [evidence("e-a2", "H_A", "L3", 0.95)],
            ReasoningTraceSummary("adaptive", ("H_A",), confidence=0.90),
        )


class CyberLogicContracts(unittest.TestCase):
    def test_safe_ast(self):
        ev = SafeArithmeticEvaluator()
        self.assertEqual(ev.evaluate("2 + 3 * 4"), 14.0)
        with self.assertRaises(ValueError): ev.evaluate("__import__('os').system('echo no')")
        with self.assertRaises(ValueError): ev.evaluate("2 ** 99")

    def test_stepwise_rejects_bad_transition(self):
        ok, last, index = StepwiseProgramVerifier().verify([
            ProgramStep("10 + 5", 15), ProgramStep("15 * 2", 31), ProgramStep("30 - 4", 26)
        ])
        self.assertFalse(ok); self.assertEqual(last, 30.0); self.assertEqual(index, 1)

    def test_lineage_clone_discount(self):
        s = EvidenceCreditScorer()
        clones = s.score([evidence("c1", "H", "same"), evidence("c2", "H", "same")])
        independent = s.score([evidence("i1", "H", "L1"), evidence("i2", "H", "L2")])
        self.assertLess(sum(x.credit for x in clones), sum(x.credit for x in independent))

    def test_verified_native_stops(self):
        sovereign = claim("VERIFIED", provenance=Provenance.VERIFIED_NATIVE, epistemic=EpistemicState.KNOWN, confidence=1.0)
        organ = FixedOrgan("proof", [sovereign], [evidence("ev", "VERIFIED", "native", 1.0)])
        result = DefaultCyberneticSociety(max_rounds=4).run({}, CTX, [organ], AcceptVerifier())
        self.assertEqual(result.stopped_by, "verified_native_authority"); self.assertEqual(organ.calls, 1)

    def test_false_derived_removed(self):
        bad = Claim("BAD", "task", "answer", "false-proof", EpistemicState.DERIVED, Provenance.DERIVED, 0.999)
        result = DefaultCyberneticSociety(max_rounds=1).run(
            {}, CTX, [FixedOrgan("bad", [bad], [evidence("bad-e", "BAD", "Lx", 0.999)])], AcceptVerifier()
        )
        self.assertEqual(result.claims, []); self.assertEqual(result.evidence, [])

    def test_ambiguity_triggers_next_round(self):
        organ = AdaptiveOrgan()
        result = DefaultCyberneticSociety(max_rounds=3, stop_margin=0.10).run({}, CTX, [organ], AcceptVerifier())
        self.assertGreaterEqual(len(result.rounds), 2); self.assertIsNotNone(result.rounds[0].proposal)

    def test_complete_certificate(self):
        self.assertTrue(complete_certificate().verified_eligible)

    def test_unconsumed_operator_blocks_verified(self):
        sovereign = claim("4", provenance=Provenance.VERIFIED_NATIVE, epistemic=EpistemicState.KNOWN, confidence=1.0)
        state = {"_completeness": complete_certificate(operators_consumed_fraction=0.5)}
        result = DefaultCyberneticSociety(max_rounds=2).run(
            state, CTX, [FixedOrgan("proof", [sovereign], [evidence("e", "4", "native", 1.0)])], AcceptVerifier()
        )
        self.assertEqual(result.stopped_by, "incomplete_at_budget_limit")
        self.assertIn("operators_consumed_fraction", result.rounds[0].completeness_missing)

    def test_counterfactual_and_applicability_are_required(self):
        cert = complete_certificate(counterfactual_checked=False, domain_recognized=False, full_utterance_parsed=False)
        self.assertFalse(cert.verified_eligible)
        self.assertIn("counterfactual_checked", cert.missing())
        self.assertIn("domain_recognized", cert.missing())
        self.assertIn("full_utterance_parsed", cert.missing())


if __name__ == "__main__": unittest.main()

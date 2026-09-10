from __future__ import annotations

import unittest

from .contracts import (
    Claim,
    ContextFrame,
    EpistemicState,
    Evidence,
    Provenance,
    ReasoningTraceSummary,
)
from .cyberlogic import (
    CompletenessCertificate,
    DefaultCyberneticSociety,
    EvidenceCreditScorer,
    ProgramStep,
    SafeArithmeticEvaluator,
    StepwiseProgramVerifier,
)


CTX = ContextFrame(session_id="cyber-test")


def claim(
    cid: str,
    *,
    epistemic: EpistemicState = EpistemicState.HYPOTHESIS,
    provenance: Provenance = Provenance.TRUSTED_KNOWLEDGE,
    confidence: float = 0.8,
) -> Claim:
    return Claim(
        claim_id=cid,
        subject="task",
        predicate="answer",
        value=cid,
        epistemic=epistemic,
        provenance=provenance,
        confidence=confidence,
    )


def evidence(eid: str, cid: str, lineage: str, confidence: float = 0.8) -> Evidence:
    return Evidence(
        evidence_id=eid,
        claim_id=cid,
        source_id=eid,
        lineage_id=lineage,
        provenance=Provenance.TRUSTED_KNOWLEDGE,
        confidence=confidence,
        verified=False,
    )


def complete_certificate(**overrides) -> CompletenessCertificate:
    values = dict(
        parse_complete=True,
        operators_consumed_fraction=1.0,
        state_consistent=True,
        unique_answer=True,
        world_type_known=True,
        attributes_consumed_fraction=1.0,
        objective_consumed_fraction=1.0,
        algorithm_matches_type=True,
        capabilities_available=True,
        plan_fully_executed=True,
        capability_proof_complete=True,
        semantic_obligation_coverage=1.0,
        domain_recognized=True,
        full_utterance_parsed=True,
        intent_parsed=True,
        no_unconsumed_semantic_content=True,
        world_model_complete=True,
        prediction_checked=True,
        no_open_contradiction=True,
        counterfactual_checked=True,
    )
    values.update(overrides)
    return CompletenessCertificate(**values)


class AcceptVerifier:
    def verify_claim(self, c, graph_state):
        return c.value != "false-proof"


class FixedOrgan:
    def __init__(self, name, claims, evidence_rows):
        self.name = name
        self._claims = list(claims)
        self._evidence = list(evidence_rows)
        self.calls = 0

    def reason(self, graph_state, context):
        self.calls += 1
        return (
            list(self._claims),
            list(self._evidence),
            ReasoningTraceSummary(
                trajectory=self.name,
                proposed_claim_ids=tuple(c.claim_id for c in self._claims),
                confidence=0.5,
            ),
        )


class AdaptiveOrgan:
    name = "adaptive"

    def __init__(self):
        self.calls = 0

    def reason(self, graph_state, context):
        self.calls += 1
        if "_cyber" not in graph_state:
            c1 = claim("H_A", confidence=0.55)
            c2 = claim("H_B", confidence=0.54)
            return (
                [c1, c2],
                [evidence("e-a", "H_A", "L1", 0.55), evidence("e-b", "H_B", "L2", 0.54)],
                ReasoningTraceSummary(
                    trajectory=self.name,
                    proposed_claim_ids=("H_A", "H_B"),
                    confidence=0.55,
                ),
            )
        c1 = claim("H_A", confidence=0.90)
        return (
            [c1],
            [evidence("e-a2", "H_A", "L3", 0.95)],
            ReasoningTraceSummary(
                trajectory=self.name,
                proposed_claim_ids=("H_A",),
                confidence=0.90,
            ),
        )


class OverclaimingAbducer:
    def expand(self, claims, evidence_rows, graph_state, context):
        return [
            claim(
                "ABDUCED",
                epistemic=EpistemicState.KNOWN,
                provenance=Provenance.VERIFIED_NATIVE,
                confidence=1.0,
            )
        ]


class CyberLogicContracts(unittest.TestCase):
    def test_safe_ast_allows_only_bounded_arithmetic(self):
        ev = SafeArithmeticEvaluator()
        self.assertEqual(ev.evaluate("2 + 3 * 4"), 14.0)
        with self.assertRaises(ValueError):
            ev.evaluate("__import__('os').system('echo no')")
        with self.assertRaises(ValueError):
            ev.evaluate("2 ** 99")

    def test_stepwise_verifier_rejects_first_bad_transition(self):
        verifier = StepwiseProgramVerifier()
        ok, last, index = verifier.verify(
            [
                ProgramStep("10 + 5", 15),
                ProgramStep("15 * 2", 31),
                ProgramStep("30 - 4", 26),
            ]
        )
        self.assertFalse(ok)
        self.assertEqual(last, 30.0)
        self.assertEqual(index, 1)

    def test_lineage_clones_receive_less_total_credit_than_independent_sources(self):
        scorer = EvidenceCreditScorer()
        clones = scorer.score(
            [evidence("c1", "H", "same"), evidence("c2", "H", "same")]
        )
        independent = scorer.score(
            [evidence("i1", "H", "L1"), evidence("i2", "H", "L2")]
        )
        self.assertLess(sum(x.credit for x in clones), sum(x.credit for x in independent))

    def test_verified_native_authority_stops_cyber_loop(self):
        sovereign = claim(
            "VERIFIED",
            provenance=Provenance.VERIFIED_NATIVE,
            epistemic=EpistemicState.KNOWN,
            confidence=1.0,
        )
        organ = FixedOrgan("proof", [sovereign], [evidence("ev", "VERIFIED", "native", 1.0)])
        result = DefaultCyberneticSociety(max_rounds=4).run({}, CTX, [organ], AcceptVerifier())
        self.assertEqual(len(result.rounds), 1)
        self.assertEqual(result.stopped_by, "verified_native_authority")
        self.assertEqual(organ.calls, 1)

    def test_false_derived_claim_is_removed_before_it_can_accumulate_evidence(self):
        bad = Claim(
            claim_id="BAD",
            subject="task",
            predicate="answer",
            value="false-proof",
            epistemic=EpistemicState.DERIVED,
            provenance=Provenance.DERIVED,
            confidence=0.999,
        )
        organ = FixedOrgan("bad-proof", [bad], [evidence("bad-e", "BAD", "Lx", 0.999)])
        result = DefaultCyberneticSociety(max_rounds=1).run({}, CTX, [organ], AcceptVerifier())
        self.assertEqual(result.claims, [])
        self.assertEqual(result.evidence, [])

    def test_ambiguous_competing_hypotheses_trigger_discriminating_round(self):
        organ = AdaptiveOrgan()
        result = DefaultCyberneticSociety(max_rounds=3, stop_margin=0.10).run(
            {}, CTX, [organ], AcceptVerifier()
        )
        self.assertGreaterEqual(len(result.rounds), 2)
        self.assertIsNotNone(result.rounds[0].proposal)
        self.assertIn("H_A", result.rounds[0].proposal.target_claim_ids)
        self.assertIn("H_B", result.rounds[0].proposal.target_claim_ids)
        self.assertGreaterEqual(organ.calls, 2)

    def test_complete_certificate_is_verified_eligible(self):
        cert = complete_certificate()
        self.assertTrue(cert.verified_eligible)
        self.assertEqual(cert.missing(), ())

    def test_correct_answer_cannot_stop_when_operator_is_unconsumed(self):
        sovereign = claim(
            "4",
            provenance=Provenance.VERIFIED_NATIVE,
            epistemic=EpistemicState.KNOWN,
            confidence=1.0,
        )
        organ = FixedOrgan("proof", [sovereign], [evidence("e", "4", "native", 1.0)])
        state = {"_completeness": complete_certificate(operators_consumed_fraction=0.5)}
        result = DefaultCyberneticSociety(max_rounds=2).run(state, CTX, [organ], AcceptVerifier())
        self.assertEqual(result.stopped_by, "incomplete_at_budget_limit")
        self.assertIn("operators_consumed_fraction", result.rounds[0].completeness_missing)
        self.assertIsNotNone(result.rounds[0].proposal)

    def test_counterfactual_check_is_required_when_certificate_is_present(self):
        strong = claim("H", confidence=0.99)
        organ = FixedOrgan(
            "reflective",
            [strong],
            [evidence("e1", "H", "L1", 0.99), evidence("e2", "H", "L2", 0.99)],
        )
        state = {"_completeness": complete_certificate(counterfactual_checked=False)}
        result = DefaultCyberneticSociety(max_rounds=2, stop_margin=0.01).run(
            state, CTX, [organ], AcceptVerifier()
        )
        self.assertEqual(result.stopped_by, "incomplete_at_budget_limit")
        self.assertIn("counterfactual_checked", result.rounds[0].completeness_missing)

    def test_semantic_applicability_gate_blocks_narrow_solver_overreach(self):
        cert = complete_certificate(
            domain_recognized=False,
            full_utterance_parsed=False,
            no_unconsumed_semantic_content=False,
        )
        self.assertFalse(cert.verified_eligible)
        self.assertIn("domain_recognized", cert.missing())
        self.assertIn("full_utterance_parsed", cert.missing())
        self.assertIn("no_unconsumed_semantic_content", cert.missing())

    def test_abductive_expansion_is_forced_back_to_hypothesis(self):
        base = claim("BASE", confidence=0.6)
        organ = FixedOrgan("base", [base], [evidence("base-e", "BASE", "L1", 0.6)])
        result = DefaultCyberneticSociety(
            max_rounds=1,
            abductive_expander=OverclaimingAbducer(),
        ).run({}, CTX, [organ], AcceptVerifier())
        abducted = next(c for c in result.claims if c.claim_id == "ABDUCED")
        self.assertEqual(abducted.epistemic, EpistemicState.HYPOTHESIS)
        self.assertNotEqual(abducted.provenance, Provenance.VERIFIED_NATIVE)
        self.assertLessEqual(abducted.confidence, 0.95)


if __name__ == "__main__":
    unittest.main()

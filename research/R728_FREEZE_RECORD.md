# NEXUS R7.28 Freeze Record

Date: 2026-08-24

Release: **NEXUS R7.28 — Semantic Applicability Gate + Full-Utterance Binding**

Freeze ZIP SHA-256:

`c6b6358dd26ebd04faea42b57a213c736c02d0323bb6a574f1160a2a4db28387`

Verified invariant:

`VERIFIED => DomainRecognized AND FullUtteranceParsed AND QuestionIntentParsed AND OptionSemanticsBound AND NoUnconsumedSemanticContent AND ExecutionProofComplete AND ParentProofVerified`

Development evidence before freeze:
- Blind-22..40 disclosed regression: 2336/2824 correct, 2336 resolved, conditional 100%, false VERIFIED 0; exact parent preservation vs R7.27.
- Blind-41 disclosed development: 160/200 strict, 160/160 VERIFIED correct, false VERIFIED 0. R7.27 had five false VERIFIED on unknown logarithm operator spans.
- External-LogiQA-50 disclosed development: 0/50 strict, 0 resolved, false VERIFIED 0. R7.27 had five false VERIFIED caused by accidental narrow-solver activation.
- R7.28 tests: 5 self + 1300 property + 320 adversarial = 1625 PASS.
- 23/23 R7.27 parent source files byte-identical.

Chronology commitments:
- **Blind-42 DOES NOT EXIST at this freeze.**
- External LogiQA holdout records/lines **51–100 have not been retrieved or used** at this freeze.
- Holdout selection rule is fixed now: records 51–100 in repository order from `lei-nlp-lab/logical_subspace_acl_2026/generalization/data/logiqa_500_sample.jsonl`.
- Source Git blob SHA: `d8080e9137cdd25eb36511e53db85fcc863b9c92`.

R7.28 is immutable after this record. Future Blind-42 and external LogiQA-51..100 results are post-freeze evidence only.
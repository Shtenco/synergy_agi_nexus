# Blind-42 Pre-Inference Commitment

Date: 2026-08-24

R7.28 frozen ZIP SHA-256:
`c6b6358dd26ebd04faea42b57a213c736c02d0323bb6a574f1160a2a4db28387`

Blind-42 no-gold benchmark SHA-256:
`8697ebb56a10f8e68cbb9f45a84071827bfbea22e2f1fa75849acf7c6a868c44`

Evaluator key SHA-256:
`c5f67df99e12a84abb7eb2d7cde82663b91da4687b4b80e879cfccce817e78b7`

Design:
- N=200
- 8 categories × 25
- 160 standard composable tasks
- 40 near-OOD semantic-applicability traps
- near-OOD includes unknown operator spans and long general-MRC surfaces containing familiar narrow-solver triggers.

At this commit:
`inference_has_run = false`

R7.28 source is immutable after its freeze. Blind-42 evaluation may not modify R7.28 or the benchmark.
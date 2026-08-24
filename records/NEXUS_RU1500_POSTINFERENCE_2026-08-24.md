# NEXUS-RU-1500 POST-INFERENCE RECORD

Date: 2026-08-24

Pre-inference commit: `8902bff9d6bd86bac82d8f08b6a1ed7b61d65b5b`

Visible benchmark SHA-256:
`afb073f1e032959207c699cdfdf7f7c91549108fd81c56ed1dea69c47b1d426d`

Evaluator key SHA-256:
`a0991e96ae1a5e391d32055745bb7e630e884240a09e9f88aad2b43aa48d9b94`

## Common frozen results

- R7.8: 0/1500, resolved 0, false VERIFIED 0.
- R7.9 native-only reconstructed: 0/1500, resolved 0, false VERIFIED 0.
- R7.10 through R7.28: 50/1500 = 3.33% strict; resolved 100/1500; conditional 50%; false VERIFIED 50.
- R7.15-R7.17 are reported as source-proven zero-teacher output-equivalent, not as physical full instrumentation runs.

R7.28 group breakdown:
- language: 0/600, resolved 0.
- adequacy-response selection: 50/400, resolved 50, conditional 100%, false VERIFIED 0.
- reasoning in Russian: 0/450, resolved 50, false VERIFIED 50.
- applicability traps: 0/50, resolved 0.

Only two categories resolve:
- instruction-following numeric-only: 50/50 correct.
- Russian FIFO state updates: 0/50 correct, 50 false VERIFIED.

Interpretation: internal reasoning improved across later R versions, but general Russian semantic grounding did not. The formal core recognizes some state-machine structure without correctly binding Russian action verbs; R7.28 still accepts the inherited formal proof.

Scientific boundary: this benchmark measures Russian understanding and selection among candidate Russian answers. It is not a free-form generation benchmark; the common frozen NEXUS interface does not expose a generic Russian chat-response API.
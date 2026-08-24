# Blind-42 Post-Inference Result

Date: 2026-08-24

Chronology:
1. R7.28 freeze record commit: `99b58ae1b00dd915467f34e89580fae63482731a`
2. Blind-42 pre-inference commitment: `1d3625b1bbbbfe54431a4c3c36277639730a8a35`
3. This post-inference record was created only after frozen R7.27 and frozen R7.28 were evaluated.

R7.28 freeze ZIP SHA-256:
`c6b6358dd26ebd04faea42b57a213c736c02d0323bb6a574f1160a2a4db28387`

Blind-42 no-gold benchmark SHA-256:
`8697ebb56a10f8e68cbb9f45a84071827bfbea22e2f1fa75849acf7c6a868c44`

## Frozen R7.27
- strict correct: **160/200 = 80.0%**
- resolved: **195/200 = 97.5%**
- conditional accuracy: **160/195 = 82.0513%**
- false VERIFIED: **35**
- standard subset: **160/160 correct**, false VERIFIED 0
- near-OOD applicability traps: 0/40 correct, 35/40 resolved, **35 false VERIFIED**

## Frozen R7.28
- strict correct: **160/200 = 80.0%**
- resolved: **160/200 = 80.0%**
- conditional accuracy: **160/160 = 100%**
- false VERIFIED: **0**
- standard subset: **160/160 correct**, false VERIFIED 0
- near-OOD applicability traps: 0/40 resolved; **40 safe UNKNOWN**, false VERIFIED 0

## Paired interpretation
Strict correctness is unchanged because abstentions count wrong in total accuracy: both versions retain the same 160 correct standard answers.

Safety transition on the 35 items where R7.27 was incorrectly VERIFIED:
- unsafe incorrect VERIFIED -> safe UNKNOWN: **35**
- safe -> unsafe: **0**
- exact two-sided sign-test over these 35 directional safety transitions: **p = 5.820766091346741e-11**

Thus Blind-42 validates a **soundness/applicability improvement**, not a raw strict-accuracy improvement.

No R7.28 source or Blind-42 benchmark content was changed after freeze/pre-inference commitment.
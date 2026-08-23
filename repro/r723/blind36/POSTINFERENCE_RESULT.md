# Blind-36 post-inference result

R7.23 freeze ZIP SHA-256: `e626d4cd86aa2534815e38f921315d678bee3034e5b446955ec920b678175473`

Blind-36 benchmark SHA-256: `ad95b097c992970ea69e2b8447f9b0e9c30efcc2200c45b82bd4baac178413b4`

Zero-teacher comparison on the same frozen benchmark:
- R7.22: 70/200 correct, 78 resolved, 8 false VERIFIED.
- R7.23: 170/200 correct = 85.0%, 170 resolved, 0 false VERIFIED.
- R7.23 conditional accuracy: 170/170 = 100%.
- paired R7.23 vs R7.22: 100 corrections / 0 regressions.
- exact two-sided sign p ≈ 1.5777218104420236e-30.

Preregistered near-OOD result:
- widest-path capacity: 0/5, safe abstain 5/5.
- max-flow capacity: 0/5, safe abstain 5/5.
- cube operator: 0/5, safe abstain 5/5.
- deque model revision: 0/5, safe abstain 5/5.
- masked conditional table: 0/5, safe abstain 5/5.
- shared-firmware latent dependency: 0/5, safe abstain 5/5.

Thus R7.23 solved all 170 non-near-OOD tasks and abstained on all 30 preregistered near-OOD tasks, with zero confident errors. No post-freeze modification of R7.23 was made.
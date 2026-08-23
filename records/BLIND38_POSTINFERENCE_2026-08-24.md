# Blind-38 post-inference result

Frozen benchmark SHA-256: `6f5977a0e7e19a7b7083c0a23477a594fbdf1e1c05a175ba16a411fff1f16a17`

Frozen R7.25 ZIP SHA-256: `69640417ad1418f4339c45aaf3b20c74ddc131e5c33525cf00fd4b49d7a7de4e`

Zero-teacher results on the same fresh post-freeze Blind-38:
- R7.24: 0/200 correct, 0 resolved, 0 false VERIFIED.
- R7.25: **165/200 = 82.5% correct**, 170/200 resolved, **165/170 = 97.0588% conditional accuracy**, **5 false VERIFIED**.
- Composable subset: **160/160 = 100%**.
- Near-OOD subset: 5/40 correct, 10/40 resolved, 5 false VERIFIED.
- Pairwise R7.25 vs R7.24: **165 corrections / 0 regressions**, exact two-sided sign p ≈ `4.2764e-50`.

Reflection audit on the frozen R7.25 run:
- 170 items reached R7.25 reasoning VERIFIED.
- 65 items contained explicit revision.
- 160 items contained counterfactual checking.
- 25 items contained an explicit prediction-error phase.

All 5 false VERIFIED are from one near-OOD family: `opposing_paths_near_ood`.
Root cause: one causal clause used an adverbial surface (`X also decreases N`) that the frozen relation parser did not consume. The reasoner therefore reflected over an incomplete world model and certified the remaining single-sign path.

This result is preserved as-is. **R7.25 is not patched against Blind-38.** The next version must address semantic relation coverage / observation completeness before reflection.

# Blind-37 post-inference result

Chronology was frozen before evaluation:
- R7.24 freeze ZIP SHA-256: `7bcc991d298a1a8f11fc7a64449fb311a0609f85bb2e32bba670ce0dcdfb178e`
- Blind-37 no-gold benchmark SHA-256: `971a3b853f504a9435a4513f4f93d12eb5659678bb245033c9fd63eed64ac00f`
- pre-inference commitment commit: `fa52c14c850c0fb341fcaf6dd7762a4dfead7dee`

Fresh post-freeze zero-teacher result on 200 tasks:

| Frozen core | Correct | Resolved | Conditional accuracy | False VERIFIED |
|---|---:|---:|---:|---:|
| R7.23 | 4/200 = 2.0% | 4 | 100% | 0 |
| **R7.24** | **160/200 = 80.0%** | **160** | **160/160 = 100%** | **0** |

Pairwise R7.24 vs R7.23: **156 corrections / 0 regressions**, exact two-sided sign p ≈ `2.19e-47`.

Blind-37 was designed as 160 composable tasks plus 40 near-OOD tasks. R7.24 solved **160/160 composable tasks** and produced **40/40 safe abstentions** on near-OOD, with zero false VERIFIED.

Fresh categories also included pre-freeze capabilities not present in Blind-36, notably minimax path composition and Jaccard set composition. This therefore tests more than replay of the six Blind-36 near-OOD families.

Scientific boundary: Blind-37 is an internal synthetic post-freeze mechanism benchmark, not an external standardized AGI benchmark. R7.24 remains frozen and must not be patched against Blind-37; Blind-37 becomes disclosed development only for later generations.

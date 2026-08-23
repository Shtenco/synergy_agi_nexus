# Blind-33 sealed protocol

This branch contains only the frozen benchmark payload and teacher-side inference runner. It contains no evaluator key, gold labels, R7.20 post-freeze modifications, or post-inference analysis.

Primary benchmark SHA-256: `a56318266aa92f4ab1ea18972c791a3ede7408f90f4ca7146b9a3f7955c858cc`.

Five frozen teacher identities: `ministral-3:3b`, `phi4-mini:3.8b`, `granite3.3:2b`, `qwen3:1.7b`, `gemma3:1b`.

Teacher protocol: temperature 0; seed 33072026; top_p 1.0; num_predict 8; output restricted to A/B/C/D. Raw evidence is uploaded independently for each teacher. Accuracy is computed only after all inference artifacts are complete using the separately held evaluator key.

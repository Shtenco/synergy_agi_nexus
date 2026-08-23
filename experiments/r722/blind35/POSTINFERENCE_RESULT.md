# Blind-35 post-inference result

Chronology is preserved: this result is committed after the R7.22 freeze record and the Blind-35 pre-inference commitment.

## Frozen identities

- R7.22 freeze ZIP SHA-256: `1268a6a1bb57501b49617e9e30ef12759a623241bdb8e2636db52db81fcd6950`
- Blind-35 benchmark SHA-256: `96014a86bd1b4f647348c7b3900659e1184974087eab15fc61304c87f0d3315f`

## Zero-teacher result

- R7.21: 82/200 = 41.0%; resolved 82; false VERIFIED 0.
- R7.22: 175/200 = 87.5%; resolved 180; conditional accuracy 175/180 = 97.22%; false VERIFIED 5.
- Paired R7.22 vs R7.21: 93 corrections / 0 regressions; exact two-sided sign p = 2.0194839173657902e-28.

## Distribution boundary

Blind-35 contains 175 standard fresh-transfer tasks and 25 explicit near-OOD tasks (5 families × 5).

- Standard fresh-transfer: R7.22 = 175/175 correct.
- Near-OOD: R7.22 = 0/25 correct.
  - 20/25 safe abstentions.
  - 5/25 unsafe false VERIFIED.

The five false VERIFIED cases are all `weighted_shortest_path_near_ood`: the frozen unweighted BFS route consumes topology but not edge-weight attributes and therefore applies the wrong graph algorithm while still declaring completion.

R7.22 is not modified after this result. The next-version invariant should require graph-type and edge-attribute completeness before VERIFIED, e.g. `AlgorithmMatchesGraphType AND EdgeAttributesConsumed=100%`.

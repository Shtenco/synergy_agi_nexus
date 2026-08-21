# NEXUS migration policy v1

`agi_nexus` is the canonical target, not a bulk copy of `agi_olga`.

## Promotion path

```text
historical branch/artifact
→ source identity
→ benchmark definition identity
→ raw result artifact
→ reproducibility check
→ negative controls / ablation
→ claim tier assignment
→ migration candidate
→ canonical NEXUS generation
```

## Rules

1. `agi_olga` remains preserved as historical and research lineage.
2. No branch is migrated merely because its version number is newer or its parameter count is larger.
3. Synthetic, generated or internal held-out suites remain explicitly labelled; they do not become official ARC scores.
4. Official-private benchmark claims require an external official evaluation artifact.
5. A migration candidate must identify code, weights/config, benchmark inputs and raw outputs by immutable digest before promotion.
6. Negative A/B results are first-class evidence and must not be deleted from the lineage.
7. Cybernetic, logical, graph/small-world and world-model components may be migrated independently if their evidence is stronger than the full model generation.
8. `agi_nexus` owns model identity and benchmark evidence, but has no financial, payment or system-governance authority.

## Initial source map

Current preserved source line includes SmallWorld V11.3, NEXUS-600K, V12–V18, V20/V21 and discovered R2/R2.1/R23/R74 branches. Exact status is machine-readable in `config/nexus_generation_inventory_v1.json`.

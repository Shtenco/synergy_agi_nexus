# Small-World Kernel Migration v1

This is the first code component proposed for migration from the preserved `Shtenco/agi_olga` lineage into canonical `Shtenco/agi_nexus`.

## Frozen source

- repository: `Shtenco/agi_olga`
- generation: `nexus-v20-smallworld-1m`
- commit: `85291b0798be2ef03eb6fea8225794756c1896a7`
- path: `nexus_v20/smallworld.py`
- Git blob: `fc4d145d4ab4c76d21b579e220fd787e35b4e281`

The legacy repository and source file remain unchanged.

## Migration rule

The canonical implementation must preserve deterministic topology and Metropolis semantics for accepted legacy inputs while being allowed to reject unsafe/unbounded inputs that the research source did not constrain.

V1 therefore adds:

- `MAX_NODES_V1=4096` memory/CPU bound;
- strict integer validation (`bool` is not accepted as integer input);
- bounded seed size;
- finite/non-negative/symmetric adjacency validation;
- required self loops;
- finite/non-negative row-stochastic Metropolis validation;
- exact float32 parity vectors from the frozen V20 source.

## What this does not mean

Migration parity does **not** prove that V20 is the best NEXUS generation, does not validate all V20 benchmark claims, and does not promote the full V20 model/runtime. It proves only that one isolated deterministic kernel has preserved provenance and reproducible semantics.

`production_promotion_authority = NONE`.

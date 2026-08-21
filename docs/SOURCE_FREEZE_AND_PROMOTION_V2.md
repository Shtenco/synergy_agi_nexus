# NEXUS Source Freeze & Promotion v2

This layer sits above `nexus.generation-inventory/v1` and does **not** replace it.

## Three different facts

1. **Inventory** — which historical/research generations are known.
2. **Source freeze** — which immutable commit bytes are under review.
3. **Promotion decision** — whether one component has enough evidence to enter migration review.

A branch name is never an identity. Promotion uses exact Git commit SHA plus an artifact SHA-256.

## Evidence policy

Default migration review requires at least `REPRODUCED_INTERNAL` benchmark evidence plus:

- frozen source commit;
- frozen component artifact SHA-256;
- benchmark result digest;
- negative-control/ablation digest;
- reproducibility evidence digest.

`SYNTHETIC`, `BRANCH_DISCOVERED`, README claims and larger model/version numbers are insufficient by themselves.

## Authority boundary

A successful evaluator result is only:

`MIGRATION_REVIEWABLE`

It is **not**:

- a claim that this is the best NEXUS generation;
- a production release;
- an automatic merge authorization;
- an official ARC score;
- permission to delete or rewrite `agi_olga` history.

`automatic_merge_authority = NONE` is invariant in v2.

## Current frozen refs

The v2 overlay freezes, among others:

- `agi_olga@d88d753995b839fa03cbe9e78b61d103e282fc41` for the preserved main lineage;
- V20 SmallWorld 1M at `85291b0798be2ef03eb6fea8225794756c1896a7`;
- V21 Collective at `1f8cd8ad323333d4368736f0e3fe22b9d5cad3e9`;
- R23 at `3c5d5d9b4dadd3ce44195f0cbda5fcdaf94e9fef`;
- R7.4 teacher lab at `08bbead85db62c8409e16d48dfc731b1efa99de9`.

Future source refreshes must create a new source-freeze generation rather than silently changing these identities.

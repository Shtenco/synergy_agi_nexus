# Deterministic NEXUS source capsule v1

This generation turns the first migrated NEXUS kernel into a reproducible **source artifact**, not an executable service package.

## Scope

Recipe: `nexus.source-capsule-recipe/v1`

Included bytes are exactly the sorted source paths declared in `config/nexus_source_capsule_recipe_v1.json` plus a generated `CAPSULE_MANIFEST.json`.

The archive profile is deliberately simple and deterministic:

- ZIP container;
- `ZIP_STORED` only;
- fixed entry timestamp `1980-01-01 00:00:00`;
- sorted unique POSIX paths;
- fixed regular-file mode `0644`;
- no symlink inputs;
- no absolute paths or `..` traversal;
- canonical JSON manifest;
- SHA-256 and byte length for every included source file.

## Identity and evidence

Recipe digest:

`a75b05124ed358960a5313b34be38434564f5bcd40db102104516a58a89ccbd9`

The recipe intentionally states:

- `artifact_kind = NON_EXECUTABLE_DETERMINISTIC_SOURCE_CAPSULE`;
- `dependency_lock_status = RANGE_NOT_RUNTIME_LOCKED`;
- `build_evidence_status = NOT_EXECUTED`;
- `execution_authority = NONE`.

The current NumPy dependency remains a range (`numpy>=1.26,<3`), so this source capsule must not be treated as a reproducible runtime environment or executable Meta-OS service artifact.

## Reproducibility contract

For the same repository bytes and recipe, two executions of `tools/build_source_capsule_v1.py` must produce byte-identical ZIP output. The generated manifest independently hashes every source file.

The CLI prints an output SHA-256 only after a build actually executes. That output digest is intentionally not pre-written into the source recipe, avoiding an evidence claim before execution.

## Next generation

A later producer-side build receipt may bind:

`source commit + recipe digest + source capsule digest + runtime dependency lock + executable artifact digest`.

Only such a later artifact can be considered for Meta-OS deployability. This v1 capsule itself is archival/reproducibility evidence only.

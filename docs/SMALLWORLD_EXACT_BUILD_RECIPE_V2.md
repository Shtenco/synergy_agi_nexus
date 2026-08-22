# Deterministic SmallWorld exact service build recipe v2

This generation packages the stdlib-only `nexus.compute-service/v2` introduced by the exact rational SmallWorld protocol. It is additive and does not modify the NumPy/float32 v1 service or v1 build recipe.

## Source identity

- source repository: `Shtenco/agi_nexus`
- source commit: `2ee8f2a29ad2497afca6c7386375a296cd0bdbcf`
- recipe digest: `3e255804dbd420492fc5481fe11d6333be2a50c8834bd4a8e3896de726f44089`
- dependency contract: `PYTHON_STDLIB_ONLY`
- dependency lock status: `STDLIB_ONLY_NO_THIRD_PARTY_RUNTIME_DEPENDENCIES`

Each included source file is frozen by Git blob SHA. The recipe separates `source_path` from `archive_path`, so repository `src/agi_nexus/...` files are packaged as a directly runnable `agi_nexus/...` module tree.

## Deterministic archive profile

- ZIP_STORED
- entries ordered by archive path
- fixed timestamp `1980-01-01T00:00:00Z`
- mode `0644`
- no extra ZIP fields/comments
- exact content SHA-256 and Git blob evidence per file

The intended extracted entrypoint is:

```text
python -m agi_nexus.compute_service_v2
```

with the extracted artifact root as `PYTHONPATH=.` / working directory.

## Evidence boundary

The source-repository builder may emit `nexus.service-build-artifact/v2` containing the actual artifact SHA-256 and file evidence. It deliberately emits:

```text
test_evidence_status = NOT_ATTESTED
build_status = ARTIFACT_BUILT_TEST_EVIDENCE_PENDING
execution_authority = NONE
```

The builder cannot promote its own artifact to `BUILD_VERIFIED`. Test execution/attestation is a separate evidence boundary. A fresh outer hash cannot legalize a fabricated `PASSED` or `BUILD_VERIFIED` state.

## Why this matters

V1 remained blocked by a range-only NumPy dependency and by implementation-dependent float32 reduction semantics. V2 uses exact rational Metropolis semantics and standard-library-only runtime code. This removes the third-party runtime dependency blocker, but **does not** by itself prove that CI executed or that Meta-OS may deploy the service.

The next cross-root step is to register this recipe as the NEXUS recipe for `SCIENCE_RESEARCH_NODE`, while preserving the old recipe registry generation. Actual node admission remains blocked until source-owned artifact + test attestations exist and are independently consumed by Meta-OS.

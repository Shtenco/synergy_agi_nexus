# SmallWorld service build recipe v1

This generation adds a deterministic build recipe for the bounded NEXUS SmallWorld service candidate from commit `ef1a6e3675e53fda4bf91566aec61f1b62fa9336`.

The recipe packages only an explicit allowlist of service/runtime/schema files. Every file is verified from its raw bytes against the frozen Git blob identity before packaging. ZIP entries use lexicographic order, `ZIP_STORED`, fixed `1980-01-01T00:00:00Z` timestamps, fixed `0644` file mode and no extra fields.

The resulting archive is an `EXECUTABLE_SOURCE_PACKAGE_CANDIDATE`, not a production binary and not a production deployment approval. Its dependency contract is still `numpy>=1.26,<3`; the exact runtime dependency set has not yet been frozen. Therefore a successfully built archive remains blocked from `BUILD_VERIFIED` until an exact dependency lock and independent test/build attestation exist.

The build recipe grants `execution_authority=NONE`. A source package digest is never a Meta-OS admission decision and never a model-authority claim.

When GitHub Actions runners execute normally, the isolated workflow builds the artifact twice and compares the bytes before uploading the ZIP and generated evidence manifest. Until that run actually executes, no artifact SHA is pre-claimed in federation build locks.

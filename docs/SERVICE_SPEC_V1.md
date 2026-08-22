# NEXUS service specification v1

This contract records a deliberate readiness gap rather than hiding it.

The first migrated canonical component is a deterministic Small-World **library kernel**. The current `agi_nexus` package does not yet expose a node-service entrypoint, health probe, lifecycle protocol or NEXUS wire protocol. Therefore it is not a deployable Meta-OS NEXUS service regardless of source/build integrity.

V1 requires:

- `runtime_form = PYTHON_LIBRARY_ONLY`
- `entrypoint = null`
- `health_probe = null`
- `lifecycle_protocol = null`
- `wire_protocol = null`
- `readiness_status = SERVICE_INTERFACE_NOT_IMPLEMENTED`
- `execution_authority = NONE`

A future additive service generation must define and test a bounded NEXUS service interface around canonical kernels. It must not mutate this library-only provenance generation.

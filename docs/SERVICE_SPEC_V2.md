# NEXUS ServiceSpec v2

This additive generation supersedes the *service-interface conclusion* of ServiceSpec v1 for a newer source commit without rewriting v1 history.

ServiceSpec v1 remains correct for the older SmallWorld-only candidate: that source was a library kernel and not a complete NEXUS service.

ServiceSpec v2 pins the exact runtime source parent commit:

`4915872c60117bbac0001a0f792f2a8f3a12899a`

and the frozen upstream R7.10 proof-first source commit:

`fc8a32bc949947a42ab5038de0a3e55fa9921e64`

The new source contains a bounded stdlib service with a real entrypoint, health operation, lifecycle contract and wire protocol. Therefore:

`interface_status = SERVICE_INTERFACE_IMPLEMENTED_SOURCE_ONLY`

is now evidence-backed.

This does **not** imply build reproducibility or process admission. The ServiceSpec requires:

- `build_artifact_digest = null`
- `build_evidence_digest = null`
- `execution_authority = NONE`

The neural Ω-R5 checkpoint is also not overclaimed. It is explicitly recorded as `NOT_MIGRATED_NOT_REQUIRED_FOR_EXACT_CORE`. The exact proof/cyber core can run and abstain correctly while neural checkpoint migration remains a separate later generation.

Canonical ServiceSpec v2 digest:

`c01a22e4dbd5a1e4e6f2b9a3fbc9e49f559a43f1575cd4e6a6f4c22420f3121b`

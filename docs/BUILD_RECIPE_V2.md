# NEXUS proof-core BuildRecipe v2

This additive recipe binds the real minimal NEXUS runtime generation and its ServiceSpec v2.

Source commit:

`0cf581fe6ac6e79bcf39c9ed4833e2d5719ddd6f`

ServiceSpec digest:

`c01a22e4dbd5a1e4e6f2b9a3fbc9e49f559a43f1575cd4e6a6f4c22420f3121b`

The executable core itself uses only Python standard-library runtime facilities, but the repository package build still declares the open build-system requirement `setuptools>=68`. Therefore this generation deliberately remains:

- `build_toolchain.status = NOT_FROZEN`
- `reproducibility_status = NOT_REPRODUCIBLE_TOOLCHAIN_NOT_FROZEN`
- `artifact_digest = null`
- `build_evidence_digest = null`
- `execution_authority = NONE`

A source-level runnable interface is not the same claim as reproducible artifact bytes. A later toolchain-lock/build-evidence generation must solve that independently.

Canonical recipe digest:

`46e874b075c52ee81e4996c6ce3fc027078f54ad4c4824a869d92b597821fe90`

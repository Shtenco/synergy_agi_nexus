# AGI NEXUS build recipe v1

This artifact freezes the *current packaging assumptions* for the first migrated NEXUS Small-World kernel. It does not claim a reproducible wheel build yet.

Source identity:

- repository: `Shtenco/agi_nexus`
- source commit: `cbc06e83f7f9e242719667e446a090894e11eef1`
- source role: `NEXUS_SMALLWORLD_KERNEL_CANDIDATE`
- package: `agi-nexus==0.1.0`
- artifact kind: `PYTHON_WHEEL`

Current unresolved reproducibility inputs:

- build-system requirement is still a range: `setuptools>=68`;
- runtime NumPy requirement is still a range: `numpy>=1.26,<3`;
- no content-addressed build-toolchain lock exists;
- no independently reproduced wheel digest exists.

Therefore v1 deliberately requires:

- `build_toolchain.status = NOT_FROZEN`
- `build_toolchain.lock_digest = null`
- `reproducibility_status = NOT_REPRODUCIBLE_TOOLCHAIN_NOT_FROZEN`
- `artifact_digest = null`
- `execution_authority = NONE`

A later recipe generation may freeze exact toolchain/dependency artifacts and enable reproducibility experiments. It must be additive; this source-candidate recipe remains provenance.

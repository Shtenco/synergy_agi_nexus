# NEXUS SmallWorld Build Readiness v1

This contract answers a deliberately narrow question: **what is proven about the current canonical SmallWorld migration as a build/deployment input?**

What is frozen:
- repository: `Shtenco/agi_nexus`
- source commit: `cbc06e83f7f9e242719667e446a090894e11eef1`
- exact Git blob identities for the runtime component and dependency-range file
- Python test targets: 3.11 and 3.12

What is *not* proven:
- an exact reproducible dependency lock (`numpy` is still expressed as a range)
- a NEXUS node-service entrypoint
- a reproducibly built deployable artifact
- process execution authority

Therefore the v1 status is intentionally:

`COMPONENT_ONLY_NOT_NODE_SERVICE`

and the canonical readiness digest is:

`0e29504a9448c970fd5057123300000aca8c3d88e84f524bed2041cb881aec9a`

The next generation must create a bounded NEXUS compute service protocol/entrypoint and a reproducible dependency lock before a deployable build can be claimed. The historical SmallWorld migration and this v1 contract remain immutable.

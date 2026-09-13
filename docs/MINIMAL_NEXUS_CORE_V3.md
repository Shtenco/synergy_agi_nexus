# Minimal NEXUS Core v3

This additive generation removes the architectural mistake `SmallWorld kernel == NEXUS service` without pretending that the frozen neural Ω-R5 checkpoint has already been migrated.

## Source lineage

The formal/cyber proof path is migrated from the frozen NEXUS R7.10 proof-first release in `Shtenco/ai_language`, source freeze commit:

`fc8a32bc949947a42ab5038de0a3e55fa9921e64`

The upstream freeze predates Blind-27 generation. Source hashes and Blind-27 hash are recorded in `config/r710_migration_provenance_v1.json`.

R7.10 architecture preserved here:

`natural question -> typed FormalIR -> Solver -> ProofObject -> independent Verifier -> option matcher`

A proof is authoritative only when the independent verifier recomputes the result and returns `VERIFIED`. Unsupported questions return `UNKNOWN` and the service clears the answer rather than guessing.

## Minimal service core

The runtime combines three independent components:

1. `R710_FORMAL_PROOF` — exact proof-first logic/cyber/policy/code/Russian/trusted-fact routes.
2. `EXACT_SMALLWORLD` — stdlib exact-rational SmallWorld semantic digests, preserving the canonical 8-node v2 vector.
3. `BOUNDED_CYBER_STATE` — eight typed nodes: `context/domain/cause/effect/goal/error/action/constraint`, maximum 64 transitions, hash-chained state ancestry.

The neural Ω-R5/Phase-4 checkpoint is deliberately **not** claimed as part of this executable source generation. It remains a future `NEURAL_HYPOTHESIS` organ after independent checkpoint migration/parity evidence. The exact core is useful and service-complete without inventing neural availability.

## Service boundary

Entrypoint:

`python -m agi_nexus.nexus_service_v3`

Allowlisted operations only:

- `STATUS`
- `FORMAL_REASON`
- `SMALLWORLD_EXACT_DIGESTS`
- `CYBER_STEP`

Wire limits:

- frame <= 64 KiB;
- question <= 16 KiB;
- each option <= 4 KiB;
- cyber state <= 64 transitions.

The request protocol contains no host, port, URL, filesystem path, dynamic module, shell or process command fields. The runtime exposes no network client and no payment/accounting/financial capability.

## Authority hierarchy

`FORMAL_VERIFIED > CYBER_FEEDBACK > NONE`

This is reasoning authority inside the service response only. It is **not** process execution, Meta-OS admission, financial authority or scientific-truth authority outside the proven formal claim.

Every response carries `execution_authority=NONE`.

## Build boundary

This PR proves a real source-level service interface. It does not claim reproducible wheel bytes:

- `build_artifact_digest = null`
- `build_evidence_digest = null`

The repository build backend still uses an open `setuptools>=68` requirement, so build/toolchain evidence remains a separate blocker.

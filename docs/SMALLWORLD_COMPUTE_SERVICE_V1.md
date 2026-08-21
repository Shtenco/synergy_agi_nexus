# SmallWorld Compute Service Protocol v1

This is the first bounded process/service protocol in canonical `agi_nexus`.

It is intentionally **not a full NEXUS model server**. The only allowlisted operation is:

`SMALLWORLD_DIGESTS`

The service accepts bounded canonical JSONL requests on stdin and emits canonical JSONL responses on stdout. It performs no dynamic import, shell execution, network access, file access or arbitrary Python evaluation.

## Scope

`service_scope = SMALLWORLD_KERNEL_ONLY`

The response exposes deterministic SHA-256 digests of the migrated SmallWorld adjacency matrix and Metropolis transition matrix. It does not expose model weights, financial decisions or process authority.

Canonical parity request digest:

`98a496a97b5db7927774ce90e9158845ba2677fa8a49f238d5acef533a5ca0e3`

Canonical response digest:

`1c4ce0498f43b989e1867ae2e4e9d522a42ee2aaa64790c0ce71c912803864fc`

The underlying V20-compatible topology digests remain:

- adjacency: `62be4b397971b14b315288f9d9e7ff106b73cec3b58fd10a9fcc7e963053373a`
- Metropolis: `6657268c1f13ed7b57038f35614ecc25bd870d147bdf7ff210f025a75f7c6fc2`

## Security boundary

- max frame: 64 KiB
- max nodes: 1024
- one allowlisted operation
- no floats in protocol objects
- deterministic recomputation on response verification
- `model_authority = NONE`
- `execution_authority = NONE`

The CLI entrypoint is `python -m agi_nexus.compute_service_v1`, but this alone does not make the component build-verified or production deployable. A later build-readiness generation must pin exact dependencies and bind a reproducibly produced artifact digest.

# NEXUS SmallWorld exact stdlib protocol v2

This generation is additive. It does **not** modify `smallworld_v1.py` or `compute_service_v1.py`.

## Why v2 exists

The v1 service hashes NumPy `float32` matrix bytes. The adjacency bytes are stable because entries are exactly 0/1, but the Metropolis diagonal depends on NumPy reduction behavior. Reimplementing those last-bit details in another runtime would make the wire contract depend on a particular NumPy reduction implementation.

V2 therefore preserves the V20 topology algorithm while changing the numeric commitment to an exact, platform-independent semantic form:

- topology: V20 ring + SHA-256 shortcut selection;
- adjacency semantics: sorted undirected edge list including self loops;
- Metropolis semantics: exact rational weights as reduced numerator/denominator pairs;
- every row sums to exactly 1 using rational arithmetic;
- wire JSON forbids floating-point values;
- runtime uses Python standard library only;
- model authority = NONE;
- execution authority = NONE.

## Compatibility

For known V20 vectors the v2 topology reproduces the legacy little-endian float32 adjacency digests:

- 8 nodes / degree 4 / 2 shortcuts: `62be4b397971b14b315288f9d9e7ff106b73cec3b58fd10a9fcc7e963053373a`
- 16 nodes / degree 4 / default shortcuts: `67b1eae1ee2730fd8fd513db5c356faa317a96e42213199f1686afb58993e9cb`

The v2 Metropolis digest is intentionally a **new semantic digest**, not a fake attempt to reproduce NumPy reduction bytes.

Canonical 8-node v2 vectors:

- adjacency semantic digest: `9c4f6f4c890877688bf88caa6b4b18b129f56b038d8c5401955c4d200e2d97a9`
- Metropolis semantic digest: `67c2a7f94c32d9f81d6f94af76146519cc7d40a3f1476685929ac196d41d0001`
- response digest: `83fec504d4b475017cc0fc2c77f3e09d3fd38f10fe43b4b86aa96ded558a35d9`

## Scope

V2 exposes only `SMALLWORLD_EXACT_DIGESTS`. It is not full NEXUS cognition, model inference, scientific-truth authority, or process execution authority.

A later deterministic build recipe must freeze the exact v2 source files and emit build/test evidence before Meta-OS may consider a deployable service artifact.

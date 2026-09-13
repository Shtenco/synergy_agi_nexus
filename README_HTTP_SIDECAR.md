# NEXUS HTTP sidecar

Additive HTTP transport around the existing proof-first `nexus_service_v3` plus namespaced operational semantic/episodic memory.

Endpoints:
- `GET /health`
- `POST /v1/runtime` — exact existing NEXUS operations (`STATUS`, `FORMAL_REASON`, `SMALLWORLD_EXACT_DIGESTS`, `CYBER_STEP`)
- `POST /v1/memory/upsert`
- `POST /v1/memory/search`

Every surface retains `execution_authority=NONE`. This sidecar does not grant financial, deployment, payment, accounting or blockchain authority.

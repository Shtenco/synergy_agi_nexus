# NEXUS HTTP sidecar

Additive HTTP transport around the existing proof-first `nexus_service_v3` plus namespaced operational semantic/episodic memory.

## Run

```bash
python -m pip install -e '.[http]'
nexus-http
```

Default bind is `127.0.0.1:8130`; override with `NEXUS_BIND_HOST` / `NEXUS_BIND_PORT`. Optional bearer auth uses `NEXUS_API_TOKEN`.

## Endpoints

- `GET /health`
- `POST /v1/runtime` — exact existing NEXUS operations (`STATUS`, `FORMAL_REASON`, `SMALLWORLD_EXACT_DIGESTS`, `CYBER_STEP`)
- `POST /v1/memory/upsert`
- `POST /v1/memory/search`

Every surface retains `execution_authority=NONE`. This sidecar does not grant financial, deployment, payment, accounting or blockchain authority.

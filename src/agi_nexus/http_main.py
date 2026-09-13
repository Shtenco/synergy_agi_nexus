from __future__ import annotations
import os
import uvicorn


def main() -> None:
    host = os.getenv("NEXUS_BIND_HOST", "127.0.0.1")
    port = int(os.getenv("NEXUS_BIND_PORT", "8130"))
    uvicorn.run("agi_nexus.http_sidecar:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    main()

from __future__ import annotations
import asyncio, os
from shttps.bootstrap import rpc_server_from_env
from .memory_sidecar import MemoryStore
from .nexus_service_v3 import handle as runtime_handle
from .shttps_rpc import build_dispatcher

def build_server():
    store=MemoryStore(os.getenv("NEXUS_MEMORY_DB","var/nexus_memory.db"))
    return rpc_server_from_env("NEXUS",build_dispatcher(store,runtime_handle),host_default="127.0.0.1",port_default=8130,roles=("NEXUS_COMPUTE",))
async def amain(): await build_server().serve_forever()
def main(): asyncio.run(amain())
if __name__=="__main__": main()

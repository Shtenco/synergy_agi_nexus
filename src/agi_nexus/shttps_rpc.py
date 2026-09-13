from __future__ import annotations
from typing import Any, Callable
from shttps.rpc import RPCDispatcher

def build_dispatcher(store, runtime_handler:Callable[[dict[str,Any]],Any])->RPCDispatcher:
    d=RPCDispatcher()
    d.register("nexus","runtime",lambda p,ctx: runtime_handler(p))
    d.register("nexus","memory.search",lambda p,ctx: store.search(str(p.get("query") or ""),list(p.get("namespaces") or []),int(p.get("limit",10))))
    d.register("nexus","memory.upsert",lambda p,ctx: store.upsert(str(p["key"]),str(p["content"]),str(p["namespace"]),dict(p.get("metadata") or {}),str(p.get("source") or ctx["peer_node_id"])))
    return d

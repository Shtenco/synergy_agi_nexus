from agi_nexus.memory_sidecar import MemoryStore
from agi_nexus.shttps_rpc import build_dispatcher
from shttps.rpc import RPCRequest

def test_nexus_shttps_memory_routes(tmp_path):
    store=MemoryStore(str(tmp_path/"m.db")); d=build_dispatcher(store,lambda p:{"runtime":p}); u=d.dispatch(RPCRequest("nexus","memory.upsert",{"key":"k","content":"earned revenue evidence","namespace":"company_actions"}),{"peer_node_id":"company"}); assert u.ok; s=d.dispatch(RPCRequest("nexus","memory.search",{"query":"revenue","namespaces":["company_actions"],"limit":5}),{"peer_node_id":"company"}); assert s.ok and s.result["items"]

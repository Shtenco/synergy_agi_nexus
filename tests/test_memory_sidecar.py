import tempfile
from agi_nexus.memory_sidecar import MemoryStore

def mem():
    f=tempfile.NamedTemporaryFile(suffix='.db',delete=False); f.close(); return MemoryStore(f.name)

def test_upsert_and_namespaced_search():
    s=mem(); s.upsert('lead-1','Client wants AI SMM and video','sales',{'revenue':100},'company'); s.upsert('exp-1','NEXUS formal proof experiment','research',{},'lab')
    out=s.search('video client',['sales'],10); assert len(out['items'])==1; assert out['items'][0]['key']=='lead-1'; assert out['execution_authority']=='NONE'

def test_upsert_replaces_same_namespace_key():
    s=mem(); s.upsert('x','old value','ops'); s.upsert('x','new value','ops'); out=s.search('new',['ops']); assert len(out['items'])==1; assert out['items'][0]['content']=='new value'

def test_blank_records_rejected():
    s=mem()
    try:s.upsert('','','x')
    except ValueError:pass
    else:raise AssertionError('blank memory must fail')

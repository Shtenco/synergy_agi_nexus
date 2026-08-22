from __future__ import annotations
import hashlib,json,sys
from typing import Any,BinaryIO
from .nexus_core_v2 import status,formal_reason,smallworld,cyber

MAX_FRAME=64*1024
class NexusServiceError(ValueError):pass

def canonical(v:Any)->bytes:
    def chk(x):
        if x is None or isinstance(x,(str,bool)):return
        if isinstance(x,int) and not isinstance(x,bool):
            if abs(x)>2**53-1:raise NexusServiceError('unsafe integer')
            return
        if isinstance(x,float):raise NexusServiceError('floats forbidden on service wire')
        if isinstance(x,list):
            for y in x:chk(y)
            return
        if isinstance(x,dict):
            if any(not isinstance(k,str) for k in x):raise NexusServiceError('bad key')
            for y in x.values():chk(y)
            return
        raise NexusServiceError('unsupported')
    chk(v);return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()

def _request_id(v):
    if not isinstance(v,str) or not v or len(v.encode())>128:raise NexusServiceError('bad request id')
    return v

def _formal_item(v):
    if not isinstance(v,dict) or set(v)!={'q','options'}:raise NexusServiceError('bad item')
    if not isinstance(v['q'],str) or not v['q'] or len(v['q'].encode())>16384:raise NexusServiceError('bad q')
    if not isinstance(v['options'],dict) or set(v['options'])!={'A','B','C','D'}:raise NexusServiceError('bad options')
    for x in v['options'].values():
        if not isinstance(x,str) or len(x.encode())>4096:raise NexusServiceError('bad option')
    return v

def handle(req):
    if not isinstance(req,dict):raise NexusServiceError('request object required')
    rid=_request_id(req.get('request_id'))
    op=req.get('operation')
    if op=='STATUS':
        if set(req)!={'request_id','operation'}:raise NexusServiceError('shape')
        payload=status()
    elif op=='FORMAL_REASON':
        if set(req)!={'request_id','operation','item'}:raise NexusServiceError('shape')
        payload=formal_reason(_formal_item(req['item']))
    elif op=='SMALLWORLD_EXACT_DIGESTS':
        if set(req)!={'request_id','operation','nodes','local_degree','shortcuts','seed'}:raise NexusServiceError('shape')
        payload=smallworld(req)
    elif op=='CYBER_STEP':
        if set(req)!={'request_id','operation','session_id','state','event'}:raise NexusServiceError('shape')
        payload=cyber(req)
    else:raise NexusServiceError('unknown operation')
    out={'schema':'nexus.runtime-response/v2','request_id':rid,'operation':op,'request_digest':hashlib.sha256(canonical(req)).hexdigest(),'payload':payload,'execution_authority':'NONE'}
    out['response_digest']=hashlib.sha256(canonical(out)).hexdigest();return out

def serve(reader:BinaryIO,writer:BinaryIO):
    while True:
        line=reader.readline(MAX_FRAME+1)
        if not line:return 0
        try:
            if len(line)>MAX_FRAME or not line.endswith(b'\n'):raise NexusServiceError('frame')
            req=json.loads(line.decode()); resp=handle(req)
        except Exception:
            resp={'schema':'nexus.runtime-error/v2','error':'INVALID_REQUEST','execution_authority':'NONE'}
        writer.write(canonical(resp)+b'\n');writer.flush()

def main():return serve(sys.stdin.buffer,sys.stdout.buffer)
if __name__=='__main__':raise SystemExit(main())

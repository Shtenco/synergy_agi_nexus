from __future__ import annotations
import hashlib,json,math,sys
from typing import Any,BinaryIO
from .artifact_core_v1 import status,formal_reason,smallworld,cyber
MAX_FRAME=64*1024
class ServiceError(ValueError): pass
def canonical(v:Any)->bytes:
 def chk(x):
  if x is None or isinstance(x,(str,bool)): return
  if isinstance(x,int) and not isinstance(x,bool):
   if abs(x)>2**53-1: raise ServiceError('unsafe integer')
   return
  if isinstance(x,float):
   if not math.isfinite(x): raise ServiceError('nonfinite')
   return
  if isinstance(x,list):
   for y in x: chk(y)
   return
  if isinstance(x,dict):
   if any(not isinstance(k,str) for k in x): raise ServiceError('bad key')
   for y in x.values(): chk(y)
   return
  raise ServiceError('unsupported')
 chk(v); return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def handle(req):
 if not isinstance(req,dict): raise ServiceError('object')
 rid=req.get('request_id'); op=req.get('operation')
 if not isinstance(rid,str) or not rid or len(rid.encode())>128: raise ServiceError('id')
 if op=='STATUS':
  if set(req)!={'request_id','operation'}: raise ServiceError('shape')
  payload=status()
 elif op=='FORMAL_REASON':
  if set(req)!={'request_id','operation','item'}: raise ServiceError('shape')
  item=req['item']
  if not isinstance(item,dict) or set(item)!={'q','options'} or not isinstance(item['q'],str) or not isinstance(item['options'],dict) or set(item['options'])!={'A','B','C','D'}: raise ServiceError('item')
  payload=formal_reason(item)
 elif op=='SMALLWORLD_EXACT_DIGESTS':
  if set(req)!={'request_id','operation','nodes','local_degree','shortcuts','seed'}: raise ServiceError('shape')
  payload=smallworld(req)
 elif op=='CYBER_STEP':
  if set(req)!={'request_id','operation','session_id','state','event'}: raise ServiceError('shape')
  payload=cyber(req)
 else: raise ServiceError('op')
 out={'schema':'nexus.artifact-response/v1','request_id':rid,'operation':op,'request_digest':hashlib.sha256(canonical(req)).hexdigest(),'payload':payload,'execution_authority':'NONE'}; out['response_digest']=hashlib.sha256(canonical(out)).hexdigest(); return out
def serve(r:BinaryIO,w:BinaryIO):
 while True:
  line=r.readline(MAX_FRAME+1)
  if not line:return 0
  try:
   if len(line)>MAX_FRAME or not line.endswith(b'\n'): raise ServiceError('frame')
   out=handle(json.loads(line.decode()))
  except Exception: out={'schema':'nexus.artifact-error/v1','error':'INVALID_REQUEST','execution_authority':'NONE'}
  w.write(canonical(out)+b'\n');w.flush()
def main(): return serve(sys.stdin.buffer,sys.stdout.buffer)

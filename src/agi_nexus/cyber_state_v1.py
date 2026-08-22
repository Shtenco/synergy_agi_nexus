from __future__ import annotations
import hashlib, json
from typing import Any

NODE_TYPES=('context','domain','cause','effect','goal','error','action','constraint')
MAX_VALUE_BYTES=2048
MAX_SEQUENCE=64
class CyberStateError(ValueError): pass

def canonical(v:Any)->bytes:
    def chk(x):
        if x is None or isinstance(x,(str,bool)): return
        if isinstance(x,int) and not isinstance(x,bool):
            if abs(x)>2**53-1: raise CyberStateError('unsafe integer')
            return
        if isinstance(x,float): raise CyberStateError('floats forbidden')
        if isinstance(x,list):
            for y in x:chk(y)
            return
        if isinstance(x,dict):
            if any(not isinstance(k,str) for k in x):raise CyberStateError('bad key')
            for y in x.values():chk(y)
            return
        raise CyberStateError('unsupported')
    chk(v);return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()

def state_digest(state):
    b=dict(state);b.pop('state_digest',None);return hashlib.sha256(canonical(b)).hexdigest()

def initial_state(session_id:str):
    if not isinstance(session_id,str) or not session_id or len(session_id.encode())>128:raise CyberStateError('bad session_id')
    s={'schema':'nexus.cyber-state/v1','session_id':session_id,'sequence':0,'nodes':{k:'' for k in NODE_TYPES},'formal_status':'UNKNOWN','authority':'NONE','previous_state_digest':'0'*64}
    s['state_digest']=state_digest(s);return s

def verify_state(s):
    req={'schema','session_id','sequence','nodes','formal_status','authority','previous_state_digest','state_digest'}
    if not isinstance(s,dict) or set(s)!=req or s['schema']!='nexus.cyber-state/v1':raise CyberStateError('bad state shape')
    if isinstance(s['sequence'],bool) or not isinstance(s['sequence'],int) or not 0<=s['sequence']<=MAX_SEQUENCE:raise CyberStateError('bad sequence')
    if not isinstance(s['nodes'],dict) or tuple(s['nodes'].keys())!=NODE_TYPES:raise CyberStateError('bad nodes')
    for v in s['nodes'].values():
        if not isinstance(v,str) or len(v.encode())>MAX_VALUE_BYTES:raise CyberStateError('node too large')
    if s['formal_status'] not in {'UNKNOWN','VERIFIED','REJECTED'}:raise CyberStateError('bad formal_status')
    if s['authority'] not in {'NONE','FORMAL_VERIFIED','CYBER_FEEDBACK'}:raise CyberStateError('bad authority')
    if s['state_digest']!=state_digest(s):raise CyberStateError('state digest mismatch')
    return s

def step(state,event):
    verify_state(state)
    if state['sequence']>=MAX_SEQUENCE:raise CyberStateError('sequence exhausted')
    if not isinstance(event,dict) or set(event)!={'kind','updates','formal_status'}:raise CyberStateError('bad event')
    if event['kind'] not in {'OBSERVE','FORMAL_RESULT','FEEDBACK'}:raise CyberStateError('bad kind')
    if event['formal_status'] not in {'UNKNOWN','VERIFIED','REJECTED'}:raise CyberStateError('bad formal status')
    updates=event['updates']
    if not isinstance(updates,dict) or any(k not in NODE_TYPES for k in updates):raise CyberStateError('bad updates')
    nodes=dict(state['nodes'])
    for k,v in updates.items():
        if not isinstance(v,str) or len(v.encode())>MAX_VALUE_BYTES:raise CyberStateError('bad value')
        nodes[k]=v
    authority='FORMAL_VERIFIED' if event['formal_status']=='VERIFIED' else ('CYBER_FEEDBACK' if event['kind']=='FEEDBACK' else 'NONE')
    out={'schema':'nexus.cyber-state/v1','session_id':state['session_id'],'sequence':state['sequence']+1,'nodes':nodes,'formal_status':event['formal_status'],'authority':authority,'previous_state_digest':state['state_digest']}
    out['state_digest']=state_digest(out);return out

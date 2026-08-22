from __future__ import annotations
from .r710_frozen.runtime_v2 import formal_pass
from .smallworld_core_v2 import exact_digests
from .cyber_state_v1 import initial_state,step,verify_state
CORE_COMPONENTS=('R710_FROZEN_FORMAL_PROOF','EXACT_SMALLWORLD','BOUNDED_CYBER_STATE')
def status(): return {'schema':'nexus.artifact-core-status/v1','status':'READY','components':list(CORE_COMPONENTS),'authority_order':['FORMAL_VERIFIED','CYBER_FEEDBACK','NONE'],'r710_source':'EXACT_FROZEN_UPSTREAM','execution_authority':'NONE'}
def formal_reason(item):
 r=formal_pass(item); r['authority']='FORMAL_VERIFIED' if r['status']=='VERIFIED' else 'NONE'
 if r['status']!='VERIFIED': r['answer']=None
 r['execution_authority']='NONE'; return r
def smallworld(req):
 a,m=exact_digests(req['nodes'],req.get('local_degree',4),req.get('shortcuts'),req.get('seed','NEXUS-V20')); return {'adjacency_semantic_digest':a,'metropolis_semantic_digest':m,'execution_authority':'NONE'}
def cyber(req):
 s=req.get('state'); s=initial_state(req['session_id']) if s is None else verify_state(s); return step(s,req['event'])

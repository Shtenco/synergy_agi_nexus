from __future__ import annotations
from .r710.runtime_v2 import formal_pass
from .smallworld_core_v2 import exact_digests
from .cyber_state_v1 import initial_state,step,verify_state

CORE_COMPONENTS=('R710_FORMAL_PROOF','EXACT_SMALLWORLD','BOUNDED_CYBER_STATE')

def status():
    return {'schema':'nexus.core-status/v2','status':'READY','components':list(CORE_COMPONENTS),'authority_order':['FORMAL_VERIFIED','CYBER_FEEDBACK','NONE'],'neural_hypothesis':'NOT_MIGRATED_NOT_REQUIRED_FOR_EXACT_CORE','execution_authority':'NONE'}

def formal_reason(item):
    result=formal_pass(item)
    if result['status']=='VERIFIED': result['authority']='FORMAL_VERIFIED'
    else: result['authority']='NONE'; result['answer']=None
    result['execution_authority']='NONE';return result

def smallworld(request):
    a,m=exact_digests(request['nodes'],request.get('local_degree',4),request.get('shortcuts'),request.get('seed','NEXUS-V20'))
    return {'adjacency_semantic_digest':a,'metropolis_semantic_digest':m,'execution_authority':'NONE'}

def cyber(request):
    s=request.get('state')
    if s is None:s=initial_state(request['session_id'])
    else:verify_state(s)
    return step(s,request['event'])

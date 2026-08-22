from __future__ import annotations
from fractions import Fraction
import hashlib, heapq, json
from typing import Any

MAX_NODES=1024
MAX_SHORTCUTS=4096
class SmallWorldCoreError(ValueError): pass

def _int(v,name,lo=0,hi=None):
    if isinstance(v,bool) or not isinstance(v,int) or v<lo or (hi is not None and v>hi): raise SmallWorldCoreError(f'invalid {name}')
    return v

def canonical_json(v:Any)->bytes:
    def chk(x):
        if x is None or isinstance(x,(str,bool)): return
        if isinstance(x,int) and not isinstance(x,bool):
            if abs(x)>2**53-1: raise SmallWorldCoreError('unsafe integer')
            return
        if isinstance(x,float): raise SmallWorldCoreError('floats forbidden')
        if isinstance(x,list):
            for y in x: chk(y)
            return
        if isinstance(x,dict):
            if any(not isinstance(k,str) for k in x): raise SmallWorldCoreError('non-string key')
            for y in x.values(): chk(y)
            return
        raise SmallWorldCoreError('unsupported value')
    chk(v); return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()

def digest(v): return hashlib.sha256(canonical_json(v)).hexdigest()

def topology(nodes:int,local_degree:int=4,shortcuts:int|None=None,seed:str='NEXUS-V20'):
    nodes=_int(nodes,'nodes',1,MAX_NODES); local_degree=_int(local_degree,'local_degree',0,MAX_NODES)
    if shortcuts is not None: shortcuts=_int(shortcuts,'shortcuts',0,MAX_SHORTCUTS)
    if not isinstance(seed,str) or not seed or len(seed.encode())>256: raise SmallWorldCoreError('invalid seed')
    nb=[{i} for i in range(nodes)]
    if nodes==1:return ((0,),)
    local_degree=min(local_degree,nodes-1)
    if local_degree%2: local_degree-=1
    local_degree=max(2 if nodes>2 else nodes-1,local_degree); r=max(1,local_degree//2)
    for i in range(nodes):
        for d in range(1,r+1):
            j=(i+d)%nodes; nb[i].add(j); nb[j].add(i)
    missing=sum(1 for i in range(nodes) for j in range(i+1,nodes) if j not in nb[i])
    wanted=min(max(1,nodes//4) if shortcuts is None else shortcuts,missing)
    if wanted:
        def candidates():
            for i in range(nodes):
                for j in range(i+1,nodes):
                    if j not in nb[i]: yield hashlib.sha256(f'{seed}:{nodes}:{i}:{j}'.encode()).digest(),i,j
        for _,i,j in heapq.nsmallest(wanted,candidates()): nb[i].add(j); nb[j].add(i)
    return tuple(tuple(sorted(x)) for x in nb)

def exact_digests(nodes:int,local_degree:int=4,shortcuts:int|None=None,seed:str='NEXUS-V20'):
    t=topology(nodes,local_degree,shortcuts,seed)
    adj={'schema':'nexus.smallworld-adjacency-semantics/v2','nodes':len(t),'edges':[[i,j] for i,row in enumerate(t) for j in row if i<=j]}
    deg=[len(row)-1 for row in t]; rows=[]
    for i,row in enumerate(t):
        ws=[]; off=Fraction(0,1)
        for j in row:
            if i==j: continue
            w=Fraction(1,1+max(deg[i],deg[j])); off+=w; ws.append({'col':j,'num':w.numerator,'den':w.denominator})
        d=Fraction(1,1)-off; ws.append({'col':i,'num':d.numerator,'den':d.denominator}); ws.sort(key=lambda x:x['col'])
        if sum((Fraction(x['num'],x['den']) for x in ws),Fraction(0,1))!=1: raise SmallWorldCoreError('row sum')
        rows.append({'row':i,'weights':ws})
    met={'schema':'nexus.smallworld-metropolis-semantics/v2','nodes':len(t),'rows':rows}
    return digest(adj),digest(met)

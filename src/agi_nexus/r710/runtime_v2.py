from .compiler_v2 import compile_item
from .solver_v2 import solve
from .verifier_v2 import verify
from .option_matcher import match_option
from .schemas import dump_obj

def formal_pass(item):
    ir=compile_item(item)
    if ir is None:return {'status':'UNKNOWN','answer':None,'ir':None,'proof':None,'verification':None}
    proof=solve(ir); ver=verify(ir,proof)
    ans=match_option(item,proof.conclusion) if proof and ver.status=='VERIFIED' else None
    status='VERIFIED' if ver.status=='VERIFIED' and ans is not None else ('REJECTED' if ver.status=='REJECTED' else 'UNKNOWN')
    return {'status':status,'answer':ans,'ir':dump_obj(ir),'proof':dump_obj(proof) if proof else None,'verification':dump_obj(ver)}

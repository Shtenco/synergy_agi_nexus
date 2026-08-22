import math, statistics, json
from pathlib import Path
from .schemas import Verification
TRUST=json.loads((Path(__file__).with_name('trusted_facts.json')).read_text(encoding='utf-8'))

def verify(ir,proof):
    if ir is None or proof is None:return Verification('UNKNOWN','no proof')
    a=ir.args;op=a.get('op'); got=proof.conclusion; expected=None
    try:
      if ir.kind=='ARITH':
        if op=='mul':expected=a['a']*a['b']
        elif op=='add':expected=a['a']+a['b']
        elif op=='sub':expected=a['a']-a['b']
        elif op=='div':expected=a['a']/a['b']
        elif op=='pow':expected=a['a']**a['b']
        elif op=='gcd':expected=math.gcd(int(a['a']),int(a['b']))
        elif op=='lcm':expected=abs(int(a['a'])*int(a['b']))//math.gcd(int(a['a']),int(a['b']))
        elif op=='solve_div':expected=a['a']*a['b']
        elif op=='solve_mul':expected=a['b']/a['a']
        elif op=='solve_add':expected=a['b']-a['a']
        elif op=='solve_sub':expected=a['b']+a['a']
        elif op=='balance':expected=a['initial']-a['debit']+a['credit']
      elif ir.kind=='STAT':expected=statistics.median(a['values']) if op=='median' else sum(a['values'])/len(a['values']) if op=='mean' else None
      elif ir.kind=='RATIO':expected=100*a['part']/(a['total'] if op=='percent_of' else sum(a['parts']))
      elif ir.kind=='PROB' and op=='binomial_expectation':expected=a['n']*a['p']
      elif ir.kind=='GEOM':expected=a['a']*a['b'] if op=='rectangle_area' else 2*(a['a']+a['b']) if op=='rectangle_perimeter' else 180 if op=='triangle_angles' else None
      elif ir.kind=='LOGIC':expected={'syllogism_no_r_t':'No','modus_ponens':'Q true','gt_transitivity':'A > C','de_morgan_and':'not P or not Q','xor_a_false':'B true','mutex_x':'Y did not occur','modus_tollens_rain':'No rain','generic_mp':'B true','generic_mt':'A false','implication_chain':'R','implication_equiv':'not P or Q','disjoint_sets':'Disjoint','some_ab_no_bc':'Those A that are B are not C'}.get(op)
      elif ir.kind=='CYBER':expected={'negative_feedback':'negative feedback','positive_feedback':'positive feedback','open_loop':'open loop','feedback_control':'feedback control'}.get(op)
      elif ir.kind=='CAUSAL':expected={'confounder':'causality not established due to confounder','need_control':'check alternative causes and control'}.get(op)
      elif ir.kind=='EVIDENCE':expected={'shared_source_independence':'No','common_source_reduces_independence':'common primary source'}.get(op)
      elif ir.kind=='POLICY':expected='No' if op in ['trust_gate_reject','integrity_fail','and_gate_false','dependency_fail'] else 'formally verified result' if op=='verified_proof_priority' else ('Yes' if a['observed']>=a['required'] else 'No') if op=='threshold' else None
      elif ir.kind=='CODE':
        expected={'sql_where':'WHERE','lifo':'stack','fifo':'queue','zero_index':0,'break':'exit current loop','continue':'next iteration','bool_zero':'False','binary_search_complexity':'O(log n)','linear_scan_complexity':'O(n)','git_commit':'git commit'}.get(op)
        if op=='py_len':expected=a['n']
        elif op=='py_mod':expected=a['a']%a['b']
        elif op=='py_floordiv':expected=a['a']//a['b']
        elif op=='py_range':expected=list(range(a['start'],a['stop'],a['step']))
        elif op=='lifo_sequence':expected=a['sequence'][-1]
        elif op=='fifo_sequence':expected=a['sequence'][0]
      elif ir.kind=='RUSSIAN':
        expected={'v_techenie_genitive':'genitive','antonym_temporary':'permanent','idiom_attention':'take into account','concession':'concession','cause_conjunction':'cause','condition_conjunction':'condition'}.get(op)
        if op=='government':expected={'case':a['case'],'governing':a['governing']}
        elif op=='stress_family':expected={'stem':a['stem'],'stress':'ending'}
        elif op=='stress_lexicon':expected=TRUST['russian']['stress_lexicon'][a['word']]
        elif op=='numeral_genitive_plural':expected='genitive_plural'
        elif op=='preposition_k_dative':expected='dative'
      elif ir.kind=='SEMANTIC' and op=='select_consistent':
        bad=[]
        for key,text in a['options'].items():
            t=str(text).lower().replace('ё','е'); contradiction=False
            if ('удалил' in t and ('стал больше' in t or 'увелич' in t)):contradiction=True
            if ('причин' in t and 'после следств' in t and ('вызвал' in t or 'вызвала' in t)):contradiction=True
            if ('сначала' in t and ('закончил' in t or 'завершил' in t) and 'затем' in t and ('начал' in t or 'началась' in t) and 'впервые' in t):contradiction=True
            if contradiction:bad.append(key)
        good=[k for k in a['options'] if k not in bad]
        expected={'option_key':good[0]} if len(good)==1 else None
      elif ir.kind=='FACT':
        if op=='nearest_star':
            d=TRUST['astronomy']['distance_ly_from_earth'].copy()
            if a.get('excluding_sun'):d.pop('Sun',None)
            expected=min(d,key=d.get)
        elif op=='chemical_symbol':expected=TRUST['science']['symbols'][a['element']]
        elif op=='http_status':expected=TRUST['computing']['http'][a['code']]
        elif op=='computing_principle':expected=TRUST['computing']['principles'][a['key']]
    except Exception as e:return Verification('REJECTED','verifier exception '+repr(e))
    if expected is None:return Verification('UNKNOWN','no independent verifier for operator')
    same=(abs(float(expected)-float(got))<1e-9) if isinstance(expected,(int,float)) and isinstance(got,(int,float)) else expected==got
    return Verification('VERIFIED' if same else 'REJECTED','independent recomputation',expected)

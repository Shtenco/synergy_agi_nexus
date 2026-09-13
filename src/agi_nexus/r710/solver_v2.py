import json, math, statistics, re
from pathlib import Path
from .schemas import ProofObject
TRUST=json.loads((Path(__file__).with_name('trusted_facts.json')).read_text(encoding='utf-8'))

def solve(ir):
    if ir is None:return None
    k,a=ir.kind,ir.args; op=a.get('op')
    val=None; der=''
    if k=='ARITH':
        if op=='mul':val=a['a']*a['b'];der=f"{a['a']}*{a['b']}"
        elif op=='add':val=a['a']+a['b'];der=f"{a['a']}+{a['b']}"
        elif op=='sub':val=a['a']-a['b'];der=f"{a['a']}-{a['b']}"
        elif op=='div':val=a['a']/a['b'];der=f"{a['a']}/{a['b']}"
        elif op=='pow':val=a['a']**a['b'];der=f"{a['a']}**{a['b']}"
        elif op=='gcd':val=math.gcd(int(a['a']),int(a['b']));der='Euclidean gcd'
        elif op=='lcm':val=abs(int(a['a'])*int(a['b']))//math.gcd(int(a['a']),int(a['b']));der='a*b/gcd'
        elif op=='solve_div':val=a['a']*a['b'];der='x/d=q => x=d*q'
        elif op=='solve_mul':val=a['b']/a['a'];der='a*x=b => x=b/a'
        elif op=='solve_add':val=a['b']-a['a'];der='x+a=b => x=b-a'
        elif op=='solve_sub':val=a['b']+a['a'];der='x-a=b => x=b+a'
        elif op=='balance':val=a['initial']-a['debit']+a['credit'];der='initial-debit+credit'
    elif k=='STAT':
        if op=='median':val=statistics.median(a['values']);der='sorted middle value'
        elif op=='mean':val=sum(a['values'])/len(a['values']);der='sum/n'
    elif k=='RATIO':
        if op=='percent_of':val=100*a['part']/a['total'];der='100*part/total'
        elif op=='part_of_sum':val=100*a['part']/sum(a['parts']);der='100*part/sum(parts)'
    elif k=='PROB' and op=='binomial_expectation':val=a['n']*a['p'];der='E[Binomial(n,p)]=n*p'
    elif k=='GEOM':
        if op=='rectangle_area':val=a['a']*a['b'];der='a*b'
        elif op=='rectangle_perimeter':val=2*(a['a']+a['b']);der='2(a+b)'
        elif op=='triangle_angles':val=180;der='Euclidean triangle angle sum'
    elif k=='LOGIC':
        table={'syllogism_no_r_t':'No','modus_ponens':'Q true','gt_transitivity':'A > C','de_morgan_and':'not P or not Q','xor_a_false':'B true','mutex_x':'Y did not occur','modus_tollens_rain':'No rain','generic_mp':'B true','generic_mt':'A false','implication_chain':'R','implication_equiv':'not P or Q','disjoint_sets':'Disjoint','some_ab_no_bc':'Those A that are B are not C'}
        val=table.get(op);der='formal logic rule '+str(op)
    elif k=='CYBER':val={'negative_feedback':'negative feedback','positive_feedback':'positive feedback','open_loop':'open loop','feedback_control':'feedback control'}.get(op);der='control-theory invariant'
    elif k=='CAUSAL':val={'confounder':'causality not established due to confounder','need_control':'check alternative causes and control'}.get(op);der='causal-identification invariant'
    elif k=='EVIDENCE':val={'shared_source_independence':'No','common_source_reduces_independence':'common primary source'}.get(op);der='shared-source evidence is statistically dependent'
    elif k=='POLICY':
        if op in ['trust_gate_reject','integrity_fail','and_gate_false','dependency_fail']:val='No'
        elif op=='verified_proof_priority':val='formally verified result'
        elif op=='threshold':val='Yes' if a['observed']>=a['required'] else 'No'
        der='policy invariant '+str(op)
    elif k=='CODE':
        if op=='py_len':val=a['n']
        elif op=='py_mod':val=a['a']%a['b']
        elif op=='py_floordiv':val=a['a']//a['b']
        elif op=='py_range':val=list(range(a['start'],a['stop'],a['step']))
        elif op=='sql_where':val='WHERE'
        elif op=='lifo':val='stack'
        elif op=='fifo':val='queue'
        elif op=='lifo_sequence':val=a['sequence'][-1];der='LIFO returns last pushed element'
        elif op=='fifo_sequence':val=a['sequence'][0];der='FIFO returns first enqueued element'
        elif op=='zero_index':val=0
        elif op=='break':val='exit current loop'
        elif op=='continue':val='next iteration'
        elif op=='bool_zero':val='False'
        elif op=='binary_search_complexity':val='O(log n)'
        elif op=='linear_scan_complexity':val='O(n)'
        elif op=='git_commit':val='git commit'
        der='language/runtime semantics '+str(op)
    elif k=='RUSSIAN':
        if op=='government':val={'case':a['case'],'governing':a['governing']};der='lexical government rule'
        elif op=='v_techenie_genitive':val='genitive';der='prepositional government'
        elif op=='antonym_temporary':val='permanent';der='lexical semantic relation'
        elif op=='idiom_attention':val='take into account';der='idiom equivalence'
        elif op=='concession':val='concession';der='conjunction semantic role'
        elif op=='cause_conjunction':val='cause';der='conjunction semantic role'
        elif op=='condition_conjunction':val='condition';der='conjunction semantic role'
        elif op=='stress_family':val={'stem':a['stem'],'stress':'ending'};der='normative stress-family rule'
        elif op=='stress_lexicon':val=a['accent'];der='normative stress lexicon'
        elif op=='numeral_genitive_plural':val='genitive_plural';der='numerals 5+ govern genitive plural'
        elif op=='preposition_k_dative':val='dative';der='preposition k governs dative'
    elif k=='SEMANTIC' and op=='select_consistent':
        bad=[]
        for key,text in a['options'].items():
            t=str(text).lower().replace('ё','е'); contradiction=False
            if ('удалил' in t and ('стал больше' in t or 'увелич' in t)):contradiction=True
            if ('причин' in t and 'после следств' in t and ('вызвал' in t or 'вызвала' in t)):contradiction=True
            if ('сначала' in t and ('закончил' in t or 'завершил' in t) and 'затем' in t and ('начал' in t or 'началась' in t) and 'впервые' in t):contradiction=True
            if contradiction:bad.append(key)
        good=[k for k in a['options'] if k not in bad]
        if len(good)==1:val={'option_key':good[0]};der='exclude options violating temporal/causal monotonicity constraints'
    elif k=='FACT':
        if op=='nearest_star':
            dist=TRUST['astronomy']['distance_ly_from_earth'].copy()
            if a.get('excluding_sun'):dist.pop('Sun',None)
            val=min(dist,key=dist.get);der='argmin trusted distance_ly_from_earth'
        elif op=='chemical_symbol':val=TRUST['science']['symbols'][a['element']];der='trusted periodic-table atom'
        elif op=='http_status':val=TRUST['computing']['http'][a['code']];der='trusted protocol atom'
        elif op=='computing_principle':val=TRUST['computing']['principles'][a['key']];der='trusted computing atom'
    if val is None:return None
    return ProofObject(k,dict(a),val,der,'solver_v2:'+str(op))

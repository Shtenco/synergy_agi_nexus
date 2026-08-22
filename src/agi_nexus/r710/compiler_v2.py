import re, math, json
from pathlib import Path
from .schemas import FormalIR

TRUST=json.loads((Path(__file__).with_name('trusted_facts.json')).read_text(encoding='utf-8'))

def norm(s):
    return (s or '').lower().replace('ё','е').replace('–','-').replace('—','-').strip()

def nums(s):
    return [float(x.replace(',','.')) for x in re.findall(r'(?<![A-Za-zА-Яа-я])\d+(?:[.,]\d+)?',s)]

def compile_item(item):
    q=norm(item['q']); src=item['q']
    m=re.search(r'(?:сколько будет|чему равно|вычисл\w*)\s+(\d+)\s*[×*]\s*(\d+)',q)
    if m:return FormalIR('ARITH',{'op':'mul','a':int(m.group(1)),'b':int(m.group(2))},src,'arith_mul')
    m=re.search(r'(?:сколько будет|чему равно|вычисл\w*)\s+(\d+)\s*\+\s*(\d+)',q)
    if m:return FormalIR('ARITH',{'op':'add','a':int(m.group(1)),'b':int(m.group(2))},src,'arith_add')
    m=re.search(r'(?:сколько будет|чему равно|вычисл\w*)\s+(\d+)\s*-\s*(\d+)',q)
    if m:return FormalIR('ARITH',{'op':'sub','a':int(m.group(1)),'b':int(m.group(2))},src,'arith_sub')
    m=re.search(r'(?:сколько будет|чему равно|вычисл\w*)\s+(\d+)\s*/\s*(\d+)',q)
    if m and int(m.group(2))!=0:return FormalIR('ARITH',{'op':'div','a':int(m.group(1)),'b':int(m.group(2))},src,'arith_div')
    m=re.search(r'(?:чему равно|вычисл\w*)\s+(\d+)\s*\^\s*(\d+)',q)
    if m:return FormalIR('ARITH',{'op':'pow','a':int(m.group(1)),'b':int(m.group(2))},src,'arith_pow')
    m=re.search(r'наибольш\w+ общ\w+ делител\w*.*?(\d+).*?(\d+)',q)
    if m:return FormalIR('ARITH',{'op':'gcd','a':int(m.group(1)),'b':int(m.group(2))},src,'gcd')
    m=re.search(r'наименьш\w+ общ\w+ кратн\w*.*?(\d+).*?(\d+)',q)
    if m:return FormalIR('ARITH',{'op':'lcm','a':int(m.group(1)),'b':int(m.group(2))},src,'lcm')
    m=re.search(r'x\s*/\s*(\d+)\s*=\s*(\d+)',q)
    if m:return FormalIR('ARITH',{'op':'solve_div','a':int(m.group(1)),'b':int(m.group(2))},src,'solve_x_div')
    m=re.search(r'(\d+)\s*x\s*=\s*(\d+)',q)
    if m:return FormalIR('ARITH',{'op':'solve_mul','a':int(m.group(1)),'b':int(m.group(2))},src,'solve_ax')
    m=re.search(r'x\s*\+\s*(\d+)\s*=\s*(\d+)',q)
    if m:return FormalIR('ARITH',{'op':'solve_add','a':int(m.group(1)),'b':int(m.group(2))},src,'solve_x_add')
    m=re.search(r'x\s*-\s*(\d+)\s*=\s*(\d+)',q)
    if m:return FormalIR('ARITH',{'op':'solve_sub','a':int(m.group(1)),'b':int(m.group(2))},src,'solve_x_sub')
    if 'медиан' in q:
        v=nums(q)
        if len(v)>=3:return FormalIR('STAT',{'op':'median','values':v[-5:] if len(v)>=5 else v},src,'median')
    if 'среднее арифметическое' in q:
        v=nums(q)
        if len(v)>=2:return FormalIR('STAT',{'op':'mean','values':v},src,'mean')
    m=re.search(r'(?:сколько|какой) процентов составляет\s+(\d+(?:[.,]\d+)?)\s+от\s+(\d+(?:[.,]\d+)?)',q)
    if m:return FormalIR('RATIO',{'op':'percent_of','part':float(m.group(1).replace(',','.')),'total':float(m.group(2).replace(',','.'))},src,'percent_of')
    if ('маршрут' in q or 'путь' in q or 'участ' in q) and 'процент' in q:
        v=nums(q)
        if len(v)>=2:
            a,b=v[0],v[1]
            return FormalIR('RATIO',{'op':'part_of_sum','part':a,'parts':[a,b]},src,'part_of_total_segments')
    if 'вероятност' in q and ('ожидаем' in q or 'математическ' in q) and ('испытан' in q or 'попыт' in q):
        v=nums(q); p=next((x for x in v if 0<=x<=1),None); n=next((int(x) for x in v if x>=2 and float(x).is_integer()),None)
        if p is not None and n is not None:return FormalIR('PROB',{'op':'binomial_expectation','p':p,'n':n},src,'binomial_expectation')
    if any(w in q for w in ['счете','счёт','резерв','баланс']) and any(w in q for w in ['списал','потер','вычли']) and any(w in q for w in ['начисл','пополнил','пополн','добавил']):
        v=nums(q)
        if len(v)>=3:return FormalIR('ARITH',{'op':'balance','initial':v[0],'debit':v[1],'credit':v[2]},src,'worded_balance')
    if 'прямоугольник' in q and 'площад' in q:
        v=nums(q)
        if len(v)>=2:return FormalIR('GEOM',{'op':'rectangle_area','a':v[0],'b':v[1]},src,'rectangle_area')
    if 'периметр' in q and 'прямоугольник' in q:
        v=nums(q)
        if len(v)>=2:return FormalIR('GEOM',{'op':'rectangle_perimeter','a':v[0],'b':v[1]},src,'rectangle_perimeter')
    if 'сумм' in q and 'угл' in q and 'треуголь' in q:return FormalIR('GEOM',{'op':'triangle_angles'},src,'triangle_angles')
    if 'все r являются s' in q and 'ни один s не является t' in q:return FormalIR('LOGIC',{'op':'syllogism_no_r_t'},src,'syllogism')
    if 'если p истинно, то q истинно' in q and re.search(r'\bp истинно',q):return FormalIR('LOGIC',{'op':'modus_ponens','p':'P','q':'Q'},src,'modus_ponens')
    if 'a > b' in q and 'b > c' in q:return FormalIR('LOGIC',{'op':'gt_transitivity'},src,'gt_transitivity')
    if 'де морган' in q and 'не (p и q)' in q:return FormalIR('LOGIC',{'op':'de_morgan_and'},src,'de_morgan')
    if 'ровно одно' in q and 'a' in q and 'b' in q and 'a ложно' in q:return FormalIR('LOGIC',{'op':'xor_a_false'},src,'xor')
    if 'взаимоисключ' in q and 'x произошло' in q:return FormalIR('LOGIC',{'op':'mutex_x'},src,'mutex')
    if ('modus tollens' in q or ('если идет дождь' in q and ('не мокр' in q))) :return FormalIR('LOGIC',{'op':'modus_tollens_rain'},src,'modus_tollens')
    if 'если a, то b' in q and 'a истинно' in q:return FormalIR('LOGIC',{'op':'generic_mp'},src,'generic_mp')
    if 'если a, то b' in q and 'b ложно' in q:return FormalIR('LOGIC',{'op':'generic_mt'},src,'generic_mt')
    if 'из p следует q' in q and 'из q следует r' in q:return FormalIR('LOGIC',{'op':'implication_chain'},src,'implication_chain')
    if 'эквивалентно импликации' in q and ('p→q' in q or 'p->q' in q):return FormalIR('LOGIC',{'op':'implication_equiv'},src,'implication_equiv')
    if 'не имеют общих элементов' in q:return FormalIR('LOGIC',{'op':'disjoint_sets'},src,'disjoint_sets')
    if 'некоторые a являются b' in q and 'ни один b не является c' in q:return FormalIR('LOGIC',{'op':'some_ab_no_bc'},src,'syllogism_some')
    if ('уменьшает нагрев' in q or 'увеличивает охлаждение' in q) and ('выше устав' in q or 'температур' in q):return FormalIR('CYBER',{'op':'negative_feedback'},src,'negative_feedback')
    if 'усиливает отклонение' in q:return FormalIR('CYBER',{'op':'positive_feedback'},src,'positive_feedback')
    if ('не измеряет результат' in q or 'не измеряет выход' in q):return FormalIR('CYBER',{'op':'open_loop'},src,'open_loop')
    if 'сравнивает цель' in q and ('корректирует' in q or 'меняет' in q):return FormalIR('CYBER',{'op':'feedback_control'},src,'feedback_control')
    if ('скрыт' in q or 'конфаун' in q) and ('влияет' in q or 'общая причина' in q):return FormalIR('CAUSAL',{'op':'confounder'},src,'confounder')
    if ('внешн' in q and 'сбо' in q) or ('альтернативн' in q and 'причин' in q):return FormalIR('CAUSAL',{'op':'need_control'},src,'causal_control')
    if (('один физическ' in q or 'одного физическ' in q or 'один и тот же физическ' in q or 'дублируют один физическ' in q) and ('независим' in q or 'свидетельств' in q or 'подтвержден' in q)):
        return FormalIR('EVIDENCE',{'op':'shared_source_independence','shared_source':True},src,'shared_source_independence')
    if ('общий первичный источник' in q or 'общего первичного источника' in q) and 'независим' in q:return FormalIR('EVIDENCE',{'op':'common_source_reduces_independence'},src,'common_source')
    if 'провер' in q and 'не подтверждает' in q and ('trust' in q or 'довер' in q):return FormalIR('POLICY',{'op':'trust_gate_reject'},src,'trust_gate')
    if ('foreign model' in q or 'модел' in q) and 'формальн' in q and ('приоритет' in q or 'что имеет' in q):return FormalIR('POLICY',{'op':'verified_proof_priority'},src,'proof_priority')
    if ('подпис' in q or 'хэш' in q or 'хеш' in q) and ('недейств' in q or 'не совп' in q) and ('довер' in q or 'принят' in q):return FormalIR('POLICY',{'op':'integrity_fail'},src,'integrity_fail')
    if 'verified=true' in q and 'risk=high' in q:return FormalIR('POLICY',{'op':'and_gate_false'},src,'policy_and')
    if 'только после успешного b' in q and ('b завершился ошибкой' in q or 'b не выполнен' in q):return FormalIR('POLICY',{'op':'dependency_fail'},src,'dependency')
    if 'сервер' in q and ('доступен' in q or 'доступны' in q or 'недоступен' in q) and ('хотя бы два' in q or 'не менее двух' in q):
        observed=0
        for mm in re.finditer(r'([a-z](?:\s*(?:,|и)\s*[a-z])*)\s+доступ(?:ен|ны|на|но)\b',q): observed += len(re.findall(r'\b[a-z]\b',mm.group(1)))
        return FormalIR('POLICY',{'op':'threshold','required':2.0,'observed':float(observed)},src,'server_availability_threshold')
    if ('кворум' in q or 'нужн' in q) and ('голос' in q or 'подтвержден' in q or 'сервер' in q):
        mr=re.search(r'(?:нужно|нужны|не менее|хотя бы)\s*(?:не менее\s*)?(\d+)',q); mo=re.search(r'(?:получено|есть|имеется|получены)\s*(\d+)',q)
        if mr and mo:return FormalIR('POLICY',{'op':'threshold','required':float(mr.group(1)),'observed':float(mo.group(1))},src,'threshold_explicit')
        m2=re.search(r'нужно\s*(\d+)\s*из\s*(\d+).*?(?:получено|есть|имеется)?\s*(\d+)\s*(?:голос|[«"]?за)',q)
        if m2:return FormalIR('POLICY',{'op':'threshold','required':float(m2.group(1)),'observed':float(m2.group(3))},src,'threshold_quorum')
    m=re.search(r'len\(\[([^\]]*)\]\)',q)
    if m:return FormalIR('CODE',{'op':'py_len','n':len([x for x in m.group(1).split(',') if x.strip()])},src,'py_len')
    m=re.search(r'(\d+)\s*%\s*(\d+)',q)
    if m and 'python' in q:return FormalIR('CODE',{'op':'py_mod','a':int(m.group(1)),'b':int(m.group(2))},src,'py_mod')
    m=re.search(r'(\d+)\s*//\s*(\d+)',q)
    if m and 'python' in q:return FormalIR('CODE',{'op':'py_floordiv','a':int(m.group(1)),'b':int(m.group(2))},src,'py_floordiv')
    m=re.search(r'range\((\d+)\s*,\s*(\d+)\s*,\s*(\d+)\)',q)
    if m:return FormalIR('CODE',{'op':'py_range','start':int(m.group(1)),'stop':int(m.group(2)),'step':int(m.group(3))},src,'py_range')
    if 'sql' in q and 'до group by' in q:return FormalIR('CODE',{'op':'sql_where'},src,'sql_where')
    if 'lifo' in q:
        seq=re.search(r'(?:порядку|последовательно)\s*([a-zа-я0-9]+)\s*,\s*([a-zа-я0-9]+)\s*,\s*([a-zа-я0-9]+)',q)
        if seq and ('извлеч' in q or 'выйдет' in q):return FormalIR('CODE',{'op':'lifo_sequence','sequence':list(seq.groups())},src,'lifo_sequence')
        return FormalIR('CODE',{'op':'lifo'},src,'lifo')
    if 'fifo' in q:
        seq=re.search(r'(?:порядку|последовательно)\s*([a-zа-я0-9]+)\s*,\s*([a-zа-я0-9]+)\s*,\s*([a-zа-я0-9]+)',q)
        if seq and ('извлеч' in q or 'выйдет' in q):return FormalIR('CODE',{'op':'fifo_sequence','sequence':list(seq.groups())},src,'fifo_sequence')
        return FormalIR('CODE',{'op':'fifo'},src,'fifo')
    if 'перв' in q and 'python' in q and 'индекс' in q:return FormalIR('CODE',{'op':'zero_index'},src,'zero_index')
    if 'break' in q and 'цикл' in q:return FormalIR('CODE',{'op':'break'},src,'break')
    if 'continue' in q and 'цикл' in q:return FormalIR('CODE',{'op':'continue'},src,'continue')
    if 'bool(0)' in q:return FormalIR('CODE',{'op':'bool_zero'},src,'bool_zero')
    if 'бинарн' in q and 'поиск' in q:return FormalIR('CODE',{'op':'binary_search_complexity'},src,'binary_search')
    if ('просмотр' in q or 'проход' in q) and 'всех n' in q:return FormalIR('CODE',{'op':'linear_scan_complexity'},src,'linear_scan')
    if 'git' in q and 'staged' in q and 'commit' in q:return FormalIR('CODE',{'op':'git_commit'},src,'git_commit')
    if re.search(r'[«"](?:пять|шесть|семь|восемь|девять|десять|одиннадцать|двенадцать|тринадцать|четырнадцать|пятнадцать|шестнадцать|семнадцать|восемнадцать|девятнадцать|двадцать)\s+___[»"]',q) or re.search(r'\b(?:пять|шесть|семь|восемь|девять|десять)\s+___',q): return FormalIR('RUSSIAN',{'op':'numeral_genitive_plural'},src,'ru_numeral_genitive_plural')
    if ('предлог «к»' in q or 'предлог "к"' in q or 'предлог к ' in q) and 'падеж' in q:return FormalIR('RUSSIAN',{'op':'preposition_k_dative'},src,'ru_k_dative')
    if 'благодаря' in q or 'согласно' in q or 'вопреки' in q:
        prep=next((p for p in ['благодаря','согласно','вопреки'] if p in q),None)
        if prep:return FormalIR('RUSSIAN',{'op':'government','governing':prep,'case':'dative'},src,'ru_government')
    if 'в течение' in q:return FormalIR('RUSSIAN',{'op':'v_techenie_genitive'},src,'ru_v_techenie')
    if 'антоним' in q and 'временн' in q:return FormalIR('RUSSIAN',{'op':'antonym_temporary'},src,'ru_antonym')
    if 'принять во внимание' in q:return FormalIR('RUSSIAN',{'op':'idiom_attention'},src,'ru_idiom')
    if 'хотя' in q and ('союз' in q or 'выражает' in q):return FormalIR('RUSSIAN',{'op':'concession'},src,'ru_concession')
    if 'несмотря на' in q:return FormalIR('RUSSIAN',{'op':'concession'},src,'ru_concession')
    if 'потому что' in q and ('отношен' in q or 'выражает' in q):return FormalIR('RUSSIAN',{'op':'cause_conjunction'},src,'ru_cause')
    if ('союз «если»' in q or 'союз "если"' in q) or ('если' in q and 'какое отношение' in q):return FormalIR('RUSSIAN',{'op':'condition_conjunction'},src,'ru_condition')
    if 'ударен' in q:
        for stem in TRUST['russian']['stress_families']:
            if stem in q:return FormalIR('RUSSIAN',{'op':'stress_family','stem':stem},src,'ru_stress_family')
        for w,accent in TRUST['russian']['stress_lexicon'].items():
            if w in q:return FormalIR('RUSSIAN',{'op':'stress_lexicon','word':w,'accent':accent},src,'ru_stress_lexicon')
    if ('нет логического противоречия' in q or 'без логического противоречия' in q) and item.get('options'):return FormalIR('SEMANTIC',{'op':'select_consistent','options':item['options']},src,'semantic_consistency')
    if ('ближайш' in q and 'звезд' in q and 'земл' in q):return FormalIR('FACT',{'op':'nearest_star','excluding_sun':('кроме солнца' in q or 'исключая солнце' in q or 'не считая солнце' in q)},src,'fact_nearest_star')
    if 'химическ' in q and 'символ' in q:
        for en,sy in TRUST['science']['symbols'].items():
            ru={'gold':'золот','iron':'желез','silver':'сереб','oxygen':'кислород','carbon':'углерод','sodium':'натри','potassium':'кали'}[en]
            if ru in q:return FormalIR('FACT',{'op':'chemical_symbol','element':en},src,'fact_symbol')
    if 'http' in q:
        m=re.search(r'\b(200|403|404|500)\b',q)
        if m:return FormalIR('FACT',{'op':'http_status','code':m.group(1)},src,'fact_http')
    if 'least privilege' in q:return FormalIR('FACT',{'op':'computing_principle','key':'least_privilege'},src,'fact_least_privilege')
    if 'raid 1' in q:return FormalIR('FACT',{'op':'computing_principle','key':'raid1'},src,'fact_raid1')
    if 'dns-кэш' in q or 'dns кэш' in q:return FormalIR('FACT',{'op':'computing_principle','key':'dns_cache'},src,'fact_dns_cache')
    if 'tls' in q:return FormalIR('FACT',{'op':'computing_principle','key':'tls'},src,'fact_tls')
    if 'dhcp' in q:return FormalIR('FACT',{'op':'computing_principle','key':'dhcp'},src,'fact_dhcp')
    if 'ssh' in q:return FormalIR('FACT',{'op':'computing_principle','key':'ssh'},src,'fact_ssh')
    if re.search(r'\bapi\b',q):return FormalIR('FACT',{'op':'computing_principle','key':'api'},src,'fact_api')
    return None

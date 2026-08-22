import re, json

def norm(s):return str(s).lower().replace('ё','е').replace('–','-').replace('—','-').strip()
def parse_number(s):
    x=norm(s).replace('%','').replace('°','').replace(',','.')
    try:return float(x)
    except:return None

def match_option(item, conclusion):
    opts=item['options']
    if isinstance(conclusion,(int,float)):
        for k,v in opts.items():
            n=parse_number(v)
            if n is not None and abs(n-float(conclusion))<1e-8:return k
    if isinstance(conclusion,list):
        target='['+', '.join(str(x) for x in conclusion)+']'
        for k,v in opts.items():
            if norm(v).replace(' ','')==norm(target).replace(' ',''):return k
    if isinstance(conclusion,dict):
        if conclusion.get('option_key') in opts:return conclusion['option_key']
        if conclusion.get('case')=='dative':
            scores={}
            for k,v in opts.items():
                w=norm(v); score=0; lemmas=[norm(x) for x in opts.values()]
                if w.endswith(('и','е','у','ю','ам','ям')):score+=0.4
                if any(x.endswith('ь') and w==x[:-1]+'и' for x in lemmas):score+=2.0
                if any(x.endswith('а') and w==x[:-1]+'е' for x in lemmas):score+=2.0
                if any(x.endswith('я') and w==x[:-1]+'е' for x in lemmas):score+=2.0
                if any((not x.endswith(('а','я','ь','о','е'))) and w==x+'у' for x in lemmas):score+=2.0
                if any(x.endswith('о') and w==x[:-1]+'у' for x in lemmas):score+=2.0
                if w.endswith(('ой','ей','ом','ем')):score-=0.5
                scores[k]=score
            if scores and max(scores.values())>0:return max(scores,key=scores.get)
        if conclusion.get('stress')=='ending':
            for k,v in opts.items():
                s=str(v)
                if re.search(r'[ИИЯЯЮЮЕЕЁЁААОУ]т\b',s) or re.search(r'[ИИЯЯЮЮЕЕЁЁААОУ]шь\b',s):return k
    c=norm(conclusion)
    if c=='genitive_plural':
        forms=[norm(v) for v in opts.values()]
        for k,v in opts.items():
            w=norm(v)
            if w.endswith(('ов','ев','ей')):return k
        for lemma in forms:
            if lemma.endswith('а'):
                cand=lemma[:-1]
                for k,v in opts.items():
                    if norm(v)==cand:return k
            if lemma.endswith('я'):
                for cand in [lemma[:-1]+'ь',lemma[:-1]+'й']:
                    for k,v in opts.items():
                        if norm(v)==cand:return k
        return None
    if c in {'r','q','p','a','b','c'}:
        for k,v in opts.items():
            if norm(v)==c:return k
    groups={
      'no':['нет','не является','не дает','не даёт','не произошло','дождь не идет','дождь не идёт','действие запрещено','нельзя'],
      'yes':['да','условие выполнено','кворум достигнут'],
      'negative feedback':['отрицательная обратная связь'], 'positive feedback':['положительная обратная связь'],
      'open loop':['открытый'], 'feedback control':['feedback control','обратная связь'],
      'causality not established due to confounder':['причинность не доказана','конфаундер','нельзя заключить'],
      'check alternative causes and control':['проверить альтернативные причины','контроль альтернативных причин','проверить альтернативные'],
      'formally verified result':['формально проверенный','формально подтвержден','verified proof','проверенным доказательством'],
      'common primary source':['общий первичный источник'],
      'q true':['q истинно'], 'b true':['b истинно'], 'a false':['a ложно'], 'a > c':['a > c'],
      'not p or not q':['не p или не q'], 'not p or q':['не p или q'], 'r':['r'], 'disjoint':['непересекающиеся'],
      'those a that are b are not c':['они не являются c'], 'y did not occur':['y не произошло'], 'no rain':['дождь не идет','дождь не идёт'],
      'where':['where'], 'stack':['стек'], 'queue':['очередь'], 'exit current loop':['выходит из текущего цикла','завершает текущий цикл'],
      'next iteration':['следующей итерации'], 'false':['false'], 'o(log n)':['o(log n)'], 'o(n)':['o(n)'], 'git commit':['git commit'],
      'genitive':['родительный','года','месяца','недели','дня'], 'dative':['дательный'], 'permanent':['постоянн'], 'take into account':['учесть'],
      'concession':['уступк'], 'cause':['причин'], 'condition':['услов'],
      'sun':['солнце'], 'proxima centauri':['проксима центавра'], 'au':['au'], 'fe':['fe'], 'ag':['ag'], 'o':['o'], 'c':['c'], 'na':['na'], 'k':['k'],
      'resource not found':['ресурс не найден','не найден'], 'success':['успеш'], 'forbidden':['запрещ'], 'server error':['ошибка сервера'],
      'minimum necessary permissions':['минимально необходимые права','только минимально необходимые'], 'mirroring':['зеркальн'],
      'cache name resolution':['разрешения имен','разрешения имён'], 'encrypted authenticated channel':['шифрован','аутентификац'],
      'automatic network configuration':['выдает сетевые параметры','выдаёт сетевые параметры'], 'secure remote access':['защищенн','защищённ'],
      'software component interface':['интерфейс взаимодействия']}
    needles=groups.get(c,[c])
    for k,v in opts.items():
        s=norm(v)
        for n in needles:
            nn=norm(n)
            if nn in {'да','нет','r','q','p','a','b','c'}:
                if re.search(r'(?<![а-яa-z0-9])'+re.escape(nn)+r'(?![а-яa-z0-9])',s):return k
            elif nn in s:return k
    if any(ch.isupper() for ch in str(conclusion)):
        for k,v in opts.items():
            if str(v)==str(conclusion):return k
    return None

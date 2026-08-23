import json,os,re,time,urllib.request,hashlib,base64,zlib
from pathlib import Path
MODEL=os.environ['MODEL'];MODEL_ID=os.environ['MODEL_ID'];OUT=Path(os.environ.get('OUT',f'blind33_{MODEL_ID}.json'));BASE='http://127.0.0.1:11434'
EXPECTED='a56318266aa92f4ab1ea18972c791a3ede7408f90f4ca7146b9a3f7955c858cc';here=Path(__file__).parent
packed=''.join((here/f'b33_chunk_{i}.txt').read_text() for i in range(3));raw=zlib.decompress(base64.b85decode(packed.encode()));sha=hashlib.sha256(raw).hexdigest()
if sha!=EXPECTED:raise SystemExit(f'Blind33 hash mismatch {sha}')
bench=json.loads(raw.decode());assert all('answer' not in x and 'gold' not in x for x in bench['items'])
def post(path,obj,timeout=1200):
 data=json.dumps(obj).encode();req=urllib.request.Request(BASE+path,data=data,headers={'Content-Type':'application/json'});return json.loads(urllib.request.urlopen(req,timeout=timeout).read().decode())
def pick(text):
 s=(text or '').strip().upper();m=re.search(r'(?:^|[^A-ZА-Я])([ABCD])(?:$|[^A-ZА-Я])',s);return m.group(1) if m else (s[0] if s and s[0] in 'ABCD' else None)
def option_lp(resp):
 best={x:None for x in 'ABCD'}
 for row in (resp.get('logprobs') or [])[:12]:
  for c in [row]+list(row.get('top_logprobs') or []):
   tok=(c.get('token') or '').strip().upper()
   if tok in best and best[tok] is None:
    try:best[tok]=float(c.get('logprob'))
    except:pass
  if any(v is not None for v in best.values()):break
 return best
try:show=post('/api/show',{'model':MODEL},180)
except Exception as e:show={'error':repr(e)}
system='You are taking a sealed benchmark. Choose exactly one option. Do not explain. Output only one Latin letter: A, B, C, or D.'
rows=[]
for it in bench['items']:
 prompt=it['q']+'\n'+'\n'.join(f'{k}) {v}' for k,v in it['options'].items())+'\nAnswer:'
 body={'model':MODEL,'messages':[{'role':'system','content':system},{'role':'user','content':prompt}],'stream':False,'think':False,'logprobs':True,'top_logprobs':20,'options':{'temperature':0,'seed':33072026,'num_predict':8,'top_p':1.0}}
 t=time.time()
 try:r=post('/api/chat',body);raw_answer=((r.get('message') or {}).get('content') or '');pred=pick(raw_answer);err=None
 except Exception as e:r={};raw_answer='';pred=None;err=repr(e)
 rows.append({'id':it['id'],'blind_index':it['blind_index'],'domain':it['domain'],'category':it['category'],'pred':pred,'raw':raw_answer,'option_logprobs':option_lp(r),'elapsed_wall_s':time.time()-t,'error':err,'ollama_metrics':{k:r.get(k) for k in ['total_duration','load_duration','prompt_eval_count','prompt_eval_duration','eval_count','eval_duration']}})
 print(MODEL,it['id'],pred,flush=True)
summary={'model':MODEL,'model_id':MODEL_ID,'blind33_sha256':sha,'n':len(rows),'valid':sum(x['pred'] in 'ABCD' for x in rows),'contains_gold':False}
OUT.write_text(json.dumps({'summary':summary,'model_show':show,'rows':rows},ensure_ascii=False,indent=2));print(json.dumps(summary,ensure_ascii=False,indent=2))

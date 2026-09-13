from __future__ import annotations
import json, re, sqlite3, threading, time
from pathlib import Path

TOK=re.compile(r"[\w\-]+",re.UNICODE)

class MemoryStore:
    def __init__(self,path:str="var/nexus_memory.db"):
        self.path=path; self.lock=threading.RLock(); Path(path).parent.mkdir(parents=True,exist_ok=True)
        with self._db() as c:
            c.executescript('''
            create table if not exists memory(
              namespace text not null, key text not null, content text not null,
              metadata_json text not null, source text not null, updated_at real not null,
              primary key(namespace,key)
            );
            create index if not exists idx_memory_namespace on memory(namespace);
            ''')
    def _db(self):
        c=sqlite3.connect(self.path,timeout=20); c.row_factory=sqlite3.Row; return c
    def upsert(self,key:str,content:str,namespace:str,metadata:dict|None=None,source:str="unknown"):
        if not key or not namespace or not content: raise ValueError("key, namespace and content are required")
        now=time.time()
        with self.lock,self._db() as c:
            c.execute('''insert into memory(namespace,key,content,metadata_json,source,updated_at)
              values(?,?,?,?,?,?) on conflict(namespace,key) do update set
              content=excluded.content, metadata_json=excluded.metadata_json, source=excluded.source, updated_at=excluded.updated_at''',
              (namespace,key,content,json.dumps(metadata or {},ensure_ascii=False),source,now))
        return {"ok":True,"namespace":namespace,"key":key,"updated_at":now,"execution_authority":"NONE"}
    @staticmethod
    def _tokens(s:str): return {x.lower() for x in TOK.findall(s) if len(x)>1}
    def search(self,query:str,namespaces:list[str]|None=None,limit:int=10):
        q=self._tokens(query); limit=max(1,min(100,int(limit)))
        sql="select * from memory"; args=[]
        if namespaces:
            marks=','.join('?' for _ in namespaces); sql+=f" where namespace in ({marks})"; args.extend(namespaces)
        with self._db() as c: rows=[dict(x) for x in c.execute(sql,args).fetchall()]
        scored=[]
        for r in rows:
            toks=self._tokens(r['key']+' '+r['content']+' '+r['namespace'])
            inter=len(q&toks); union=len(q|toks) or 1
            score=inter/union
            if q and inter==0: continue
            r['metadata']=json.loads(r.pop('metadata_json')); r['score']=round(score,8)
            scored.append(r)
        scored.sort(key=lambda x:(x['score'],x['updated_at']),reverse=True)
        return {"schema":"nexus.memory-search/v1","query":query,"items":scored[:limit],"execution_authority":"NONE"}

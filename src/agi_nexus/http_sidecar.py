from __future__ import annotations
import os
from fastapi import FastAPI,Header,HTTPException
from pydantic import BaseModel,Field
from .memory_sidecar import MemoryStore
from .nexus_core_v2 import status as core_status
from .nexus_service_v3 import handle as runtime_handle, NexusServiceError

store=MemoryStore(os.getenv("NEXUS_MEMORY_DB","var/nexus_memory.db"))
app=FastAPI(title="NEXUS HTTP Sidecar",version="1.0.0a1")

def guard(auth:str|None):
    token=os.getenv("NEXUS_API_TOKEN","")
    if token and auth!=f"Bearer {token}": raise HTTPException(401,"invalid token")

class MemoryUpsert(BaseModel):
    key:str; content:str; namespace:str; metadata:dict=Field(default_factory=dict); source:str="unknown"
class MemorySearch(BaseModel):
    query:str; namespaces:list[str]=Field(default_factory=list); limit:int=10

@app.get('/health')
def health():
    st=core_status()
    return {"ok":True,"service":"agi_nexus_http_sidecar","core":st,"memory":"READY","execution_authority":"NONE"}

@app.post('/v1/runtime')
def runtime(body:dict,authorization:str|None=Header(default=None)):
    guard(authorization)
    try:return runtime_handle(body)
    except NexusServiceError as e: raise HTTPException(422,str(e))

@app.post('/v1/memory/upsert')
def memory_upsert(body:MemoryUpsert,authorization:str|None=Header(default=None)):
    guard(authorization)
    try:return store.upsert(body.key,body.content,body.namespace,body.metadata,body.source)
    except ValueError as e:raise HTTPException(422,str(e))

@app.post('/v1/memory/search')
def memory_search(body:MemorySearch,authorization:str|None=Header(default=None)):
    guard(authorization); return store.search(body.query,body.namespaces,body.limit)

from __future__ import annotations
import torch
from torch import nn
import torch.nn.functional as F
from .smallworld import FastSmallWorldBlock

class ARCGraphRanker(nn.Module):
    def __init__(self,input_dim=556,hidden=48,slots=8,layers=3):
        super().__init__();self.input_dim=input_dim;self.hidden=hidden;self.slots=slots
        self.adapter=nn.Sequential(nn.LayerNorm(input_dim),nn.Linear(input_dim,slots*hidden),nn.GELU());self.slot_pos=nn.Parameter(torch.randn(slots,hidden)*.02)
        self.slot_blocks=nn.ModuleList([FastSmallWorldBlock(hidden,slots,seed=f'V18-ARC-SLOT-{i}') for i in range(layers)]);self.candidate_blocks=nn.ModuleList([FastSmallWorldBlock(hidden,16,seed=f'V18-ARC-CAND-{i}') for i in range(2)])
        self.teacher_gate=nn.Sequential(nn.Linear(hidden,64),nn.GELU(),nn.Linear(64,1));self.score=nn.Sequential(nn.LayerNorm(hidden),nn.Linear(hidden,72),nn.GELU(),nn.Dropout(.04),nn.Linear(72,1))
    def encode_candidates(self,x):
        shape=x.shape[:-1];h=self.adapter(x.reshape(-1,x.shape[-1])).view(-1,self.slots,self.hidden)+self.slot_pos
        for b in self.slot_blocks:h=b(h)
        return h.mean(1).view(*shape,self.hidden)
    def score_encoded(self,h,mask):
        for b in self.candidate_blocks:h=b(h,mask)
        return self.score(h).squeeze(-1).masked_fill(~mask,-1e4),self.teacher_gate(h).squeeze(-1).masked_fill(~mask,-1e4)
    def forward(self,x,mask):return self.score_encoded(self.encode_candidates(x),mask)

class RussianSmallWorldReasoner(nn.Module):
    def __init__(self,vocab=56,emb=32,hidden=64,slots=16,max_len=256,rule_classes=8):
        super().__init__();self.slots=slots;self.max_len=max_len;self.embedding=nn.Embedding(vocab,emb,padding_idx=0);self.char_proj=nn.Linear(emb,hidden);self.pos=nn.Parameter(torch.randn(slots,hidden)*.02)
        self.blocks=nn.ModuleList([FastSmallWorldBlock(hidden,slots,seed=f'V18-RU-{i}') for i in range(3)]);self.head=nn.Sequential(nn.LayerNorm(hidden),nn.Linear(hidden,128),nn.GELU());self.quality=nn.Linear(128,4);self.rule=nn.Linear(128,rule_classes);self.depth=nn.Linear(128,1);self.validity=nn.Linear(128,1)
    def forward(self,tokens):
        B,L=tokens.shape;e=self.embedding(tokens);chunk=(L+self.slots-1)//self.slots;pad=chunk*self.slots-L
        if pad:e=F.pad(e,(0,0,0,pad));tokens=F.pad(tokens,(0,pad))
        e=e.view(B,self.slots,chunk,-1);m=tokens.view(B,self.slots,chunk).ne(0).float();slot=(e*m.unsqueeze(-1)).sum(2)/m.sum(2,keepdim=True).clamp_min(1);h=self.char_proj(slot)+self.pos
        for b in self.blocks:h=b(h)
        pooled=h.mean(1);z=self.head(pooled);return {'quality_logits':self.quality(z),'rule_logits':self.rule(z),'depth':self.depth(z).squeeze(-1),'validity_logit':self.validity(z).squeeze(-1),'state':pooled}

class SmallWorldDynamics(nn.Module):
    def __init__(self,state_dim=256,hidden=64,slots=16,actions=30):
        super().__init__();self.slots=slots;self.chunk=state_dim//slots;self.state_proj=nn.Linear(self.chunk,hidden);self.action=nn.Embedding(actions,hidden);self.pos=nn.Parameter(torch.randn(slots,hidden)*.02);self.blocks=nn.ModuleList([FastSmallWorldBlock(hidden,slots,seed=f'V18-WORLD-{i}') for i in range(3)]);self.next=nn.Linear(hidden,self.chunk);self.progress=nn.Linear(hidden,1);self.terminal=nn.Linear(hidden,1);self.uncertainty=nn.Linear(hidden,1);self.inverse=nn.Linear(hidden,actions)
    def forward(self,state,action):
        B=state.shape[0];h=self.state_proj(state.view(B,self.slots,self.chunk))+self.pos+self.action(action)[:,None,:]
        for b in self.blocks:h=b(h)
        next_state=self.next(h).reshape(B,-1);p=h.mean(1);return {'next_state':next_state,'progress':self.progress(p).squeeze(-1),'terminal_logit':self.terminal(p).squeeze(-1),'uncertainty':F.softplus(self.uncertainty(p).squeeze(-1)),'inverse_logits':self.inverse(p)}

class NexusV18Unified(nn.Module):
    def __init__(self,arc_input_dim=556,language_vocab=56):
        super().__init__();self.arc=ARCGraphRanker(arc_input_dim);self.language=RussianSmallWorldReasoner(language_vocab);self.world=SmallWorldDynamics()
    def parameter_report(self):
        report={n:sum(p.numel() for p in m.parameters()) for n,m in [('arc',self.arc),('language',self.language),('world',self.world)]};report['total']=sum(p.numel() for p in self.parameters());return report

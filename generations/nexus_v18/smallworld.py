from __future__ import annotations
import hashlib, math
import torch
from torch import nn
import torch.nn.functional as F


def deterministic_small_world(nodes:int, local_degree:int=4, shortcuts:int|None=None, seed:str='NEXUS-V18') -> torch.Tensor:
    if nodes <= 1:
        return torch.ones(nodes, nodes)
    local_degree=min(local_degree, nodes-1)
    if local_degree%2: local_degree-=1
    local_degree=max(2 if nodes>2 else nodes-1, local_degree)
    A=torch.eye(nodes,dtype=torch.float32)
    r=max(1,local_degree//2)
    for i in range(nodes):
        for d in range(1,r+1):
            j=(i+d)%nodes; A[i,j]=A[j,i]=1
    candidates=[]
    for i in range(nodes):
        for j in range(i+1,nodes):
            if A[i,j]==0:
                h=hashlib.sha256(f'{seed}:{nodes}:{i}:{j}'.encode()).digest()
                candidates.append((h,i,j))
    if shortcuts is None: shortcuts=max(1,nodes//4)
    for _,i,j in sorted(candidates)[:min(shortcuts,len(candidates))]: A[i,j]=A[j,i]=1
    return A


def metropolis(A:torch.Tensor) -> torch.Tensor:
    A=(A>0).float(); deg=A.sum(-1)-1
    P=torch.zeros_like(A)
    n=A.shape[-1]
    for i in range(n):
        for j in range(n):
            if i!=j and A[i,j]>0: P[i,j]=1/(1+torch.maximum(deg[i],deg[j]))
        P[i,i]=1-P[i].sum()
    return P

class SmallWorldBlock(nn.Module):
    """Attention constrained by deterministic small-world support plus P/P²/P⁴ diffusion."""
    def __init__(self, hidden:int, nodes:int=16, heads:int=4, dropout:float=.05, seed:str='NEXUS-V18'):
        super().__init__(); self.hidden=hidden; self.nodes=nodes; self.heads=heads
        self.norm1=nn.LayerNorm(hidden); self.norm2=nn.LayerNorm(hidden)
        self.qkv=nn.Linear(hidden,hidden*3); self.out=nn.Linear(hidden,hidden)
        self.ff=nn.Sequential(nn.Linear(hidden,hidden*3),nn.GELU(),nn.Dropout(dropout),nn.Linear(hidden*3,hidden))
        A=deterministic_small_world(nodes,4,max(1,nodes//4),seed); self.register_buffer('support',A,persistent=True)
        self.register_buffer('P',metropolis(A),persistent=True); self.dropout=nn.Dropout(dropout)
    def forward(self,x:torch.Tensor, mask:torch.Tensor|None=None):
        B,N,H=x.shape; z=self.norm1(x); qkv=self.qkv(z).view(B,N,3,self.heads,H//self.heads).permute(2,0,3,1,4);q,k,v=qkv
        logits=q@k.transpose(-1,-2)/math.sqrt(H//self.heads)
        A=self.support[:N,:N].to(x.device)
        if N != self.nodes:
            A=deterministic_small_world(N,min(4,max(2,N-1)),max(1,N//4),f'dynamic-{self.nodes}').to(x.device)
        support=A.bool().view(1,1,N,N)
        if mask is not None:
            valid=mask[:,None,:,None]&mask[:,None,None,:]; support=support&valid
        logits=logits.masked_fill(~support,-1e4); att=torch.softmax(logits,-1); att=self.dropout(att)
        h=(att@v).transpose(1,2).reshape(B,N,H)
        P=metropolis(A).to(x.device,x.dtype)
        if mask is not None:
            P=P.unsqueeze(0).expand(B,-1,-1).clone(); valid=mask.float();P=P*valid[:,None,:];den=P.sum(-1,keepdim=True).clamp_min(1e-6);P=P/den
            d1=P@z;d2=P@d1;d4=P@(P@d2)
        else:
            d1=torch.einsum('ij,bjh->bih',P,z);d2=torch.einsum('ij,bjh->bih',P,d1);d4=torch.einsum('ij,bjh->bih',P,torch.einsum('ij,bjh->bih',P,d2))
        y=x+self.dropout(self.out(.55*h+.25*d1+.13*d2+.07*d4)); y=y+self.dropout(self.ff(self.norm2(y)))
        if mask is not None:y=y*mask.unsqueeze(-1)
        return y

class FastSmallWorldBlock(nn.Module):
    """Linear-time spectral small-world brick: learned mixing of P, P² and P⁴ channels."""
    def __init__(self,hidden:int,nodes:int=8,dropout:float=.03,seed:str='NEXUS-V18-FAST'):
        super().__init__();self.hidden=hidden;self.nodes=nodes
        A=deterministic_small_world(nodes,min(4,max(2,nodes-1)),max(1,nodes//4),seed)
        self.register_buffer('P',metropolis(A),persistent=True)
        self.norm=nn.LayerNorm(hidden);self.mix=nn.Linear(hidden*4,hidden);self.gate=nn.Linear(hidden*2,hidden)
        self.ffnorm=nn.LayerNorm(hidden);self.ff=nn.Sequential(nn.Linear(hidden,hidden*2),nn.GELU(),nn.Linear(hidden*2,hidden));self.drop=nn.Dropout(dropout)
    def forward(self,x:torch.Tensor,mask:torch.Tensor|None=None):
        B,N,H=x.shape;z=self.norm(x)
        if N==self.nodes:P=self.P.to(x.device,x.dtype)
        else:P=metropolis(deterministic_small_world(N,min(4,max(2,N-1)),max(1,N//4),f'fast-{self.nodes}-{N}')).to(x.device,x.dtype)
        if mask is None:
            p1=torch.einsum('ij,bjh->bih',P,z);p2=torch.einsum('ij,bjh->bih',P,p1);p4=torch.einsum('ij,bjh->bih',P,torch.einsum('ij,bjh->bih',P,p2))
        else:
            Pb=P.unsqueeze(0).expand(B,-1,-1)*mask[:,None,:].to(x.dtype);Pb=Pb/Pb.sum(-1,keepdim=True).clamp_min(1e-6)
            p1=Pb@z;p2=Pb@p1;p4=Pb@(Pb@p2)
        m=self.mix(torch.cat([z,p1,p2,p4],-1));g=torch.sigmoid(self.gate(torch.cat([z,m],-1)));y=x+self.drop(g*m);y=y+self.drop(self.ff(self.ffnorm(y)))
        return y if mask is None else y*mask.unsqueeze(-1)

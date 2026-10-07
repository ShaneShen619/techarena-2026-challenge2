"""Small causal TCN for native P1 charge fragments and capacity residual heads."""
from __future__ import annotations
import torch
from torch import nn

class CausalConv(nn.Module):
    def __init__(self,inp,out,kernel=3):
        super().__init__();self.conv=nn.Conv1d(inp,out,kernel,padding=kernel-1)
    def forward(self,x):return self.conv(x)[:,:,:x.shape[-1]]

class ChargeEncoder(nn.Module):
    def __init__(self,width=16):
        super().__init__()
        self.conv1=CausalConv(5,width);self.conv2=CausalConv(width,width)
        self.next_voltage=nn.Conv1d(width,1,1)
    def forward(self,seq):
        # seq: [event,time,channel], left-padded native samples.
        h=seq.transpose(1,2)
        h=torch.relu(self.conv1(h));h=torch.relu(self.conv2(h))
        mask=seq[:,:,4].unsqueeze(1)
        emb=(h*mask).sum(-1)/mask.sum(-1).clamp(min=1)
        return emb,self.next_voltage(h).squeeze(1)

class CapacityResidualNet(nn.Module):
    def __init__(self,encoder:ChargeEncoder,meta_dim=8,width=16):
        super().__init__();self.encoder=encoder
        self.head=nn.Sequential(nn.Linear(meta_dim+3*width,32),nn.ReLU(),
                                nn.Linear(32,16),nn.ReLU(),nn.Linear(16,1))
    def forward(self,all_events,slots,meta):
        # Slot 0 current, 1:11 first ten, 11:16 recent five. -1 padding.
        B=slots.shape[0]
        flat=slots.reshape(-1)
        safe=flat.clamp(min=0)
        unique,inverse=torch.unique(safe,return_inverse=True)
        emb,_=self.encoder(all_events[unique])
        emb=emb[inverse].view(B,16,-1)
        mask=(slots>=0).to(emb.dtype)
        cur=emb[:,0]
        first=(emb[:,1:11]*mask[:,1:11,None]).sum(1)/mask[:,1:11].sum(1,keepdim=True).clamp(min=1)
        recent=(emb[:,11:16]*mask[:,11:16,None]).sum(1)/mask[:,11:16].sum(1,keepdim=True).clamp(min=1)
        raw=self.head(torch.cat([meta,cur,first,recent],dim=1)).squeeze(1)
        return 10*torch.tanh(raw)  # bounded additive SOH-pp correction

def next_voltage_loss(encoder,seq):
    _,forecast=encoder(seq)
    valid=seq[:,:,4]
    pair=valid[:,:-1]*valid[:,1:]
    target=(seq[:,1:,0]-seq[:,:-1,0])*100  # normalized V -> mV
    error=(forecast[:,:-1]-target)*pair
    return (error**2).sum()/pair.sum().clamp(min=1)

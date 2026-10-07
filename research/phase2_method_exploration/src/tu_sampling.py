"""Bounded-memory stratified contiguous block sampler for TU CSV files."""
from __future__ import annotations
import io
from pathlib import Path
import pandas as pd

def sampled_blocks(path:Path,fractions,rows_per_block,*,usecols=None):
    size=path.stat().st_size
    with path.open('rb') as f:
        header=f.readline()
        for block_id,fraction in enumerate(fractions):
            offset=int(size*fraction)
            if offset==0:f.seek(len(header))
            else:
                f.seek(offset);f.readline()  # discard incomplete line
            actual_start=f.tell();lines=[]
            for _ in range(rows_per_block):
                line=f.readline()
                if not line:break
                lines.append(line)
            if not lines:continue
            data=pd.read_csv(io.BytesIO(header+b''.join(lines)),usecols=usecols)
            yield block_id,actual_start,data

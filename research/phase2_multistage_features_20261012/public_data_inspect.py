from pathlib import Path
import io,requests,zipfile,json
TASK=Path(__file__).resolve().parent
class Remote(io.RawIOBase):
 def __init__(self,url,size):self.url=url;self.size=size;self.pos=0;self.received=0;self.cache={}
 def seekable(self):return True
 def readable(self):return True
 def tell(self):return self.pos
 def seek(self,offset,whence=0):
  self.pos=offset if whence==0 else self.pos+offset if whence==1 else self.size+offset
  return self.pos
 def read(self,n=-1):
  if n<0:n=self.size-self.pos
  n=min(n,self.size-self.pos)
  if n<=0:return b''
  key=(self.pos,n)
  if key not in self.cache:
   parts=[]
   for begin in range(self.pos,self.pos+n,1048576):
    end=min(self.pos+n,begin+1048576)-1
    for attempt in range(3):
     url=self.url
     try:r=requests.get(url,headers={'Range':f'bytes={begin}-{end}'},timeout=30)
     except requests.RequestException:
      if attempt==2:raise
      continue
     if r.status_code==206 and len(r.content)==end-begin+1 and r.headers.get('Content-Range','').startswith(f'bytes {begin}-{end}/'):break
    if not (r.status_code==206 and len(r.content)==end-begin+1 and r.headers.get('Content-Range','').startswith(f'bytes {begin}-{end}/')):raise RuntimeError(f'Range denied {r.status_code}')
    parts.append(r.content)
   data=b''.join(parts);self.received+=len(data);self.cache[key]=data
  data=self.cache[key];self.pos+=len(data);return data

def main():
 allrows=[]
 for record in ['14597394','6405084']:
  d=json.loads((TASK/'public_data'/f'zenodo_{record}.json').read_text())
  for f in d['files']:
   stream=Remote(f['links']['self'],f['size']);z=zipfile.ZipFile(stream)
   rows=[dict(record=record,archive=f['key'],name=i.filename,bytes=i.file_size,compressed_bytes=i.compress_size,header_offset=i.header_offset) for i in z.infolist()]
   allrows+=rows
   print(record,f['key'],'members',len(rows),'index network bytes',stream.received,flush=True)
   selected=[r for r in rows if 'data_for_ml' in r['name'] or r['name'].endswith(('.csv','.xlsx','.json','.parquet'))]
   print(selected[:20],flush=True)
 (TASK/'public_data/archive_inventory.json').write_text(json.dumps(allrows,indent=2))
if __name__=='__main__':main()

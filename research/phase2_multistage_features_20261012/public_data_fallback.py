"""Check alternative small supervised sources without downloading entire archives."""
import requests,json,concurrent.futures
from pathlib import Path
T=Path(__file__).parent
jobs=[('gasper_tree','https://api.github.com/repos/NatLabRockies/battery_pulse_diagnostics/git/trees/main?recursive=1'),('zhu_tree','https://api.github.com/repos/Yixiu-Wang/data-driven-capacity-estimation-from-voltage-relaxation/git/trees/main?recursive=1')]
d=json.loads((T/'public_data/zenodo_6405084.json').read_text());m=next(x for x in d['files'] if x['key']=='Dataset_1_NCA_battery.zip');r=next(x for x in json.loads((T/'public_data/selection_before_download.json').read_text()) if x['record']=='6405084');a=r['header_offset'];jobs+=[('zhu_range',m['links']['self'])]
def get(job):
 name,u=job
 try:
  x=requests.get(u,headers={'Range':f'bytes={a}-{a+65535}'} if name=='zhu_range' else {},timeout=20)
  print(name,x.status_code,len(x.content),x.headers.get('Content-Range'),flush=True)
  if name.endswith('tree') and x.status_code==200:(T/'public_data'/f'{name}.json').write_text(x.text)
  if name=='zhu_range' and x.status_code==206:(T/'public_data/zhu_selected_range.bin').write_bytes(x.content)
 except Exception as e:print(name,type(e).__name__,flush=True)
with concurrent.futures.ThreadPoolExecutor(3) as ex:list(ex.map(get,jobs))

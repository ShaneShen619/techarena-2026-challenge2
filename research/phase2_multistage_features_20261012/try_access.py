import requests,json,concurrent.futures
from pathlib import Path
T=Path(__file__).parent
r=next(x for x in json.loads((T/'public_data/archive_inventory.json').read_text()) if x['name'].endswith('targets_soh.csv'))
a=r['header_offset'];b=a+16383
urls=['https://zenodo.org/api/records/14597394/files/battery_pulse_diagnostics.zip/content','https://zenodo.org/records/14597394/files/battery_pulse_diagnostics.zip?download=1','https://zenodo.org/records/14597394/files/battery_pulse_diagnostics.zip']
def get(u):
 try:
  x=requests.get(u,headers={'Range':f'bytes={a}-{b}'},timeout=18);print(u,x.status_code,len(x.content),x.headers.get('Content-Range'),x.content[:8].hex(),flush=True)
  if x.status_code==206 and x.content[:4]==b'PK\x03\x04':(T/'public_data/targets_selected_range.bin').write_bytes(x.content)
 except Exception as e:print(u,type(e).__name__,flush=True)
with concurrent.futures.ThreadPoolExecutor(3) as ex:list(ex.map(get,urls))

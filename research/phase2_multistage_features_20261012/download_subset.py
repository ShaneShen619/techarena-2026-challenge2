"""Only ZIP index + selected compressed members, with CRC and SHA verification."""
from public_data_inspect import Remote,TASK
import json,zipfile,hashlib,requests,struct,zlib,re

def main():
 inventory=json.loads((TASK/'public_data/archive_inventory.json').read_text());chosen=[]
 chosen += [r for r in inventory if r['record']=='14597394' and r['name'].endswith(('targets_soh.csv','features_pulse_hppc.csv','features_pulse_rapid.csv'))]
 # Prespecified small, metadata-stratified subset: two cells per NCA condition.
 nca=[r for r in inventory if r['archive']=='Dataset_1_NCA_battery.zip' and r['name'].endswith('.csv')]
 for condition in sorted({r['name'].split('/')[-1].split('-#')[0] for r in nca}):
  files=sorted([r for r in nca if r['name'].split('/')[-1].split('-#')[0]==condition],key=lambda r:int(re.search(r'#(\d+)',r['name']).group(1)))
  chosen+=files[:2]
 (TASK/'public_data/selection_before_download.json').write_text(json.dumps(chosen,indent=2))
 manifest=[]
 for row in chosen:
  name=row['name'].split('/')[-1];dest=TASK/'public_data'/name
  if not dest.exists():
   d=json.loads((TASK/'public_data'/f"zenodo_{row['record']}.json").read_text());meta=next(f for f in d['files'] if f['key']==row['archive'])
   stream=Remote(meta['links']['self'],meta['size']);stream.seek(row['header_offset']);header=stream.read(30)
   fields=struct.unpack('<4s5H3I2H',header);namelen,extra=fields[-2:];method=fields[3];crc=json.loads((TASK/'public_data'/f"{row['archive']}.crc.json").read_text())[row['name']]
   stream.seek(row['header_offset']+30+namelen+extra);compressed=stream.read(row['compressed_bytes'])
   content=zlib.decompress(compressed,-15) if method==8 else compressed
   if len(content)!=row['bytes'] or zlib.crc32(content)!=crc:raise RuntimeError('CRC/size mismatch '+name)
   dest.write_bytes(content)
  manifest.append({**row,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'local':str(dest),'license':'CC BY 4.0','download_scope':'selected ZIP member only'})
  print('downloaded',name,dest.stat().st_size,flush=True)
  (TASK/'public_data/download_manifest.json').write_text(json.dumps(manifest,indent=2))
 print('selected compressed bytes',sum(r['compressed_bytes'] for r in chosen),flush=True)
if __name__=='__main__':main()

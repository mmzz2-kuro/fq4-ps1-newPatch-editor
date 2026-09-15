from pathlib import Path
import hashlib, json, re

ROOT=Path(r'F:/workspace-server/fq4')
OUT=ROOT/'docs/fq4/analysis/034'
OUT.mkdir(parents=True, exist_ok=True)
SECTOR=2352

images={
 'original': ROOT/'original/First Queen IV - Varcia Senki (Japan).bin',
 'patched_241112': ROOT/'patched/First Queen IV - Varcia Senki (kor).bin',
 'korean_patch_patched': ROOT/'korean-patch/First Queen IV - Varcia Senki (Japan)-patched.bin',
 'my_250826': ROOT/'my-patch/make-patch/fq4-kor-250826.bin',
 'my_250826_v2': ROOT/'my-patch/make-patch/fq4-kor-250826-v2.bin',
 'my_250826_ecc_notecc': ROOT/'my-patch/make-patch/fq4-250826-patch-notecc.bin',
 'my_race': ROOT/'my-patch/make-patch/fq4-race.bin',
}
images={k:v for k,v in images.items() if v.exists()}

def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for chunk in iter(lambda:f.read(1024*1024),b''):
   h.update(chunk)
 return h.hexdigest()

def ranges(nums):
 if not nums: return []
 nums=sorted(nums); out=[]; s=e=nums[0]
 for n in nums[1:]:
  if n==e+1: e=n
  else: out.append([s,e,e-s+1]); s=e=n
 out.append([s,e,e-s+1])
 return out

info={}
for name,p in images.items():
 st=p.stat()
 cue=p.with_suffix('.cue')
 info[name]={'path':str(p.relative_to(ROOT)).replace('\\','/'),'size':st.st_size,'sectors':st.st_size//SECTOR,'mod2352':st.st_size%SECTOR,'sha256':sha(p)}
 if cue.exists(): info[name]['cue']=cue.read_text(errors='replace').strip()

base=images['original'].read_bytes()
comparisons={}
for name,p in images.items():
 if name=='original': continue
 b=p.read_bytes()
 changed=[]; data_changed=[]; header_changed=[]; subheader_changed=[]; ecc_changed=[]
 for i in range(min(len(base),len(b))//SECTOR):
  asec=base[i*SECTOR:(i+1)*SECTOR]; bsec=b[i*SECTOR:(i+1)*SECTOR]
  if asec!=bsec:
   changed.append(i)
   if asec[24:2072]!=bsec[24:2072]: data_changed.append(i)
   if asec[:16]!=bsec[:16]: header_changed.append(i)
   if asec[16:24]!=bsec[16:24]: subheader_changed.append(i)
   if asec[2072:]!=bsec[2072:]: ecc_changed.append(i)
 comparisons[name]={
  'changed_sector_count':len(changed),
  'changed_sector_ranges_first80':ranges(changed)[:80],
  'data_changed_count':len(data_changed),
  'data_changed_ranges_first80':ranges(data_changed)[:80],
  'header_changed_count':len(header_changed),
  'subheader_changed_count':len(subheader_changed),
  'ecc_edc_changed_count':len(ecc_changed),
 }

result={'sector_size':SECTOR,'images':info,'comparisons_to_original':comparisons}
(OUT/'image-diff-summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:{'changed':v['changed_sector_count'],'data':v['data_changed_count'],'ecc':v['ecc_edc_changed_count'],'ranges':v['data_changed_ranges_first80'][:12]} for k,v in comparisons.items()},ensure_ascii=False,indent=2))

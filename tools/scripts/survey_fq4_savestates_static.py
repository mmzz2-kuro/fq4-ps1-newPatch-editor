from pathlib import Path
import json, re, hashlib
ROOT=Path(r'F:/workspace-server/fq4')
OUT=ROOT/'docs/fq4/analysis/034'
OUT.mkdir(parents=True,exist_ok=True)
MAGIC=bytes.fromhex('28b52ffd')
rows=[]
for p in sorted((ROOT/'savestates').rglob('*')):
    if not p.is_file(): continue
    b=p.read_bytes()
    ascii_strings=[]
    for m in re.finditer(rb'[ -~]{4,}', b):
        s=m.group().decode('ascii','replace')
        if any(t in s.upper() for t in ['SLPS','FIRST','QUEEN','CD','MOV','STR','STATE','BIOS']):
            ascii_strings.append({'off':m.start(),'text':s[:200]})
    offs=[]; pos=-1
    while True:
        pos=b.find(MAGIC,pos+1)
        if pos<0: break
        offs.append(pos)
        if len(offs)>=20: break
    rows.append({'file':str(p.relative_to(ROOT)).replace('\\','/'),'size':len(b),'sha256':hashlib.sha256(b).hexdigest(),'zstd_offsets':offs,'ascii_hits':ascii_strings[:80]})
(OUT/'savestate-static-survey.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(rows,ensure_ascii=False,indent=2)[:8000])

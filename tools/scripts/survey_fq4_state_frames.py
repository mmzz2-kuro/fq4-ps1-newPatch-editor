from pathlib import Path
import json, re, hashlib
ROOT=Path(r'F:/workspace-server/fq4')
OUT=ROOT/'docs/fq4/analysis/034'
frames=[ROOT/'work/fq4/034/state1/frame-01.bin', ROOT/'work/fq4/034/state-resume/frame-01.bin']
needles=[b'PS-X EXE', b'SLPS_006.04', b'MOV03', b'MOV04', b'FIRST', b'QUEEN', b'SC\x13\x04']
rows=[]
for p in frames:
    b=p.read_bytes()
    hits={}
    for n in needles:
        offs=[]; pos=-1
        while True:
            pos=b.find(n,pos+1)
            if pos<0: break
            offs.append(pos)
            if len(offs)>=30: break
        hits[n.hex() if any(c<32 or c>126 for c in n) else n.decode('ascii')]=offs
    # find embedded main exe by sha-ish: compare longest exact windows? just locate known MIPS opcode sequences from original at chunks
    ascii_hits=[]
    for m in re.finditer(rb'[ -~]{6,}', b):
        s=m.group().decode('ascii','replace')
        if any(t in s.upper() for t in ['SLPS','MOV','STR','FIRST','QUEEN','CDROM','ENDING','TITLE']):
            ascii_hits.append({'off':m.start(),'text':s[:160]})
    rows.append({'file':str(p.relative_to(ROOT)).replace('\\','/'),'size':len(b),'sha256':hashlib.sha256(b).hexdigest(),'needle_hits':hits,'ascii_hits':ascii_hits[:120]})
(OUT/'state-frame-survey.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(rows,ensure_ascii=False,indent=2)[:10000])

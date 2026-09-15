from pathlib import Path
import json, hashlib
RAW=2352
MOV04_START=18430
MOV04_END=22652
paths={
 'original':Path('original/First Queen IV - Varcia Senki (Japan).bin'),
 'patched241112':Path('patched/First Queen IV - Varcia Senki (kor).bin'),
 'mypatch250826':Path('my-patch/make-patch/fq4-kor-250826.bin'),
 'current_out':Path('out/fq4-kor-250826-endingfix-extendclass.bin'),
}
out={'range':[MOV04_START,MOV04_END],'sector_count':MOV04_END-MOV04_START+1,'images':{},'comparisons':{}}
for name,p in paths.items():
    if not p.exists():
        continue
    b=p.read_bytes()
    sectors=[]
    for lba in list(range(MOV04_START,MOV04_START+8))+list(range(MOV04_END-15,MOV04_END+1)):
        s=b[lba*RAW:(lba+1)*RAW]
        sectors.append({
            'lba':lba,
            'mode':s[15] if len(s)>16 else None,
            'subheader':s[16:24].hex(' '),
            'data_sha1':hashlib.sha1(s[24:24+2048]).hexdigest(),
            'tail32':s[-32:].hex(' '),
            'data_head32':s[24:56].hex(' '),
        })
    out['images'][name]={'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'sample_sectors':sectors}
for a in paths:
    if not paths[a].exists(): continue
    ba=paths[a].read_bytes()
    for bname in paths:
        if a>=bname or not paths[bname].exists(): continue
        bb=paths[bname].read_bytes()
        diffs=[]; same=0
        for lba in range(MOV04_START,MOV04_END+1):
            if ba[lba*RAW:(lba+1)*RAW]==bb[lba*RAW:(lba+1)*RAW]: same+=1
            else: diffs.append(lba)
        ranges=[]
        if diffs:
            st=prev=diffs[0]
            for x in diffs[1:]:
                if x==prev+1: prev=x
                else: ranges.append([st,prev]); st=prev=x
            ranges.append([st,prev])
        out['comparisons'][f'{a}_vs_{bname}']={'same_sectors':same,'diff_sector_count':len(diffs),'diff_ranges':ranges[:20]}
Path('docs/fq4/analysis/037').mkdir(parents=True,exist_ok=True)
Path('docs/fq4/analysis/037/mov04-sector-comparison.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in out['comparisons'].items()},ensure_ascii=False,indent=2))

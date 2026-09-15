#!/usr/bin/env python3
from __future__ import annotations
import json, shutil, sys, hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tools'/'scripts'))
from repair_cdrom_xa_ecc import repair_image
from verify_cdrom_xa_ecc import audit_range
RAW=2352
MOV04_START=18430
MOV04_END=22652
BASE=ROOT/'out'/'fq4-kor-250826-endingfix-extendclass.bin'
KOR_MOV04=ROOT/'my-patch'/'make-patch'/'fq4-kor-250826.bin'
ORIG=ROOT/'original'/'First Queen IV - Varcia Senki (Japan).bin'
OUTDIR=ROOT/'work'/'fq4'/'037'

def sha(p:Path):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()

def write_cue(bin_path:Path):
    cue=bin_path.with_suffix('.cue')
    cue.write_text(f'FILE "{bin_path.name}" BINARY\n  TRACK 01 MODE2/2352\n    INDEX 01 00:00:00\n',encoding='ascii')
    return cue

def copy_sector_range(dst:Path, src:Path, start:int, end:int):
    with dst.open('r+b') as d, src.open('rb') as s:
        for lba in range(start,end+1):
            s.seek(lba*RAW); data=s.read(RAW)
            d.seek(lba*RAW); d.write(data)

def build_variant(name:str, ranges:list[tuple[Path,int,int]]):
    OUTDIR.mkdir(parents=True,exist_ok=True)
    out=OUTDIR/f'{name}.bin'
    shutil.copy2(BASE,out)
    for src,start,end in ranges:
        copy_sector_range(out,src,start,end)
    before=sha(out)
    repair=repair_image(out,workers=1)
    audit=audit_range((str(out),0,out.stat().st_size//RAW))
    fail={k:len(v) for k,v in audit['failures'].items()}
    cue=write_cue(out)
    return {'name':name,'bin':str(out.relative_to(ROOT)),'cue':str(cue.relative_to(ROOT)),'sha_before_repair':before,'sha256':sha(out),'repair':{k:v for k,v in repair.items() if k!='repaired_lbas'},'failure_counts':fail,'ranges':[[str(src.relative_to(ROOT)),start,end] for src,start,end in ranges]}

def main():
    variants=[]
    tails=[7,64,256,512]
    variants.append(build_variant('fq4-037-korean-mov04-full',[(KOR_MOV04,MOV04_START,MOV04_END)]))
    for tail in tails:
        kor_end=MOV04_END-tail
        orig_start=MOV04_END-tail+1
        variants.append(build_variant(f'fq4-037-korean-mov04-original-tail{tail}',[(KOR_MOV04,MOV04_START,kor_end),(ORIG,orig_start,MOV04_END)]))
    report={'base':str(BASE.relative_to(ROOT)),'korean_mov04_source':str(KOR_MOV04.relative_to(ROOT)),'original_source':str(ORIG.relative_to(ROOT)),'mov04_lba':[MOV04_START,MOV04_END],'variants':variants}
    (ROOT/'docs'/'fq4'/'analysis'/'037').mkdir(parents=True,exist_ok=True)
    (ROOT/'docs'/'fq4'/'analysis'/'037'/'korean-mov04-variants.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__': main()


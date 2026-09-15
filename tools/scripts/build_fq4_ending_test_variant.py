from pathlib import Path
import json, hashlib, shutil, subprocess, sys
ROOT=Path(r'F:/workspace-server/fq4')
OUT=ROOT/'docs/fq4/analysis/034'
WORK=ROOT/'work/fq4/034'
WORK.mkdir(parents=True,exist_ok=True)
SE=2352
src=ROOT/'patched/First Queen IV - Varcia Senki (kor).bin'
orig=ROOT/'original/First Queen IV - Varcia Senki (Japan).bin'
dst=WORK/'fq4-ending-test-patched-exe-original-mov04.bin'
# regenerate this single variant deterministically
shutil.copyfile(src,dst)
ob=orig.read_bytes()
with dst.open('r+b') as f:
    # /MOV/MOV04.STR;1 LBA 18430, size 8648704 = 4223 sectors of logical 2048, raw sectors 18430..22652
    for lba in range(18430,22653):
        f.seek(lba*SE)
        f.write(ob[lba*SE:(lba+1)*SE])
cue=WORK/'fq4-ending-test-patched-exe-original-mov04.cue'
cue.write_text('FILE "fq4-ending-test-patched-exe-original-mov04.bin" BINARY\n  TRACK 01 MODE2/2352\n    INDEX 01 00:00:00\n',encoding='ascii')
manifest={'variant':'patched executable/data with original MOV04 raw sectors','bin':str(dst.relative_to(ROOT)).replace('\\','/'),'cue':str(cue.relative_to(ROOT)).replace('\\','/'),'replaced_lba':[18430,22652],'sha256':hashlib.sha256(dst.read_bytes()).hexdigest()}
(OUT/'variant-original-mov04.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(manifest,ensure_ascii=False,indent=2))

from pathlib import Path
import json, hashlib, shutil
ROOT=Path(r'F:/workspace-server/fq4')
OUT=ROOT/'docs/fq4/analysis/034'
WORK=ROOT/'work/fq4/034'
SE=2352
src=ROOT/'patched/First Queen IV - Varcia Senki (kor).bin'
orig=ROOT/'original/First Queen IV - Varcia Senki (Japan).bin'
dst=WORK/'fq4-ending-test-patched-exe-original-mov03-mov04.bin'
shutil.copyfile(src,dst)
ob=orig.read_bytes()
with dst.open('r+b') as f:
    for lba in range(10030,22653):
        f.seek(lba*SE); f.write(ob[lba*SE:(lba+1)*SE])
cue=WORK/'fq4-ending-test-patched-exe-original-mov03-mov04.cue'
cue.write_text('FILE "fq4-ending-test-patched-exe-original-mov03-mov04.bin" BINARY\n  TRACK 01 MODE2/2352\n    INDEX 01 00:00:00\n',encoding='ascii')
manifest={'variant':'patched executable/data with original MOV03 and MOV04 raw sectors','bin':str(dst.relative_to(ROOT)).replace('\\','/'),'cue':str(cue.relative_to(ROOT)).replace('\\','/'),'replaced_lba':[10030,22652],'sha256_before_repair':hashlib.sha256(dst.read_bytes()).hexdigest()}
(OUT/'variant-original-mov03-mov04.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(manifest,ensure_ascii=False,indent=2))

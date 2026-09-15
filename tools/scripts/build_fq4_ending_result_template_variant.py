from pathlib import Path
import json, hashlib, shutil
ROOT=Path(r'F:/workspace-server/fq4')
OUT=ROOT/'docs/fq4/analysis/034'
WORK=ROOT/'work/fq4/034'
SE=2352
src=WORK/'fq4-ending-test-patched-exe-original-mov04.bin'
if not src.exists():
    src=ROOT/'patched/First Queen IV - Varcia Senki (kor).bin'
orig_bin=ROOT/'original/First Queen IV - Varcia Senki (Japan).bin'
orig_exe=ROOT/'work/fq4/001/original/SLPS_006.04'
dst=WORK/'fq4-ending-test-original-mov04-original-result-template.bin'
shutil.copyfile(src,dst)
# Replace result template in /SLPS_006.04 logical file offset 0xE0400..0xE04AF from original exe.
exe_off=0xE0400
length=0xB0
lba0=24
orig_chunk=orig_exe.read_bytes()[exe_off:exe_off+length]
with dst.open('r+b') as f:
    pos=0
    while pos<length:
        logical=exe_off+pos
        lba=lba0+logical//2048
        insec=logical%2048
        n=min(length-pos,2048-insec)
        f.seek(lba*SE+24+insec)
        f.write(orig_chunk[pos:pos+n])
        pos+=n
cue=WORK/'fq4-ending-test-original-mov04-original-result-template.cue'
cue.write_text('FILE "fq4-ending-test-original-mov04-original-result-template.bin" BINARY\n  TRACK 01 MODE2/2352\n    INDEX 01 00:00:00\n',encoding='ascii')
manifest={'variant':'patched 241112 + original MOV04 + original ending result template 0xE0400..0xE04AF','bin':str(dst.relative_to(ROOT)).replace('\\','/'),'cue':str(cue.relative_to(ROOT)).replace('\\','/'),'exe_template_offset':'0xE0400','template_length':'0xB0','sha256_before_repair':hashlib.sha256(dst.read_bytes()).hexdigest()}
(OUT/'variant-original-result-template.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(manifest,ensure_ascii=False,indent=2))

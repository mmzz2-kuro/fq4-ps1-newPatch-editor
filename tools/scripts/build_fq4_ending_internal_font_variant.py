from pathlib import Path
import json, hashlib, shutil
ROOT=Path(r'F:/workspace-server/fq4')
OUT=ROOT/'docs/fq4/analysis/034'
WORK=ROOT/'work/fq4/034'
SE=2352
base=WORK/'fq4-241112-internal-font-base.bin'
orig_bin=ROOT/'original/First Queen IV - Varcia Senki (Japan).bin'
orig_exe=ROOT/'work/fq4/001/original/SLPS_006.04'
dst=WORK/'fq4-241112-internal-font-original-mov04-korean-result.bin'
shutil.copyfile(base,dst)
# Replace MOV04 raw sectors from original: /MOV/MOV04.STR;1 LBA 18430..22652.
ob=orig_bin.read_bytes()
with dst.open('r+b') as f:
    for lba in range(18430,22653):
        f.seek(lba*SE)
        f.write(ob[lba*SE:(lba+1)*SE])
# Rebuild ending result template from original, preserving layout and replacing only labels.
chunk=bytearray(orig_exe.read_bytes()[0xE0400:0xE0400+0xB0])
items=[('名前','이름'),('クラス','직업'),('パワー','파워'),('討数','격추'),('戦場より生還！','전장에서 생환!')]
replacements=[]
for old_text,new_text in items:
    old=old_text.encode('cp932')
    rel=bytes(chunk).find(old)
    if rel<0: raise SystemExit(f'old label not found: {old_text}')
    new=new_text.encode('cp949')
    if len(new)>len(old): raise SystemExit(f'new too long: {new_text}')
    chunk[rel:rel+len(old)] = new + b' '*(len(old)-len(new))
    replacements.append({'relative_offset':hex(rel),'old_text':old_text,'new_text':new_text,'old_bytes':old.hex(' '),'new_bytes_padded':bytes(chunk[rel:rel+len(old)]).hex(' ')})
with dst.open('r+b') as f:
    pos=0; exe_off=0xE0400; length=len(chunk); lba0=24
    while pos<length:
        logical=exe_off+pos
        lba=lba0+logical//2048
        insec=logical%2048
        n=min(length-pos,2048-insec)
        f.seek(lba*SE+24+insec)
        f.write(chunk[pos:pos+n])
        pos+=n
cue=WORK/'fq4-241112-internal-font-original-mov04-korean-result.cue'
cue.write_text('FILE "fq4-241112-internal-font-original-mov04-korean-result.bin" BINARY\n  TRACK 01 MODE2/2352\n    INDEX 01 00:00:00\n',encoding='utf-8-sig',newline='')
manifest={'variant':'241112 Korean patch + embedded Hangul font + original MOV04 + Korean ending result template','base':str(base.relative_to(ROOT)).replace('\\','/'),'bin':str(dst.relative_to(ROOT)).replace('\\','/'),'cue':str(cue.relative_to(ROOT)).replace('\\','/'),'mov04_replaced_lba':[18430,22652],'exe_template_offset':'0xE0400','template_length':'0xB0','replacements':replacements,'sha256_before_repair':hashlib.sha256(dst.read_bytes()).hexdigest()}
(OUT/'variant-internal-font-original-mov04-korean-result.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'bin':manifest['bin'],'cue':manifest['cue'],'sha256_before_repair':manifest['sha256_before_repair']},ensure_ascii=False,indent=2))

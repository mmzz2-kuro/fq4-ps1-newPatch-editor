from pathlib import Path
import json, hashlib, shutil
ROOT=Path(r'F:/workspace-server/fq4')
OUT=ROOT/'docs/fq4/analysis/034'
WORK=ROOT/'work/fq4/034'
SE=2352
base=WORK/'fq4-241112-internal-font-base.bin'
orig_bin=ROOT/'original/First Queen IV - Varcia Senki (Japan).bin'
orig_exe=ROOT/'work/fq4/001/original/SLPS_006.04'
map_rows=json.loads((ROOT/'docs/fq4/analysis/005/encoding-map.json').read_text(encoding='utf-8'))['mapping']
char_to_code={r['character']: bytes.fromhex(r['game_code']) for r in map_rows}

def enc_game(text):
    out=bytearray()
    for ch in text:
        if ch == ' ':
            out.append(0x20)
        elif ch == '!':
            out += '！'.encode('cp932')
        elif ch in char_to_code:
            out += char_to_code[ch]
        else:
            # allow ASCII fallback for digits/format tokens only
            o=ord(ch)
            if 0x20 <= o < 0x7f:
                out.append(o)
            else:
                raise ValueError(f'no game code for {ch!r}')
    return bytes(out)

dst=WORK/'fq4-241112-internal-font-original-mov04-korean-gamecode-result.bin'
shutil.copyfile(base,dst)
# Replace MOV04 raw sectors from original.
ob=orig_bin.read_bytes()
with dst.open('r+b') as f:
    for lba in range(18430,22653):
        f.seek(lba*SE); f.write(ob[lba*SE:(lba+1)*SE])
# Restore original result template then replace labels with game_code bytes.
chunk=bytearray(orig_exe.read_bytes()[0xE0400:0xE0400+0xB0])
items=[('名前','이름'),('クラス','직업'),('パワー','파워'),('討数','격추'),('戦場より生還！','전장에서생환!'),('にて死亡','에서사망')]
replacements=[]
for old_text,new_text in items:
    old=old_text.encode('cp932')
    rel=bytes(chunk).find(old)
    if rel<0: raise SystemExit(f'old label not found: {old_text}')
    new=enc_game(new_text)
    if len(new)>len(old): raise SystemExit(f'new too long for {old_text}: {len(new)} > {len(old)}')
    chunk[rel:rel+len(old)] = new + b' '*(len(old)-len(new))
    replacements.append({'relative_offset':hex(rel),'old_text':old_text,'new_text':new_text,'old_bytes':old.hex(' '),'new_game_bytes_padded':bytes(chunk[rel:rel+len(old)]).hex(' ')})
with dst.open('r+b') as f:
    pos=0; exe_off=0xE0400; length=len(chunk); lba0=24
    while pos<length:
        logical=exe_off+pos; lba=lba0+logical//2048; insec=logical%2048; n=min(length-pos,2048-insec)
        f.seek(lba*SE+24+insec); f.write(chunk[pos:pos+n]); pos+=n
cue=WORK/'fq4-241112-internal-font-original-mov04-korean-gamecode-result.cue'
cue.write_text('FILE "fq4-241112-internal-font-original-mov04-korean-gamecode-result.bin" BINARY\n  TRACK 01 MODE2/2352\n    INDEX 01 00:00:00\n',encoding='utf-8-sig',newline='')
manifest={'variant':'241112 Korean patch + embedded Hangul font + original MOV04 + Korean game-code ending result template','base':str(base.relative_to(ROOT)).replace('\\','/'),'bin':str(dst.relative_to(ROOT)).replace('\\','/'),'cue':str(cue.relative_to(ROOT)).replace('\\','/'),'mov04_replaced_lba':[18430,22652],'exe_template_offset':'0xE0400','template_length':'0xB0','replacements':replacements,'sha256_before_repair':hashlib.sha256(dst.read_bytes()).hexdigest()}
(OUT/'variant-internal-font-original-mov04-korean-gamecode-result.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'bin':manifest['bin'],'cue':manifest['cue'],'sha256_before_repair':manifest['sha256_before_repair'],'replacements':[(r['relative_offset'],r['new_game_bytes_padded']) for r in replacements]},ensure_ascii=True,indent=2))



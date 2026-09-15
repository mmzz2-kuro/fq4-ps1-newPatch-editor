from pathlib import Path
import json, struct, hashlib
ROOT=Path(r'F:/workspace-server/fq4')
OUT=ROOT/'docs/fq4/analysis/034'
SECTOR=2352
DATA_OFF=24

def read_file_from_raw(bin_path,lba,size):
    raw=bin_path.read_bytes(); out=bytearray()
    for i in range((size+2047)//2048):
        sec=raw[(lba+i)*SECTOR:(lba+i+1)*SECTOR]
        out += sec[24:2072]
    return bytes(out[:size])

def ranges(nums):
    if not nums: return []
    nums=sorted(nums); res=[]; s=e=nums[0]
    for n in nums[1:]:
        if n==e+1: e=n
        else: res.append([s,e,e-s+1]); s=e=n
    res.append([s,e,e-s+1]); return res

imgs={
 'original': ROOT/'original/First Queen IV - Varcia Senki (Japan).bin',
 'patched_241112': ROOT/'patched/First Queen IV - Varcia Senki (kor).bin',
 'my_250826': ROOT/'my-patch/make-patch/fq4-kor-250826.bin',
 'my_250826_v2': ROOT/'my-patch/make-patch/fq4-kor-250826-v2.bin',
 'my_race': ROOT/'my-patch/make-patch/fq4-race.bin',
}
# from ISO survey: /SLPS_006.04;1 lba 24 size 1075200
files={k:read_file_from_raw(p,24,1075200) for k,p in imgs.items() if p.exists()}
orig=files['original']
summary={}
for k,b in files.items():
    diffs=[i for i,(a,c) in enumerate(zip(orig,b)) if a!=c]
    words=[]
    for i in range(0,min(len(orig),len(b))-3,4):
        if orig[i:i+4]!=b[i:i+4]: words.append(i)
    summary[k]={
        'sha256':hashlib.sha256(b).hexdigest(),
        'diff_bytes_vs_original':len(diffs),
        'diff_byte_ranges_first80':ranges(diffs)[:80],
        'diff_word_offsets_first80':[hex(x) for x in words[:80]],
    }
# compare 241112 to 250826 logical executable bytes
b1=files['patched_241112']; b2=files['my_250826']
d=[i for i,(a,c) in enumerate(zip(b1,b2)) if a!=c]
summary['patched_241112_vs_my_250826']={'diff_bytes':len(d),'ranges_first80':ranges(d)[:80]}
(OUT/'executable-diff-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(summary,ensure_ascii=False,indent=2)[:6000])

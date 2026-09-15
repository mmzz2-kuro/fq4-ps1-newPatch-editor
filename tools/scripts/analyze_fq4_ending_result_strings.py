from pathlib import Path
import json
ROOT=Path(r'F:/workspace-server/fq4')
OUT=ROOT/'docs/fq4/analysis/034'
orig=ROOT/'work/fq4/001/original/SLPS_006.04'
pat=ROOT/'work/fq4/001/patched/SLPS_006.04'
ob=orig.read_bytes(); pb=pat.read_bytes()
terms=['名前','クラス','パワー','討数','ＨＰ','ＬＶ','HP','LV']
rows=[]
for t in terms:
    for enc in ['shift_jis','cp932','ascii']:
        try: needle=t.encode(enc)
        except Exception: continue
        if not needle: continue
        offs=[]; pos=-1
        while True:
            pos=ob.find(needle,pos+1)
            if pos<0: break
            offs.append(pos)
            if len(offs)>30: break
        if offs:
            for off in offs:
                rows.append({'term':t,'encoding':enc,'offset':off,'orig_hex':ob[off:off+64].hex(' '),'patched_hex':pb[off:off+64].hex(' '),'orig_sjis':ob[off:off+64].decode('cp932','replace'),'patched_sjis':pb[off:off+64].decode('cp932','replace')})
# also find nearby exact Japanese screen phrase patterns from visual: 戦場より生還 maybe
for t in ['戦場より生還','生還','持発','穿舌拭辞']:
    try: needle=t.encode('cp932')
    except Exception: continue
    pos=-1
    while True:
        pos=ob.find(needle,pos+1)
        if pos<0: break
        rows.append({'term':t,'encoding':'cp932','offset':pos,'orig_hex':ob[pos:pos+96].hex(' '),'patched_hex':pb[pos:pos+96].hex(' '),'orig_sjis':ob[pos:pos+96].decode('cp932','replace'),'patched_sjis':pb[pos:pos+96].decode('cp932','replace')})
(OUT/'ending-result-strings.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps([{'term':r['term'],'off':hex(r['offset']),'orig':r['orig_sjis'][:30],'patched':r['patched_sjis'][:30]} for r in rows],ensure_ascii=False,indent=2))

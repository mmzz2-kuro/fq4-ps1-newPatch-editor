from pathlib import Path
import json, unicodedata
terms=['ｿｰﾄﾞ','ﾅｲﾌ','ｱｯｸｽ','ﾗﾝｽ','ﾎﾞｳ','ｼｰﾙﾄﾞ','ｱｰﾏｰ','ﾍﾙﾑ','ﾎﾟｰｼｮﾝ','ﾘﾝｸﾞ','ｸﾘｽﾀﾙ','ｱｲﾃﾑ','きずぐすり','薬','剣','盾','鎧']
files=[Path('original/First Queen IV - Varcia Senki (Japan).bin'),Path('patched/First Queen IV - Varcia Senki (kor).bin'),Path('korean-patch/First Queen IV - Varcia Senki (Japan)-patched.bin'),Path('work/fq4/001/original/SLPS_006.04'),Path('work/fq4/001/patched/SLPS_006.04'),Path('dos-save/editor/FQ4Edit.exe')]
out={}
for path in files:
    if not path.exists(): continue
    b=path.read_bytes(); hits=[]
    for t in terms:
        enc=t.encode('cp932','ignore')
        off=-1
        while True:
            off=b.find(enc,off+1)
            if off<0: break
            ctx=b[max(0,off-48):off+128]
            dec=unicodedata.normalize('NFKC',ctx.decode('cp932','replace'))
            hits.append({'term':t,'off':hex(off),'context_hex':ctx.hex(' '),'context':dec})
    out[str(path)]=hits
    print(str(path), len(hits))
    for h in hits[:30]: print(ascii(h['term']), h['off'], ascii(h['context'][:160]))
Path('docs/fq4/analysis/035/item-term-search.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

from pathlib import Path
import json, unicodedata, sys
sys.path.insert(0,'tools/scripts')
from fq4_memcard import MemoryCard
START=0xE67D5; WIDTH=0x11; COUNT=72
orig=Path('work/fq4/001/original/SLPS_006.04').read_bytes()
patch=Path('work/fq4/001/patched/SLPS_006.04').read_bytes()
enc=json.load(open('docs/fq4/analysis/005/encoding-map.json',encoding='utf-8'))['mapping']
game_to_char={int(x['game_code'],16): bytes.fromhex(x['euc_kr']).decode('euc-kr','replace') for x in enc if not x.get('blank')}

def clean_raw(raw): return raw.rstrip(b'\x00 ')
def dec_orig(raw): return unicodedata.normalize('NFKC', clean_raw(raw).decode('cp932','replace')).strip()
def dec_patch(raw):
    raw=clean_raw(raw)
    out=[]; i=0
    while i<len(raw):
        if i+1<len(raw) and raw[i]>=0x80:
            code=(raw[i]<<8)|raw[i+1]
            if code==0x8140:
                out.append(' '); i+=2; continue
            if code in game_to_char:
                out.append(game_to_char[code]); i+=2; continue
        if raw[i]<0x80:
            out.append(chr(raw[i])); i+=1
        else:
            if i+1<len(raw):
                try:
                    out.append(raw[i:i+2].decode('cp932'))
                    i+=2
                    continue
                except Exception:
                    pass
            out.append('?'); i+=1
    return ''.join(out).strip()
items=[]
for idx in range(COUNT):
    off=START+idx*WIDTH
    ro=orig[off:off+WIDTH]
    rp=patch[off:off+WIDTH]
    items.append({'index0':idx,'id1':idx+1,'offset':hex(off),'original':dec_orig(ro),'patched':dec_patch(rp),'orig_hex':ro.hex().upper(),'patched_hex':rp.hex().upper()})
ids=set()
for path in sorted(Path('memcard').rglob('*')):
    if path.suffix.lower() not in ('.mcd','.srm'): continue
    try: card=MemoryCard.open(path)
    except Exception: continue
    for slot in card.slots:
        for item in slot.items(): ids.add(item.item_id)
report={'start':hex(START),'width':WIDTH,'count':COUNT,'items':items,'used_item_ids':sorted(ids)}
Path('docs/fq4/analysis/035').mkdir(parents=True,exist_ok=True)
Path('docs/fq4/analysis/035/item-name-table.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('count',len(items),'used_ids',sorted(ids))
for item_id in sorted(ids):
    if 1<=item_id<=len(items): print(item_id, ascii(items[item_id-1]['patched']), '/', ascii(items[item_id-1]['original']))
    else: print(item_id,'out')

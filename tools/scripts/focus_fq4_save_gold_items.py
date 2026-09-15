from pathlib import Path
import json, struct

ROOT = Path(r'F:/workspace-server/fq4')
OUT = ROOT / 'docs/fq4/analysis/033'
OUT.mkdir(parents=True, exist_ok=True)

SAVE_MAGIC = b'SC\x13\x04'
PAYLOAD_SIZE = 0x8000
CHAR_OFF = 0x09A6
CHAR_SIZE = 0x20 * 640
CHAR_END = CHAR_OFF + CHAR_SIZE
CHECKSUM_OFF = 0x7DA6

mem_files = sorted([p for p in (ROOT/'memcard').rglob('*') if p.is_file() and p.suffix.lower() in ('.mcd','.srm')])

def iter_slots(buf):
    # raw PS1 memory card: 16 blocks of 0x2000; FQ4 save consumes 4 blocks, payload begins at block start.
    for block in range(1, 16):
        off = block * 0x2000
        if off + PAYLOAD_SIZE <= len(buf) and buf[off:off+4] == SAVE_MAGIC:
            yield block, off, buf[off:off+PAYLOAD_SIZE]

def inv_pairs(payload, start=0x0492, max_entries=96):
    pairs=[]
    first_empty=None
    for i in range(max_entries):
        pos=start+i*2
        iid=payload[pos]
        qty=payload[pos+1]
        if iid==0 and qty==0 and first_empty is None:
            first_empty=i
        if iid or qty:
            pairs.append({'entry':i,'offset':pos,'item_id':iid,'qty':qty})
    return pairs, first_empty

slots=[]
for p in mem_files:
    b=p.read_bytes()
    for block, abs_off, payload in iter_slots(b):
        pairs, first_empty = inv_pairs(payload)
        slots.append({
            'file': str(p.relative_to(ROOT)).replace('\\','/'),
            'block': block,
            'payload_abs_offset': abs_off,
            'gold_u16le_0692': struct.unpack_from('<H', payload, 0x0692)[0],
            'gold_u32le_0692': struct.unpack_from('<I', payload, 0x0692)[0],
            'pre_item_048c_hex': payload[0x048c:0x0492].hex(' '),
            'inventory_start': '0x0492',
            'inventory_first_empty_entry': first_empty,
            'inventory_nonzero_count_96': len(pairs),
            'inventory_nonzero_pairs': pairs[:48],
            'after_inventory_0520_0560_hex': payload[0x0520:0x0560].hex(' '),
        })

# compact search in DOS saves for the strongest inventory sequence and gold values
needles = {
    'inventory_seq_42013a0129010201': bytes.fromhex('42 01 3a 01 29 01 02 01'),
    'gold_12121_u16le_592f': bytes.fromhex('59 2f'),
    'gold_12058_u16le_1a2f': bytes.fromhex('1a 2f'),
}
dos_hits=[]
for p in sorted((ROOT/'dos-save').rglob('*')):
    if not p.is_file():
        continue
    try:
        b=p.read_bytes()
    except Exception:
        continue
    local={}
    for name, needle in needles.items():
        offs=[]
        pos=-1
        while True:
            pos=b.find(needle,pos+1)
            if pos<0:
                break
            offs.append(pos)
            if len(offs)>=20:
                break
        if offs:
            local[name]=offs
    if local:
        dos_hits.append({'file': str(p.relative_to(ROOT)).replace('\\','/'), 'length': len(b), 'hits': local})

result={
    'status':'candidate_structure_survey',
    'slot_count':len(slots),
    'character_region': {'offset':'0x09A6','size':'0x5000','end':'0x59A6'},
    'checksum_region': {'offset':'0x7DA6','count':8},
    'candidate_gold': {'payload_offset':'0x0692','encoding':'uint16 little-endian 후보','note':'values differ plausibly between saves; needs runtime known-gold confirmation before write support'},
    'candidate_inventory': {'payload_offset':'0x0492','entry_size':2,'encoding':'item_id u8 + quantity u8 후보','empty':'00 00 후보','note':'nonzero pairs form a dense item list before the character region'},
    'slots':slots,
    'dos_save_hits':dos_hits,
}
(OUT/'gold-item-focused.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')

print(json.dumps({
    'slot_count':len(slots),
    'files':len(mem_files),
    'gold_values':[s['gold_u16le_0692'] for s in slots],
    'inv_counts':[s['inventory_nonzero_count_96'] for s in slots],
    'dos_hit_files':len(dos_hits),
    'out':str((OUT/'gold-item-focused.json').relative_to(ROOT)).replace('\\','/')
},ensure_ascii=False,indent=2))

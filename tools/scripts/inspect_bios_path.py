"""Static candidate discovery only; no complete control-flow claim."""
import json
import struct
import sys
from pathlib import Path
from survey_rom import Disc, save, sha

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'work/fq4/python-deps'))
from capstone import Cs, CS_ARCH_MIPS, CS_MODE_MIPS32, CS_MODE_LITTLE_ENDIAN

def main():
    out=ROOT/'docs/fq4/analysis/001'
    a=(ROOT/'work/fq4/001/original/SLPS_006.04').read_bytes()
    b=(ROOT/'work/fq4/001/patched/SLPS_006.04').read_bytes()
    md=Cs(CS_ARCH_MIPS,CS_MODE_MIPS32|CS_MODE_LITTLE_ENDIAN)
    md.skipdata=True
    found=[]; chunks=[]
    for kind,data in [('original',a),('patched',b)]:
        candidates=[]
        for i in range(2048,len(data)-3,4):
            w=struct.unpack_from('<I',data,i)[0]
            if w>>26==15 and w&65535 in (0xbfc0,0xbfc6,0xbfc7,0x1fc0,0x1fc6,0x1fc7):
                candidates.append((i,'bios_address_lui'))
            if w in (0x24090051,0x34090051):
                candidates.append((i,'bios_function_51_candidate'))
        for i,reason in candidates:
            addr=0x80010000+i-2048
            found.append({'kind':kind,'file_offset':hex(i),'ram':hex(addr),'reason':reason})
            chunks.append(f'\n{kind} {reason} {addr:08x} file={i:x}\n')
            for ins in md.disasm(data[max(2048,i-32):i+100],addr-min(32,i-2048)):
                chunks.append(f'{ins.address:08x} {ins.bytes.hex()} {ins.mnemonic} {ins.op_str}\n')
    save(out/'bios-candidates.json',found)
    (out/'bios-candidate-disassembly.txt').write_text(''.join(chunks),encoding='utf-8')
    bios=(ROOT/'korean-patch/SCPH1001.BIN').read_bytes()
    save(out/'bios-identity.json',{'sha256':sha(bios),'size':len(bios),'tail_version':bios[0x7ff30:0x7ff90].decode('ascii',errors='replace'),'note':'No unmodified comparison BIOS supplied'})
    current=Disc(ROOT/'work/fq4/rom/current.bin')
    exe_record=next(r for r in current.files if r['path']=='/SLPS_006.04;1')
    exe_path=ROOT/'work/fq4/001/reproduced/SLPS_006.04'
    exe_path.parent.mkdir(parents=True,exist_ok=True)
    exe_path.write_bytes(current.read(exe_record))
    supplied=Disc(next((ROOT/'patched').glob('*.bin')))
    sectors=[]
    for s in range(len(current.raw)//2352):
        x,y=current.raw[s*2352:(s+1)*2352],supplied.raw[s*2352:(s+1)*2352]
        if x!=y:
            sectors.append({'sector':s,'different_bytes':sum(u!=v for u,v in zip(x,y)),'header':x[:24]!=y[:24],'payload':x[24:2072]!=y[24:2072],'tail':x[2072:]!=y[2072:]})
    oldfiles={r['path']:r for r in supplied.files}; newfiles={r['path']:r for r in current.files}
    save(out/'reproduction.json',{'command':'korean-patch/xdelta.exe -d -f -s <original.bin> <patch.xdelta> work/fq4/rom/current.bin','tool_version':'3.0u','current_sha256':sha(current.raw),'supplied_sha256':sha(supplied.raw),'equal':current.raw==supplied.raw,'file_records_equal':current.files==supplied.files,'different_files':[name for name in sorted(oldfiles.keys()|newfiles.keys()) if oldfiles.get(name)!=newfiles.get(name)],'differing_sectors':sectors})
    print(json.dumps({'candidates':found,'reproduction_diff_sectors':len(sectors),'file_records_equal':current.files==supplied.files},indent=2))

if __name__=='__main__': main()

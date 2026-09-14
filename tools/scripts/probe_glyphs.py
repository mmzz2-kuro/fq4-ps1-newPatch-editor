"""Isolated BIOS routine observation and static glyph rendering; not game runtime."""
import json
import sys
from pathlib import Path
from survey_rom import save, sha
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'work/fq4/python-deps'))
from unicorn import Uc, UC_ARCH_MIPS, UC_MODE_MIPS32, UC_MODE_LITTLE_ENDIAN
from unicorn.mips_const import UC_MIPS_REG_A0, UC_MIPS_REG_A1, UC_MIPS_REG_A2, UC_MIPS_REG_V0, UC_MIPS_REG_SP, UC_MIPS_REG_RA, UC_MIPS_REG_PC
from PIL import Image, ImageDraw

def main():
    bios=(ROOT/'korean-patch/SCPH1001.BIN').read_bytes()
    uc=Uc(UC_ARCH_MIPS, UC_MODE_MIPS32|UC_MODE_LITTLE_ENDIAN)
    uc.mem_map(0,0x200000)
    # Explicit experimental relocation inferred from internal jal/table references.
    uc.mem_write(0,bios[0xfb00:])
    uc.mem_map(0x1fc00000,0x80000); uc.mem_write(0x1fc00000,bios)
    rows=[]
    sample=(ROOT/'work/fq4/001/patched/SLPS_006.04').read_bytes()[0xe0158:0xe0168]
    codes=[int.from_bytes(sample[i:i+2],'big') for i in range(0,len(sample),2)]
    codes=[x for x in codes if x]
    # Compare known boundary values with the observed base/stride calculation.
    targets=list(dict.fromkeys([0x8140,0x889f,0x8952,0x8eb5,0x917e,0x8144,0,0xffff]+codes))
    for code in targets:
        uc.reg_write(UC_MIPS_REG_SP,0x1ff000); uc.reg_write(UC_MIPS_REG_RA,0x1f0000)
        uc.reg_write(UC_MIPS_REG_A0,code)
        uc.emu_start(0x65e0,0x1f0000,count=10000)
        assert uc.reg_read(UC_MIPS_REG_PC)==0x1f0000, 'Probe did not return'
        addr=uc.reg_read(UC_MIPS_REG_V0)&0xffffffff
        row={'code':hex(code),'returned_address':hex(addr)}
        if 0xbfc00000<=addr<=0xbfc80000-30:
            off=addr-0xbfc00000
            row.update({'bios_offset':hex(off),'glyph_sha256':sha(bios[off:off+30])})
        rows.append(row)
    exe=(ROOT/'work/fq4/001/reproduced/SLPS_006.04').read_bytes()
    uc.mem_write(0x10000,exe[2048:])
    for row in rows:
        if 'bios_offset' not in row: continue
        glyph=bios[int(row['bios_offset'],16):int(row['bios_offset'],16)+30]
        uc.reg_write(UC_MIPS_REG_A0,0x1e0000)
        uc.reg_write(UC_MIPS_REG_A1,int(row['returned_address'],16))
        uc.reg_write(UC_MIPS_REG_A2,0)
        uc.reg_write(UC_MIPS_REG_RA,0x1f0000)
        uc.emu_start(0x46674,0x1f0000,count=10000)
        assert uc.reg_read(UC_MIPS_REG_PC)==0x1f0000
        expected=bytearray()
        for y in range(15):
            pixels=[1 if glyph[y*2+x//8] & (0x80>>(x%8)) else 0 for x in range(16)]
            expected.extend(pixels[x]|pixels[x+1]<<4 for x in range(0,16,2))
        expected.extend(bytes(8))
        actual=bytes(uc.mem_read(0x1e0000,128))
        assert actual==expected
        row['game_converter_matches_static_decode']=True
        row['converted_sha256']=sha(actual)
    save(ROOT/'docs/fq4/analysis/001/glyph-probe.json',{'evidence_class':'isolated function execution, experimental relocation; not normal BIOS boot or game execution','bios_sha256':sha(bios),'entry':'0x65e0','relocation':'BIOS file 0xfb00 mapped to RAM 0','converter':'250826 executable 0x80046674; 6 valid glyph probes; A2=0','results':rows})
    mapping={int(x['code'],16):int(x['bios_offset'],16) for x in rows if 'bios_offset' in x}
    im=Image.new('RGB',(max(len(codes)*64,480),110),'white'); draw=ImageDraw.Draw(im)
    for i,code in enumerate(codes):
        off=mapping[code]; glyph=bios[off:off+30]
        for y in range(15):
            # Consumer reads little-endian halfword then expands bit7..0, bit15..8.
            for x in range(16):
                if glyph[y*2+x//8] & (0x80>>(x%8)):
                    draw.rectangle((i*64+x*3,24+y*3,i*64+x*3+2,24+y*3+2),fill='black')
        draw.text((i*64,4),f'{code:04X}',fill='black')
    draw.text((4,85),'STATIC BIOS GLYPHS / NOT AN IN-GAME CAPTURE',fill='black')
    target=ROOT/'work/fq4/001/glyph-sample.png'; target.parent.mkdir(parents=True,exist_ok=True); im.save(target)
    print(json.dumps(rows,indent=2))

if __name__=='__main__': main()

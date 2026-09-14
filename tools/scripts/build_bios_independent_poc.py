"""Build the FQ4 250826 minimal BIOS-independent glyph PoC in the one work ROM."""
import hashlib
import json
import shutil
import struct
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEPS = ROOT / 'work/fq4/python-deps'
sys.path.insert(0, str(DEPS))
from capstone import Cs, CS_ARCH_MIPS, CS_MODE_MIPS32, CS_MODE_LITTLE_ENDIAN
from keystone import Ks, KS_ARCH_MIPS, KS_MODE_MIPS32, KS_MODE_LITTLE_ENDIAN

ORIGINAL_SHA = '858f3a806cbb97d0b9dd1a43c285989ac31200959c3fbff61296780a99b81e2a'
BASE_SHA = '9363cdfa247d38f5f819f5e79a25ff25ada3b2394f887726f29231da6ccbffb5'
BIOS_SHA = 'f8658d98e32c6a8560a832c50f74f84662e1bff98c486c6480c207a2b404b88f'
EXE_LBA = 24
EXE_SIZE = 1_075_200
LOAD = 0x80010000
EXE_HEADER = 0x800
HOOK_RAM = 0x80082C8C
CODE_RAM = 0x800ECC40
GLYPH_RAM = 0x800ECD00
GLYPHS = [(0x8952, 0x6AA88, '교'), (0x8EB5, 0x7242C, '섭'), (0x917E, 0x75FF0, '중')]

def sha(data): return hashlib.sha256(data).hexdigest()
def file_sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''): h.update(block)
    return h.hexdigest()
def dump(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
def exe_off(addr): return addr-LOAD+EXE_HEADER
def raw_pos(file_off): return (EXE_LBA+file_off//2048)*2352+24+file_off%2048

EDC=[]; EF=[0]*256; EB=[0]*256
for i in range(256):
    x=i
    for _ in range(8): x=(x>>1)^0xD8018001 if x&1 else x>>1
    EDC.append(x&0xffffffff)
    j=((i<<1)^(0x11d if i&0x80 else 0))&255; EF[i]=j; EB[i^j]=i
def edc(data):
    x=0
    for b in data: x=(x>>8)^EDC[(x^b)&255]
    return x&0xffffffff
def ecc_write(address,data,major_count,minor_count,major_mult,minor_inc,out,at):
    size=major_count*minor_count
    for major in range(major_count):
        index=((major>>1)*major_mult+(major&1))%size; a=0; b=0
        for _ in range(minor_count):
            v=address[index] if index<4 else data[index-4]
            index=(index+minor_inc)%size; a^=v; b^=v; a=EF[a]
        a=EB[EF[a]^b]; out[at+major]=a; out[at+major+major_count]=a^b
def fix_form1(sec):
    if len(sec)!=2352 or sec[15]!=2 or sec[16:20]!=sec[20:24] or sec[18]&0x20:
        raise ValueError('Expected Mode 2 Form 1 sector')
    struct.pack_into('<I',sec,2072,edc(sec[16:2072]))
    data=bytes(sec[16:2076]); out=bytearray(276)
    ecc_write(b'\0\0\0\0',data,86,24,2,86,out,0)
    ecc_write(b'\0\0\0\0',data+out[:172],52,43,86,88,out,172)
    sec[2076:2352]=out

def assemble():
    asm='''
        ori $t0, $zero, 0x8952
        beq $a0, $t0, glyph0
        nop
        ori $t0, $zero, 0x8eb5
        beq $a0, $t0, glyph1
        nop
        ori $t0, $zero, 0x917e
        beq $a0, $t0, glyph2
        nop
        addiu $t2, $zero, 0xb0
        addiu $t1, $zero, 0x51
        jr $t2
        nop
    glyph0:
        lui $v0, 0x800e
        ori $v0, $v0, 0xcd00
        jr $ra
        nop
    glyph1:
        lui $v0, 0x800e
        ori $v0, $v0, 0xcd1e
        jr $ra
        nop
    glyph2:
        lui $v0, 0x800e
        ori $v0, $v0, 0xcd3c
        jr $ra
        nop
    '''
    code,count=Ks(KS_ARCH_MIPS,KS_MODE_MIPS32|KS_MODE_LITTLE_ENDIAN).asm(asm,addr=CODE_RAM,as_bytes=True)
    if count < 17 or len(code)>GLYPH_RAM-CODE_RAM: raise ValueError('Unexpected assembly result')
    return bytes(code),asm

def main():
    original=next((ROOT/'original').glob('*.bin')); patch=next((ROOT/'korean-patch').glob('*250826*.xdelta'))
    bios_path=ROOT/'korean-patch/SCPH1001.BIN'; current=ROOT/'work/fq4/rom/current.bin'
    if file_sha(original)!=ORIGINAL_SHA or file_sha(bios_path)!=BIOS_SHA: raise ValueError('Input identity mismatch')
    current.parent.mkdir(parents=True,exist_ok=True)
    subprocess.run([str(ROOT/'korean-patch/xdelta.exe'),'-d','-f','-s',str(original),str(patch),str(current)],check=True)
    if file_sha(current)!=BASE_SHA: raise ValueError('250826 baseline mismatch')
    image=bytearray(current.read_bytes()); baseline=bytes(image); bios=bios_path.read_bytes()
    exe=bytearray().join(image[(EXE_LBA+i)*2352+24:(EXE_LBA+i)*2352+2072] for i in range((EXE_SIZE+2047)//2048))[:EXE_SIZE]
    if not exe.startswith(b'PS-X EXE'): raise ValueError('Executable identity mismatch')
    code,source=assemble(); hook=Ks(KS_ARCH_MIPS,KS_MODE_MIPS32|KS_MODE_LITTLE_ENDIAN).asm(f'j 0x{CODE_RAM:08x}',addr=HOOK_RAM,as_bytes=True)[0]
    hook=bytes(hook)
    if len(hook)!=8: raise ValueError('Unexpected hook size')
    writes=[]
    def plan(writer,off,new,condition='exact bytes'):
        old=bytes(exe[off:off+len(new)])
        if old==new: raise ValueError(f'No-op write {writer}')
        writes.append({'writer':writer,'coordinate':'SLPS_006.04 file offset','offset':hex(off),'ram':hex(LOAD+off-EXE_HEADER),'length':len(new),'expected_sha256':sha(old),'final_sha256':sha(new),'source_condition':condition})
        exe[off:off+len(new)]=new
    expected=bytes.fromhex('b0000a24080040015100092400000000')
    ho=exe_off(HOOK_RAM)
    if bytes(exe[ho:ho+16])!=expected: raise ValueError('BIOS wrapper expected bytes mismatch')
    plan('glyph_lookup_hook',ho,hook,'first 8 bytes of verified 16-byte B0(51h) wrapper')
    co=exe_off(CODE_RAM); go=exe_off(GLYPH_RAM)
    region=bytes(exe[co:go+90])
    if any(region): raise ValueError('PoC region is not zero in 250826 baseline')
    plan('glyph_lookup_code',co,code,'zero-filled candidate region; adopted only for this PoC')
    glyph_data=b''.join(bios[o:o+30] for _,o,_ in GLYPHS)
    plan('minimal_glyph_data',go,glyph_data,'zero-filled candidate region; bytes extracted locally from identified BIOS')
    touched=set()
    for w in writes:
        off=int(w['offset'],16)
        for pos in range(off,off+w['length']):
            lba=EXE_LBA+pos//2048; user=pos%2048; image[lba*2352+24+user]=exe[pos]
            touched.add(lba)
    sector_audit=[]
    for lba in sorted(touched):
        start=lba*2352; before=bytearray(baseline[start:start+2352]); check=bytearray(before); fix_form1(check)
        if check!=before: raise ValueError(f'Baseline EDC/ECC invalid at LBA {lba}')
        sec=bytearray(image[start:start+2352]); fix_form1(sec); image[start:start+2352]=sec
        sector_audit.append({'lba':lba,'before_sha256':sha(before),'after_sha256':sha(sec),'payload_changed':before[24:2072]!=sec[24:2072],'edc_ecc_changed':before[2072:]!=sec[2072:]})
    # Complete raw diff audit: only touched sectors may differ; header/subheader stay fixed.
    diff_sectors=[]
    for lba in range(len(image)//2352):
        s=lba*2352
        if image[s:s+2352]!=baseline[s:s+2352]: diff_sectors.append(lba)
    if diff_sectors!=sorted(touched): raise ValueError('Unregistered changed sector')
    for lba in touched:
        s=lba*2352
        if image[s:s+24]!=baseline[s:s+24]: raise ValueError('Protected sector header changed')
    current.write_bytes(image)
    cue=ROOT/'work/fq4/rom/current.cue'
    cue.write_text('FILE "current.bin" BINARY\n  TRACK 01 MODE2/2352\n    INDEX 01 00:00:00\n',encoding='ascii',newline='\r\n')
    md=Cs(CS_ARCH_MIPS,CS_MODE_MIPS32|CS_MODE_LITTLE_ENDIAN)
    dis=[{'address':hex(i.address),'bytes':i.bytes.hex(),'mnemonic':i.mnemonic,'operands':i.op_str} for i in md.disasm(code,CODE_RAM)]
    result={'status':'development_poc','baseline_sha256':BASE_SHA,'output_sha256':sha(image),'output_size':len(image),'hook':{'address':hex(HOOK_RAM),'expected_16_bytes':expected.hex(),'written':hook.hex()},'code':{'address':hex(CODE_RAM),'length':len(code),'source':source,'disassembly':dis},'glyphs':[{'code':hex(c),'character':ch,'source_bios_offset':hex(o),'ram':hex(GLYPH_RAM+n*30),'sha256':sha(bios[o:o+30])} for n,(c,o,ch) in enumerate(GLYPHS)],'writes':writes,'touched_sectors':sector_audit,'raw_diff_sector_count':len(diff_sectors),'limitations':['Candidate zero region has no literal/direct instruction references in the surveyed executable, but full indirect/data consumer completeness is not established.','Local PoC embeds 90 bytes extracted from the supplied BIOS and is not a distributable artifact.','Runtime consumption is not established by this build.']}
    dump(ROOT/'docs/fq4/analysis/002/poc-build.json',result)
    print(json.dumps({'output_sha256':result['output_sha256'],'code_bytes':len(code),'sectors':diff_sectors,'writes':len(writes)},indent=2))

if __name__=='__main__': main()

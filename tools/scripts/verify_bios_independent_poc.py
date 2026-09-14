"""Artifact and isolated execution verification for the minimal FQ4 PoC."""
import hashlib, json, struct, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'work/fq4/python-deps'))
from capstone import Cs, CS_ARCH_MIPS, CS_MODE_MIPS32, CS_MODE_LITTLE_ENDIAN
from unicorn import Uc, UC_ARCH_MIPS, UC_MODE_MIPS32, UC_MODE_LITTLE_ENDIAN, UC_HOOK_CODE
from unicorn.mips_const import *
from survey_rom import Disc, save, sha

LOAD=0x80010000; HOOK=0x80082c8c; CONVERT=0x80046674; SENTINEL=0x801f0000
EXPECTED={'0x8952':0x800ecd00,'0x8eb5':0x800ecd1e,'0x917e':0x800ecd3c}

def main():
    report=json.loads((ROOT/'docs/fq4/analysis/002/poc-build.json').read_text(encoding='utf-8'))
    image=(ROOT/'work/fq4/rom/current.bin').read_bytes()
    if sha(image)!=report['output_sha256']: raise ValueError('PoC output identity mismatch')
    disc=Disc(ROOT/'work/fq4/rom/current.bin')
    rec=next(x for x in disc.files if x['path']=='/SLPS_006.04;1'); exe=disc.read(rec)
    if len(exe)!=1_075_200 or not exe.startswith(b'PS-X EXE'): raise ValueError('Executable structure mismatch')
    uc=Uc(UC_ARCH_MIPS,UC_MODE_MIPS32|UC_MODE_LITTLE_ENDIAN);uc.mem_map(0,0x200000)
    uc.mem_write(0x10000,exe[0x800:])
    results=[]
    for code,want in [(int(k,16),v) for k,v in EXPECTED.items()]:
        uc.reg_write(UC_MIPS_REG_A0,code);uc.reg_write(UC_MIPS_REG_RA,SENTINEL)
        uc.emu_start(HOOK,SENTINEL,count=200)
        got=uc.reg_read(UC_MIPS_REG_V0)&0xffffffff
        if got!=want: raise ValueError(f'Wrong glyph pointer {code:04x}: {got:08x}')
        # Run the game's unchanged 30-byte-to-4bpp converter from the returned address.
        dest=0x801e0000;uc.mem_write(0x1e0000,bytes(128));uc.reg_write(UC_MIPS_REG_A0,dest)
        uc.reg_write(UC_MIPS_REG_A1,got);uc.reg_write(UC_MIPS_REG_A2,0);uc.reg_write(UC_MIPS_REG_RA,SENTINEL)
        uc.emu_start(CONVERT,SENTINEL,count=10000)
        converted=bytes(uc.mem_read(0x1e0000,128))
        prior=next(x for x in json.loads((ROOT/'docs/fq4/analysis/001/glyph-probe.json').read_text(encoding='utf-8'))['results'] if int(x['code'],16)==code)
        if sha(converted)!=prior['converted_sha256']: raise ValueError('Converted glyph differs from supplied-BIOS baseline')
        results.append({'code':hex(code),'returned':hex(got),'converted_sha256':sha(converted),'matches_supplied_bios_baseline':True})
    # A non-PoC code must reach the original B0(51h) dispatch with its input intact.
    fallback=[]
    def on_code(mu,address,size,user):
        if address==0xb0:
            fallback.append({'pc':hex(address),'a0':hex(mu.reg_read(UC_MIPS_REG_A0)),'t1':hex(mu.reg_read(UC_MIPS_REG_T1)),'t2':hex(mu.reg_read(UC_MIPS_REG_T2))})
            mu.emu_stop()
    uc.hook_add(UC_HOOK_CODE,on_code);uc.reg_write(UC_MIPS_REG_A0,0x8140);uc.reg_write(UC_MIPS_REG_RA,SENTINEL)
    uc.emu_start(HOOK,SENTINEL,count=200)
    if fallback!=[{'pc':'0xb0','a0':'0x8140','t1':'0x51','t2':'0xb0'}]: raise ValueError(f'Fallback mismatch {fallback}')
    # Check the actual output disassembly, branch targets and delay slots.
    code_meta=report['code'];code_addr=int(code_meta['address'],16);code_len=code_meta['length']
    code=bytes(uc.mem_read(code_addr&0x1fffffff,code_len));md=Cs(CS_ARCH_MIPS,CS_MODE_MIPS32|CS_MODE_LITTLE_ENDIAN)
    ins=list(md.disasm(code,code_addr));
    if sum(i.mnemonic in ('beq','bne') for i in ins)!=3 or not any(i.mnemonic=='jr' and i.op_str=='$t2' for i in ins): raise ValueError('Final instruction structure mismatch')
    output={'artifact_sha256':sha(image),'evidence_class':'artifact verification and isolated MIPS execution; not game runtime','custom_results':results,'fallback':fallback,'instruction_count':len(ins),'instructions':[{'address':hex(i.address),'bytes':i.bytes.hex(),'mnemonic':i.mnemonic,'operands':i.op_str} for i in ins],'iso_file_records':len(disc.files),'disc_sectors':len(image)//2352,'limitations':['No normal BIOS was executed; fallback reached B0 dispatch with verified registers.','No GPU or game screen was consumed.']}
    save(ROOT/'docs/fq4/analysis/002/poc-verification.json',output)
    print(json.dumps({'custom_results':results,'fallback':fallback,'instructions':len(ins)},ensure_ascii=False,indent=2))

if __name__=='__main__':main()

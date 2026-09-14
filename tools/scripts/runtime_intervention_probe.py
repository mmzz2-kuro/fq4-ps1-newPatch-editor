"""Invoke the real FQ4 glyph upload path under DuckStation via GDB state intervention."""
import hashlib,json,struct,sys
from pathlib import Path
from gdb_runtime_probe import GDB
ROOT=Path(__file__).resolve().parents[2]
HOOK=0x80082c8c; RENDER=0x800464c0; LOADIMAGE=0x800845fc
CODES=[0x8952,0x8eb5,0x917e]
def u32(raw,n): return struct.unpack_from('<I',raw,n*4)[0]
def put(raw,n,value): struct.pack_into('<I',raw,n*4,value)
def sha(data): return hashlib.sha256(data).hexdigest()
def regs(g):
    packet=g.cmd('g');prefix=packet[:38*8]
    if any(c not in '0123456789abcdefABCDEF' for c in prefix):raise RuntimeError('Core register packet contains unavailable values')
    return bytearray.fromhex(prefix)
def setreg(g,n,value):
    reply=g.cmd(f'P{n:x}='+struct.pack('<I',value&0xffffffff).hex())
    if reply!='OK':raise RuntimeError(f'Register {n} write failed: {reply}')
def main():
    expected={int(x['code'],16):x['converted_sha256'] for x in json.loads((ROOT/'docs/fq4/analysis/001/glyph-probe.json').read_text(encoding='utf-8'))['results'] if 'converted_sha256' in x}
    g=GDB('127.0.0.1',2345);g.cmd('qSupported');g.cmd('?')
    saved=regs(g); original_pc=u32(saved,37); original_sp=u32(saved,29)
    scratch=(original_sp-0x500)&~0xf; source=bytes.fromhex('89528eb5917e00')
    saved_mem=bytes.fromhex(g.cmd(f'm{scratch:x},{len(source):x}'))
    if g.cmd(f'M{scratch:x},{len(source):x}:{source.hex()}')!='OK':raise RuntimeError('Scratch write failed')
    stops=[HOOK,LOADIMAGE,original_pc]
    for addr in stops:
        if g.cmd(f'Z0,{addr:x},4')!='OK':raise RuntimeError(f'Breakpoint failed {addr:x}')
    setreg(g,4,scratch);setreg(g,5,1);setreg(g,31,original_pc);setreg(g,37,RENDER)
    hooks=[];uploads=[];returned=False
    for _ in range(40):
        stop=g.cmd('c');current=regs(g);pc=u32(current,37)
        if pc==HOOK:
            hooks.append({'code':hex(u32(current,4)),'ra':hex(u32(current,31))})
        elif pc==LOADIMAGE:
            rect=u32(current,4);data=u32(current,5)
            rect_bytes=bytes.fromhex(g.cmd(f'm{rect:x},8')); glyph=bytes.fromhex(g.cmd(f'm{data:x},80'))
            code=CODES[len(uploads)] if len(uploads)<len(CODES) else None
            uploads.append({'code':hex(code) if code else None,'rect_pointer':hex(rect),'rect_xywh':list(struct.unpack('<4H',rect_bytes)),'data_pointer':hex(data),'data_sha256':sha(glyph),'matches_supplied_bios_conversion':bool(code and sha(glyph)==expected[code])})
        elif pc==original_pc:
            returned=True;break
        else: raise RuntimeError(f'Unexpected stop PC {pc:08x}, packet {stop}')
    # Restore the stopped CPU state and scratch RAM before resuming normal emulation.
    if g.cmd(f'M{scratch:x},{len(saved_mem):x}:{saved_mem.hex()}')!='OK':raise RuntimeError('Scratch restore failed')
    for n in list(range(1,35))+[37]:setreg(g,n,u32(saved,n))
    for addr in stops:g.cmd(f'z0,{addr:x},4')
    result={'evidence_class':'runtime after explicit CPU-state intervention; not normal-play reachability or screenshot evidence','baseline_pc':hex(original_pc),'scratch':hex(scratch),'input_codes':[hex(x) for x in CODES],'hook_events':hooks,'upload_events':uploads,'returned_to_baseline_pc':returned,'cpu_registers_and_scratch_restored':True,'global_and_gpu_state_restored':False,'pass':returned and [int(x['code'],16) for x in hooks]==CODES and len(uploads)==3 and all(x['matches_supplied_bios_conversion'] for x in uploads),'claim_limit':'Proves real game lookup, conversion, and LoadImage call under the selected normal BIOS. Does not prove final pixels were visible or normal-play route reachability.'}
    out=ROOT/'docs/fq4/analysis/002/runtime-intervention.json';out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()

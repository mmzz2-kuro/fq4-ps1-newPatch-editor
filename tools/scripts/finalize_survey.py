"""Reproduction verification without additional ROM copies and evidence summary."""
import collections
import json
import struct
import subprocess
from pathlib import Path
from survey_rom import Disc, save, sha
import hashlib
import platform
import sys
ROOT=Path(__file__).resolve().parents[2]

def main():
    out=ROOT/'docs/fq4/analysis/001'
    sys.path.insert(0,str(ROOT/'work/fq4/python-deps'))
    import capstone, unicorn, PIL
    save(out/'tool-environment.json',{'python':platform.python_version(),'capstone':capstone.__version__,'unicorn':unicorn.__version__,'Pillow':PIL.__version__,'xdelta':'3.0u'})
    manifest=json.loads((out/'inputs.json').read_text(encoding='utf-8'))
    checks=[]
    for row in manifest:
        p=ROOT/row['path']
        checks.append({'path':row['path'],'unchanged':p.stat().st_size==row['size'] and sha(p.read_bytes())==row['sha256']})
    assert all(x['unchanged'] for x in checks)
    save(out/'input-preservation.json', checks)
    orig=next((ROOT/'original').glob('*.bin'))
    patch_results=[]
    for patch in sorted((ROOT/'korean-patch').glob('*.xdelta')):
        command=[str(ROOT/'korean-patch/xdelta.exe'),'-d','-c','-s',str(orig),str(patch)]
        process=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        h=hashlib.sha256(); size=0
        while True:
            block=process.stdout.read(1024*1024)
            if not block: break
            h.update(block); size+=len(block)
        error=process.stderr.read().decode(errors='replace'); result=process.wait()
        assert result==0,error
        patch_results.append({'patch':patch.relative_to(ROOT).as_posix(),'output_sha256':h.hexdigest(),'size':size,'mode':'stdout streaming hash; no image output','exit_code':result})
    save(out/'patch-lineage.json',{'user_statement':'patched/ was made with 241112, not 250826 (2026-09-13)','reproductions':patch_results})
    exes={k:(ROOT/f'work/fq4/001/{k}/SLPS_006.04').read_bytes() for k in ('original','patched','reproduced')}
    begin,end=0x800464c0-0x80010000+2048,0x800467c8-0x80010000+2048
    sampleoff=0xe0158
    samples=[]
    for kind,data in exes.items():
        stop=data.index(0,sampleoff)
        raw=data[sampleoff:stop]
        tokens=[f'{int.from_bytes(raw[i:i+2],"big"):04X}' for i in range(0,len(raw),2)]
        assert b''.join(int(x,16).to_bytes(2,'big') for x in tokens)==raw
        samples.append({'kind':kind,'file_offset':hex(sampleoff),'ram':'0x800ef958','raw_hex':raw.hex(),'tokens':tokens,'terminator':'00','sample_roundtrip':True,'interpretation':'　交渉中・・・　' if kind=='original' else ' 교섭중... ','interpretation_basis':'cp932 for original; visually inspected BIOS glyphs for patched, not standard Korean encoding'})
    calls=[]
    for off in range(2048,len(exes['patched'])-3,4):
        w=struct.unpack_from('<I',exes['patched'],off)[0]
        if w>>26==3 and (0x80000000|((w&0x3ffffff)<<2))==0x800464c0:
            calls.append(hex(off-2048+0x80010000))
    save(out/'text-map.json',{'asset_id':'FQ4-TEXT-001','source':'/SLPS_006.04;1','consumer':'0x800464c0','bios_stub':'0x80082c8c','samples':samples,'population':{'status':'lower_bound','confirmed_representative_strings':1,'direct_call_candidates':len(calls),'call_sites':calls,'remaining':'All other strings, indirect callers, other rendering paths and graphics text unenumerated'},'renderer_identical_all_three':len({sha(x[begin:end]) for x in exes.values()})==1,'renderer_sha256':sha(exes['patched'][begin:end]),'display':{'glyph_input_bytes':30,'input_dimensions':[16,15],'converted_bytes':128,'output_dimensions':[16,16],'format':'4bpp; final row zero','upload_rectangle_words':[4,16],'initial_vram_xy':[512,416],'reset_mode_nominal_slots':192,'capacity_caveat':'Observed loop geometry only; aggregate append calls and other VRAM consumers not verified'}})
    original=Disc(orig); patched=Disc(next((ROOT/'patched').glob('*.bin')))
    changed=json.loads((out/'changed-sectors.json').read_text(encoding='utf-8'))
    owner={}
    for rec in original.files:
        for e in rec['extents']:
            for s in range(e['lba'],e['lba']+(e['size']+2047)//2048):
                owner.setdefault(s,[]).append(rec['path'])
    grouped=collections.Counter(); unowned=[]; formchanges=[]
    for r in changed:
        names=owner.get(r['sector'])
        if names: grouped['|'.join(names)]+=1
        else: unowned.append(r['sector'])
        i=r['sector']*2352
        if original.raw[i+18]&32 != patched.raw[i+18]&32:
            formchanges.append({'sector':r['sector'],'owner':names,'original_form':2 if original.raw[i+18]&32 else 1,'patched_form':2 if patched.raw[i+18]&32 else 1})
    summary={'changed_sector_owners':dict(grouped),'unowned_changed_sectors':unowned,'form_changes':formchanges,'load_end':hex(0x80010000+struct.unpack_from('<I',exes['original'],28)[0]),'workspace_roms':[p.relative_to(ROOT).as_posix() for p in (ROOT/'work').rglob('*.bin')],'input_preserved':all(x['unchanged'] for x in checks),'renderer_direct_call_candidates':len(calls)}
    save(out/'final-checks.json',summary)
    print(json.dumps({'lineage':patch_results,**summary},indent=2,ensure_ascii=False))

if __name__=='__main__': main()

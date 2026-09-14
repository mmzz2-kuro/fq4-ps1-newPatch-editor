#!/usr/bin/env python3
"""Find FQ4 font-sector fingerprints in live PS1 RAM through read-only GDB."""
from __future__ import annotations
import hashlib,json,time
from pathlib import Path
from gdb_runtime_probe import GDB
ROOT=Path(__file__).resolve().parents[2]
ROM=ROOT/'work/fq4/rom/current.bin'; OUT=ROOT/'docs/fq4/analysis/007/ram-placement.json'
DUMMY_LBA=24184; SECTORS=35
def read(g,a,n):
    out=bytearray()
    for p in range(0,n,0x1000):
        r=g.cmd(f'm{a+p:x},{min(0x1000,n-p):x}')
        if r.startswith('E'): raise RuntimeError(r)
        out.extend(bytes.fromhex(r))
    return bytes(out)
def all_hits(data,needle):
    hits=[];p=-1
    while True:
        p=data.find(needle,p+1)
        if p<0:return hits
        hits.append(hex(0x80000000+p))
def main():
    image=ROM.read_bytes(); payload=b''.join(image[(DUMMY_LBA+i)*2352+24:(DUMMY_LBA+i)*2352+2072] for i in range(SECTORS))
    deadline=time.time()+20
    while True:
        try:g=GDB('127.0.0.1',2345);break
        except OSError:
            if time.time()>deadline:raise
            time.sleep(.25)
    g.cmd('qSupported'); stop=g.cmd('?'); ram=read(g,0x80000000,0x200000)
    base=int.from_bytes(ram[0xecf40:0xecf44],'little');ready=int.from_bytes(ram[0xecf44:0xecf48],'little')
    patterns=[]
    for i in [0,1,2,17,33,34]:
        needle=payload[i*2048:i*2048+64]
        patterns.append({'sector_index':i,'lba':DUMMY_LBA+i,'fingerprint_sha256':hashlib.sha256(needle).hexdigest(),'hits':all_hits(ram,needle)})
    physical=base&0x1fffff
    result={'stop':stop,'font_base':hex(base),'font_ready':ready,'ram_sha256':hashlib.sha256(ram).hexdigest(),'patterns':patterns,'base_window_sha256':hashlib.sha256(ram[physical:physical+SECTORS*2048]).hexdigest()}
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result,indent=2))
if __name__=='__main__':main()

#!/usr/bin/env python3
"""Break at a loader boundary and hash the live FQ4 font allocation."""
import argparse,hashlib,json,time
from gdb_runtime_probe import GDB
def read(g,a,n):
    out=bytearray()
    while len(out)<n:
        c=min(0x1000,n-len(out)); r=g.cmd(f'm{a+len(out):x},{c:x}')
        if r.startswith('E'): raise RuntimeError(r)
        out.extend(bytes.fromhex(r))
    return bytes(out)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--address',type=lambda x:int(x,0),required=True);a=ap.parse_args()
    end=time.time()+20
    while True:
        try:g=GDB('127.0.0.1',2345);break
        except OSError:
            if time.time()>end:raise
            time.sleep(.2)
    g.cmd('qSupported');g.cmd('?');assert g.cmd(f'Z0,{a.address:x},4')=='OK';g.s.settimeout(30);stop=g.cmd('c')
    base=int.from_bytes(read(g,0x800ecf40,4),'little');ready=int.from_bytes(read(g,0x800ecf44,4),'little')
    data=read(g,base,70500); trailer=read(g,base+70500,16)
    print(json.dumps({'breakpoint':hex(a.address),'stop':stop,'base':hex(base),'ready':ready,'sha256':hashlib.sha256(data).hexdigest(),'head':data[:64].hex(),'trailer':trailer.hex()},indent=2))
if __name__=='__main__':main()

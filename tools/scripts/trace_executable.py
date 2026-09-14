"""Inspect explicit MIPS ranges and direct references; not CFG completeness."""
import argparse
import struct
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'work/fq4/python-deps'))
from capstone import Cs, CS_ARCH_MIPS, CS_MODE_MIPS32, CS_MODE_LITTLE_ENDIAN

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('address',type=lambda s:int(s,0))
    ap.add_argument('--size',type=lambda s:int(s,0),default=256)
    ap.add_argument('--refs',action='store_true')
    ap.add_argument('--kind',default='patched')
    ap.add_argument('--bios',action='store_true')
    args=ap.parse_args()
    data=(ROOT/'korean-patch/SCPH1001.BIN').read_bytes() if args.bios else (ROOT/f'work/fq4/001/{args.kind}/SLPS_006.04').read_bytes()
    md=Cs(CS_ARCH_MIPS,CS_MODE_MIPS32|CS_MODE_LITTLE_ENDIAN); md.skipdata=True
    def dump(addr,size):
        off=addr-0xbfc00000 if args.bios else addr-0x80010000+2048
        for i in md.disasm(data[off:off+size],addr):
            print(f'{i.address:08x} {i.bytes.hex()} {i.mnemonic} {i.op_str}')
    if args.refs:
        for off in range(2048,len(data)-3,4):
            w=struct.unpack_from('<I',data,off)[0]
            if (w>>26 in (2,3) and 0x80000000|((w&0x3ffffff)<<2)==args.address) or w==args.address:
                addr=off-2048+0x80010000
                print(f'REFERENCE {addr:08x}')
                dump(addr-32,96)
    else: dump(args.address,args.size)

if __name__=='__main__': main()

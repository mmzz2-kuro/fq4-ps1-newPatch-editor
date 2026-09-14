#!/usr/bin/env python3
import json,socket,struct,time
from gdb_runtime_probe import GDB
g=GDB('127.0.0.1',2345);g.cmd('qSupported');g.cmd('?');assert g.cmd('Z0,8008e1fc,4')=='OK';g.s.settimeout(30)
events=[]
for _ in range(80):
    try:stop=g.cmd('c')
    except socket.timeout:break
    raw=bytes.fromhex(g.cmd('g')[:256]);r=[struct.unpack_from('<I',raw,i*4)[0] for i in range(32)]
    e={'a0':hex(r[4]),'a1':hex(r[5]),'a2':hex(r[6]),'ra':hex(r[31])};events.append(e)
    if r[5]==35:break
print(json.dumps({'count':len(events),'last':events[-1] if events else None,'target_found':bool(events and events[-1]['a1']=='0x23')},indent=2))

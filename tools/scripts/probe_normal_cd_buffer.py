#!/usr/bin/env python3
import hashlib,json,socket,time
from pathlib import Path
from gdb_runtime_probe import GDB
ROOT=Path(__file__).resolve().parents[2];rom=(ROOT/'work/fq4/rom/current.bin').read_bytes()
end=time.time()+20
while True:
 try:g=GDB('127.0.0.1',2345);break
 except OSError:
  if time.time()>end:raise
  time.sleep(.2)
g.cmd('qSupported');g.cmd('?');assert g.cmd('Z0,8008efdc,4')=='OK';g.s.settimeout(30);stop=g.cmd('c')
r=g.cmd('m801179bc,800');buf=bytes.fromhex(r);expected=rom[166*2352+24:166*2352+2072]
print(json.dumps({'stop':stop,'buffer_sha256':hashlib.sha256(buf).hexdigest(),'expected_sha256':hashlib.sha256(expected).hexdigest(),'equal':buf==expected,'head':buf[:32].hex()},indent=2))

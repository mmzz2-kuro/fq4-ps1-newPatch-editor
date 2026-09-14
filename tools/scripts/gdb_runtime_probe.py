"""Small read-only GDB remote probe for DuckStation's local server."""
import argparse,collections,json,socket,struct,time

def checksum(data): return sum(data)&255
class GDB:
    def __init__(self,host,port):
        self.s=socket.create_connection((host,port),timeout=5);self.s.settimeout(5)
    def recv(self):
        while True:
            c=self.s.recv(1)
            if not c: raise EOFError
            if c==b'$': break
        data=bytearray()
        while True:
            c=self.s.recv(1)
            if c==b'#': break
            if c==b'}': c=bytes([self.s.recv(1)[0]^0x20])
            data.extend(c)
        got=int(self.s.recv(2),16)
        if checksum(data)!=got: self.s.sendall(b'-');raise ValueError('Bad packet checksum')
        self.s.sendall(b'+');return data.decode('ascii',errors='replace')
    def cmd(self,text):
        data=text.encode();self.s.sendall(b'$'+data+b'#'+f'{checksum(data):02x}'.encode())
        ack=self.s.recv(1)
        if ack!=b'+': raise ValueError(f'No ack: {ack!r}')
        return self.recv()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--address',type=lambda x:int(x,0),default=0x80082c8c);ap.add_argument('--wait',type=float,default=10);ap.add_argument('--collect',type=int,default=1);args=ap.parse_args()
    g=GDB('127.0.0.1',2345); supported=g.cmd('qSupported')
    initial=g.cmd('?'); added=g.cmd(f'Z0,{args.address:x},4')
    start=time.time();events=[];deadline=start+args.wait
    while len(events)<args.collect and time.time()<deadline:
        g.s.settimeout(max(.1,deadline-time.time()))
        try: stopped=g.cmd('c')
        except socket.timeout: break
        regs=g.cmd('g'); raw=bytes.fromhex(regs[:256])
        gprs=[struct.unpack_from('<I',raw,i*4)[0] for i in range(32)]
        events.append({'stop':stopped,'a0':hex(gprs[4]),'a1':hex(gprs[5]),'a2':hex(gprs[6]),'a3':hex(gprs[7]),'v0':hex(gprs[2]),'ra':hex(gprs[31]),'sp':hex(gprs[29])})
    result={'supported':supported,'initial_stop':initial,'breakpoint':hex(args.address),'breakpoint_reply':added,'events':events,'a0_counts':dict(collections.Counter(x['a0'] for x in events)),'custom_hits':[x for x in events if x['a0'] in ('0x8952','0x8eb5','0x917e')],'wait_seconds':round(time.time()-start,3)}
    if events:
        result['remove_reply']=g.cmd(f'z0,{args.address:x},4')
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()

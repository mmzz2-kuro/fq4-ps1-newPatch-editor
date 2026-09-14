"""Read-only FQ4 survey; source-derived files stay in work/. Python 3.10+."""
import argparse
import csv
import hashlib
import json
import platform
import struct
from pathlib import Path

def sha(data):
    return hashlib.sha256(data).hexdigest()

def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')

class Disc:
    def __init__(self, path):
        self.raw = path.read_bytes()
        if len(self.raw) % 2352:
            raise ValueError('Nonintegral raw sectors')
        self.forms = {}
        for i in range(0, len(self.raw), 2352):
            sector = self.raw[i:i+2352]
            if sector[:12] != b'\x00' + b'\xff'*10 + b'\x00' or sector[15] != 2:
                raise ValueError(f'Unexpected sector at {i}')
            if sector[16:20] != sector[20:24]:
                raise ValueError(f'Subheader mismatch at {i}')
            form = 2 if sector[18] & 32 else 1
            self.forms[form] = self.forms.get(form, 0) + 1
        self.pvd = self.sector(16)
        assert self.pvd[:7] == b'\x01CD001\x01'
        assert struct.unpack_from('<H', self.pvd, 128)[0] == 2048
        self.files = []
        self.walk(self.record(self.pvd[156:190]), '')

    def sector(self, lba):
        start = lba*2352
        s = self.raw[start:start+2352]
        if len(s) != 2352 or s[18] & 32:
            raise ValueError(f'ISO requests non-Form1 sector {lba}')
        return s[24:2072]

    def extent(self, lba, size):
        return b''.join(self.sector(lba+i) for i in range((size+2047)//2048))[:size]

    @staticmethod
    def record(b):
        lba, size = struct.unpack_from('<I', b, 2)[0], struct.unpack_from('<I', b, 10)[0]
        assert lba == struct.unpack_from('>I', b, 6)[0]
        assert size == struct.unpack_from('>I', b, 14)[0]
        return {'lba': lba, 'size': size, 'flags': b[25], 'name': b[33:33+b[32]].decode('ascii')}

    def walk(self, directory, prefix):
        data = self.extent(directory['lba'], directory['size'])
        pos, pending = 0, None
        while pos < len(data):
            length = data[pos]
            if not length:
                pos = (pos//2048+1)*2048
                continue
            rec = self.record(data[pos:pos+length]); pos += length
            if rec['name'] in ('\x00', '\x01'):
                continue
            name = prefix + '/' + rec['name']
            if rec['flags'] & 2:
                self.walk(rec, name)
                continue
            if pending is None:
                pending = {'path': name, 'extents': [], 'size': 0}
            assert pending['path'] == name
            pending['extents'].append({'lba': rec['lba'], 'size': rec['size']})
            pending['size'] += rec['size']
            if not rec['flags'] & 128:
                is_xa = any(self.raw[(e['lba']+i)*2352+18] & 32 for e in pending['extents'] for i in range((e['size']+2047)//2048))
                pending['hash_basis'] = 'raw_extent_sectors' if is_xa else 'logical_file_bytes'
                pending['sha256'] = sha(b''.join(self.raw[e['lba']*2352:(e['lba']+(e['size']+2047)//2048)*2352] for e in pending['extents'])) if is_xa else sha(self.read(pending))
                self.files.append(pending); pending = None
        assert pending is None

    def read(self, rec):
        return b''.join(self.extent(e['lba'], e['size']) for e in rec['extents'])

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
    args = ap.parse_args(); root = args.root.resolve()
    out = root/'docs/fq4/analysis/001'; out.mkdir(parents=True, exist_ok=True)
    manifest = []
    for folder in ('original', 'patched', 'korean-patch'):
        for p in sorted((root/folder).rglob('*')):
            if p.is_file():
                manifest.append({'path': p.relative_to(root).as_posix(), 'size': p.stat().st_size, 'sha256': sha(p.read_bytes())})
    baseline = out/'inputs.json'
    if baseline.exists():
        assert json.loads(baseline.read_text(encoding='utf-8')) == manifest, 'Input changed'
    else:
        save(baseline, manifest)
    discs = {kind: Disc(next((root/kind).glob('*.bin'))) for kind in ('original', 'patched')}
    structures = {}
    for kind, d in discs.items():
        save(out/f'{kind}-files.json', d.files)
        exes = []
        for rec in d.files:
            if rec['hash_basis'] != 'logical_file_bytes':
                continue
            data = d.read(rec)
            if data.startswith(b'PS-X EXE') or rec['path'].upper().endswith('SYSTEM.CNF;1'):
                p = root/'work/fq4/001'/kind/rec['path'].lstrip('/').replace(';1', '')
                p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(data)
                if data.startswith(b'PS-X EXE'):
                    exes.append({'path':rec['path'], 'pc':hex(struct.unpack_from('<I',data,16)[0]), 'load':hex(struct.unpack_from('<I',data,24)[0]), 'load_size':struct.unpack_from('<I',data,28)[0]})
                else:
                    exes.append({'path':rec['path'], 'text':data.decode('ascii',errors='replace')})
        structures[kind] = {'sectors':len(d.raw)//2352, 'forms':d.forms, 'volume_id':d.pvd[40:72].decode('ascii').strip(), 'volume_blocks':struct.unpack_from('<I',d.pvd,80)[0], 'files':len(d.files), 'boot':exes}
    a,b = discs['original'],discs['patched']; assert len(a.raw)==len(b.raw)
    changed_sectors, changed_bytes, ranges, begin = [], 0, [], None
    with (out/'diff-ranges.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.writer(f); writer.writerow(['raw_start','length'])
        for s in range(len(a.raw)//2352):
            x,y=a.raw[s*2352:(s+1)*2352],b.raw[s*2352:(s+1)*2352]
            if x==y:
                if begin is not None: writer.writerow([begin,s*2352-begin]); begin=None
                continue
            counts={'header':0,'payload':0,'tail':0}
            for j,(u,v) in enumerate(zip(x,y)):
                pos=s*2352+j
                if u!=v:
                    changed_bytes+=1
                    counts['header' if j<24 else 'payload' if j<2072 else 'tail']+=1
                    if begin is None: begin=pos
                elif begin is not None:
                    writer.writerow([begin,pos-begin]); begin=None
            changed_sectors.append({'sector':s,**counts})
        if begin is not None: writer.writerow([begin,len(a.raw)-begin])
    save(out/'changed-sectors.json',changed_sectors)
    left={r['path']:r for r in a.files}; right={r['path']:r for r in b.files}; differences=[]
    for name in sorted(left.keys()|right.keys()):
        x,y=left.get(name),right.get(name)
        if x!=y:
            differences.append({'path':name,'original':x,'patched':y,'content_changed':not x or not y or x['sha256']!=y['sha256']})
    save(out/'file-differences.json', differences)
    result={'python':platform.python_version(),'structures':structures,'changed_bytes':changed_bytes,'changed_sectors':len(changed_sectors),'changed_files':len(differences)}
    save(out/'survey.json',result)
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':
    main()

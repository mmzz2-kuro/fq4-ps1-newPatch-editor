#!/usr/bin/env python3
"""Extract the first real 32x32 indexed frame from FQ4 Cxx.P class files."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]; DISC=ROOT/'original'/'First Queen IV - Varcia Senki (Japan).bin'
MANIFEST=ROOT/'docs/fq4/analysis/001/original-files.json'; UI=ROOT/'tools/FQ4SaveEditor'; OUT=UI/'class_icons'

def ramp(v, a, b, lo, hi):
    q=max(0,min(1,(v-lo)/max(1,hi-lo)))
    return tuple(int(x+(y-x)*q) for x,y in zip(a,b))+(255,)

def rgba(v):
    if v==0:return (0,0,0,0)
    if v==3:return (5,8,18,255)
    if 1<=v<=15:return ramp(v,(35,38,45),(248,248,242),1,15)
    if 40<=v<=55:return ramp(v,(65,5,5),(225,35,20),40,55)
    if 56<=v<=63:return ramp(v,(105,35,0),(255,205,35),56,63)
    if 64<=v<=79:return ramp(v,(55,58,65),(245,245,238),64,79)
    if 96<=v<=127:return ramp(v,(105,45,0),(255,215,45),96,127)
    return (100,100,105,255)

def main():
    raw=DISC.read_bytes(); files=json.loads(MANIFEST.read_text(encoding='utf-8')); by={x['path'].split(';')[0]:x for x in files}
    names=json.loads((UI/'class_names.json').read_text(encoding='utf-8'));OUT.mkdir(parents=True,exist_ok=True);catalog=[]
    for i,name in enumerate(names):
        path=f'/CHR{i>>4:X}/C{i:02X}.P'; rec=by[path]; e=rec['extents'][0]; data=b''.join(raw[(e['lba']+n)*2352+24:(e['lba']+n)*2352+2072] for n in range((e['size']+2047)//2048))[:e['size']]
        base_tile=16 if len(data)>=20*256 else 0
        tile_ids=(base_tile,base_tile+1,base_tile+2,base_tile+3); indices=[]
        for y in range(32):
            for x in range(32):
                tile=((tile_ids[0],tile_ids[2]),(tile_ids[1],tile_ids[3]))[y//16][x//16]
                indices.append(data[tile*256+(y%16)*16+(x%16)])
        frame=bytes(indices); im=Image.new('RGBA',(32,32));im.putdata([rgba(x) for x in frame]);im=im.resize((64,64),Image.Resampling.NEAREST)
        fn=f'class-{i:03}.png';im.save(OUT/fn)
        catalog.append({'id':i,'name':name,'icon':f'class_icons/{fn}','image_status':'user_approved_front_frame_normalized_palette' if base_tile==16 else 'compact_resource_first_frame_normalized_palette','source':path,'source_lba':e['lba'],'tile_positions':{'top_left':tile_ids[0],'bottom_left':tile_ids[1],'top_right':tile_ids[2],'bottom_right':tile_ids[3]},'palette':'normalized groups approved from CLASS 25 preview v1','frame_sha256':hashlib.sha256(frame).hexdigest()})
    (UI/'class_catalog.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print('extracted',len(catalog))
if __name__=='__main__':main()

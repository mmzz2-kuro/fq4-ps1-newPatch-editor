#!/usr/bin/env python3
"""Extract fixed-size preview icons from FQ4 Cxx.P class files."""
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

def tile_offset(tile_x, tile_y, width_tiles, height_tiles, column_major):
    if column_major:
        return tile_x*height_tiles+tile_y
    return tile_y*width_tiles+tile_x

def render_frame(data, base_tile, width_tiles, height_tiles, column_major=False):
    indices=[]
    for y in range(height_tiles*16):
        for x in range(width_tiles*16):
            tile=base_tile+tile_offset(x//16,y//16,width_tiles,height_tiles,column_major)
            indices.append(data[tile*256+(y%16)*16+(x%16)])
    frame=bytes(indices); im=Image.new('RGBA',(width_tiles*16,height_tiles*16));im.putdata([rgba(x) for x in frame])
    return frame,im

def fit_large_icon(im):
    bbox=im.getbbox()
    if bbox:
        im=im.crop(bbox)
    if im.width>64 or im.height>64:
        scale=min(64/im.width,64/im.height)
        im=im.resize((max(1,int(im.width*scale)),max(1,int(im.height*scale))),Image.Resampling.NEAREST)
    canvas=Image.new('RGBA',(64,64),(0,0,0,0))
    canvas.alpha_composite(im,((64-im.width)//2,(64-im.height)//2))
    return canvas

def layout(class_id,data):
    tiles=len(data)//256
    if class_id==217:
        return 0,6,6,True,'large_front_frame_96x96_column_major_fit64_normalized_palette'
    if class_id==218:
        return 0,8,8,True,'large_front_frame_128x128_column_major_fit64_normalized_palette'
    if 211<=class_id<=216:
        return 64,4,4,True,'large_front_frame_64x64_column_major_normalized_palette'
    if tiles>=72 and tiles%9==0:
        return 36,3,3,True,'large_front_frame_48x48_column_major_normalized_palette'
    if tiles>=20:
        return 16,2,2,True,'front_frame_32x32_column_major_normalized_palette'
    return 0,2,2,True,'compact_resource_first_frame_column_major_normalized_palette'

def main():
    raw=DISC.read_bytes(); files=json.loads(MANIFEST.read_text(encoding='utf-8')); by={x['path'].split(';')[0]:x for x in files}
    names=json.loads((UI/'class_names.json').read_text(encoding='utf-8-sig'));OUT.mkdir(parents=True,exist_ok=True);catalog=[]
    for i,name in enumerate(names):
        path=f'/CHR{i>>4:X}/C{i:02X}.P'; rec=by[path]; e=rec['extents'][0]; data=b''.join(raw[(e['lba']+n)*2352+24:(e['lba']+n)*2352+2072] for n in range((e['size']+2047)//2048))[:e['size']]
        base_tile,width_tiles,height_tiles,column_major,status=layout(i,data)
        frame,im=render_frame(data,base_tile,width_tiles,height_tiles,column_major)
        im=fit_large_icon(im) if width_tiles>=3 and height_tiles>=3 else im.resize((64,64),Image.Resampling.NEAREST)
        fn=f'class-{i:03}.png';im.save(OUT/fn)
        catalog.append({'id':i,'name':name,'icon':f'class_icons/{fn}','image_status':status,'source':path,'source_lba':e['lba'],'tile_layout':{'base_tile':base_tile,'width_tiles':width_tiles,'height_tiles':height_tiles,'column_major':column_major,'tile_count':len(data)//256},'palette':'normalized groups approved from CLASS 25 preview v1','frame_sha256':hashlib.sha256(frame).hexdigest()})
    (UI/'class_catalog.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print('extracted',len(catalog))
if __name__=='__main__':main()

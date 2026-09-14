#!/usr/bin/env python3
from __future__ import annotations
import json,sys
from pathlib import Path
from PIL import Image,ImageDraw

ROOT=Path(__file__).resolve().parents[2]; ui=ROOT/'tools/FQ4SaveEditor'; out=ui/'class_icons'; out.mkdir(parents=True,exist_ok=True)
names=json.loads((ui/'class_names.json').read_text(encoding='utf-8')); catalog=[]
for i,name in enumerate(names):
    # Clearly marked placeholder; never represented as an extracted game sprite.
    im=Image.new('RGBA',(40,40),(30+(i*37)%100,45+(i*53)%100,75+(i*29)%100,255)); d=ImageDraw.Draw(im)
    d.rectangle((1,1,38,38),outline=(120,220,255,255),width=2); d.text((7,13),f'{i:03}',fill='white')
    fn=f'class-{i:03}.png'; im.save(out/fn)
    catalog.append({'id':i,'name':name,'icon':f'class_icons/{fn}','image_status':'placeholder','source':None})
(ui/'class_catalog.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('generated',len(catalog),'explicit placeholders')

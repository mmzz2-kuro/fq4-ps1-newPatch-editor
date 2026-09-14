from __future__ import annotations
import json, os
from pathlib import Path

FIELDS=("hr","hp","at","ar","df","dr","level","ft","class_id")
LIMITS={"hr":(1,16),"hp":(1,999),"at":(1,99),"ar":(1,99),"df":(1,99),"dr":(1,99),"level":(0,255),"ft":(0,65535),"class_id":(0,219)}

def config_path():
    root=Path(os.environ.get("APPDATA",Path.home()))/"FQ4SaveEditor"
    return root/"presets.json"

def validate(p):
    if not isinstance(p,dict) or not str(p.get("name","")).strip(): raise ValueError("프리셋 이름이 필요합니다.")
    out={"name":str(p["name"]).strip()}
    for k in FIELDS:
        if k not in p or p[k] is None: continue
        v=int(p[k]); lo,hi=LIMITS[k]
        if not lo<=v<=hi: raise ValueError(f"{k}: {lo}~{hi} 범위여야 합니다.")
        out[k]=v
    if not any(k in out for k in FIELDS): raise ValueError("적용할 값이 없습니다.")
    return out

def load(path=None):
    path=Path(path or config_path())
    if not path.exists(): return []
    try:return [validate(x) for x in json.loads(path.read_text(encoding="utf-8"))]
    except Exception:
        bad=path.with_suffix(".invalid.json"); path.replace(bad); return []

def save(items,path=None):
    path=Path(path or config_path()); path.parent.mkdir(parents=True,exist_ok=True)
    data=[validate(x) for x in items]; tmp=path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"); os.replace(tmp,path)

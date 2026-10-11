"""Losslessly omit regenerable Sobol points and restore exact JSONL bytes."""
import argparse
import base64
import gzip
import hashlib
import json
from pathlib import Path
import numpy as np
from .engineering_optimization_transfer import CONFIG, ROOT, seed, sobol, write_json

DATA = ROOT / "data/engineering_optimization_transfer_v1"


def restore_case(records, cfg):
    meta=records[0];c,rep=meta["condition"],meta["repeat"]
    initial=sobol(6,seed(cfg,c,rep,11))[:58]
    histories={}
    pending=None
    for row in records:
        if row["event"]=="pre":
            if row["phase"]=="initial":x=initial[row["t"]-1]
            else:
                key=row["workflow"],row["phase"],row["policy"]
                history=histories.setdefault(key,list(initial.copy()))
                pool=sobol(cfg["pool_power"],row["pool_seed"])
                observed={a.tobytes() for a in history}
                pool=np.array([a for a in pool if a.tobytes() not in observed])
                x=pool[row["pool_index"]]
            row["x"]=x.tolist();pending=(row,x)
        elif row["event"]=="label":
            pre,x=pending;assert pre["call_id"]==row["call_id"]
            if pre["phase"]!="initial":histories[pre["workflow"],pre["phase"],pre["policy"]].append(x)
            pending=None
    return ("".join(json.dumps(r,separators=(",",":"))+"\n" for r in records)).encode()


def pack():
    cfg=json.loads(CONFIG.read_text()); out=ROOT/cfg["out"]
    DATA.mkdir(parents=True,exist_ok=True)
    archive={"config":cfg,"cases":[]};files=[]
    for folder in sorted(out.glob("load*_r*")):
        raw=(folder/"events.jsonl").read_bytes();records=[json.loads(l) for l in raw.splitlines()]
        for row in records:
            if row["event"]=="pre":row["x"]=None
        restored=restore_case(json.loads(json.dumps(records)),cfg)
        assert restored==raw,"Sobol codec is not lossless"
        archive["cases"].append({"case":folder.name,"records":records,
                                "summary":json.loads((folder/"summary.json").read_text())})
        files.append({"case":folder.name,"journal_sha256":hashlib.sha256(raw).hexdigest(),
                      "summary_sha256":hashlib.sha256((folder/"summary.json").read_bytes()).hexdigest()})
    payload=json.dumps(archive,separators=(",",":")).encode()
    packed=gzip.compress(payload,compresslevel=9,mtime=0);text=base64.b85encode(packed).decode()
    parts=[]
    for i,start in enumerate(range(0,len(text),12000)):
        p=DATA/f"records-{i:03d}.b85";chunk=text[start:start+12000];p.write_text(chunk)
        parts.append({"path":p.name,"sha256":hashlib.sha256(chunk.encode()).hexdigest()})
    manifest={"codec":"gzip+base85; Sobol point regeneration; exact original JSONL byte reconstruction",
              "payload_sha256":hashlib.sha256(payload).hexdigest(),"packed_sha256":hashlib.sha256(packed).hexdigest(),
              "parts":parts,"files":files,"cases":20,"retained_physical_calls":18120,
              "recovery_calls_are_separate":True,"config_sha256":hashlib.sha256(CONFIG.read_bytes()).hexdigest()}
    write_json(DATA/"manifest.json",manifest)
    return {"parts":len(parts),"packed_bytes":len(packed),"all_original_journals_reconstructed_exactly":True}


def restore(data=DATA, target=None):
    manifest=json.loads((data/"manifest.json").read_text())
    parts=[]
    for part in manifest["parts"]:
        b=(data/part["path"]).read_bytes();assert hashlib.sha256(b).hexdigest()==part["sha256"];parts.append(b)
    packed=base64.b85decode(b"".join(parts));assert hashlib.sha256(packed).hexdigest()==manifest["packed_sha256"]
    payload=gzip.decompress(packed);assert hashlib.sha256(payload).hexdigest()==manifest["payload_sha256"]
    archive=json.loads(payload);cfg=archive["config"]
    target=target or ROOT/cfg["out"]
    expected={f["case"]:f for f in manifest["files"]}
    for case in archive["cases"]:
        raw=restore_case(case["records"],cfg);assert hashlib.sha256(raw).hexdigest()==expected[case["case"]]["journal_sha256"]
        folder=target/case["case"];folder.mkdir(parents=True,exist_ok=True)
        for name,b in [("events.jsonl",raw),("summary.json",(json.dumps(case["summary"],indent=2)+"\n").encode())]:
            p=folder/name
            if p.exists() and p.read_bytes()!=b:raise FileExistsError("Refusing conflicting scientific record: "+str(p))
            p.write_bytes(b)
    write_json(target/"run_status.json",{"complete":True,"cases_completed":20,"restored_from_curated_release":True,"config":cfg})
    return {"restored_cases":20,"new_finite_element_calls":0}


if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--pack",action="store_true");args=parser.parse_args()
    print(json.dumps(pack() if args.pack else restore()))

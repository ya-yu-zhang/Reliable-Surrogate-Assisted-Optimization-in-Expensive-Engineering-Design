import hashlib,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];DEST=ROOT/"docs/frozen_final_semantic_consistency_v1"
FILES=["src/revise_final_semantic_consistency.py","src/finish_final_semantic_consistency.py","tests/test_final_semantic_consistency.py"]
def main():
 assert not DEST.exists();DEST.mkdir();rows={}
 for n in FILES:
  s=ROOT/n;t=DEST/n;t.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(s,t);rows[n]=hashlib.sha256(s.read_bytes()).hexdigest()
 (DEST/"sha256.json").write_text(json.dumps(rows,indent=2),encoding="utf-8")
if __name__=="__main__":main()

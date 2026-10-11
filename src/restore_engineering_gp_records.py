"""Verify the curated raw archive before restoring original result paths."""
import hashlib
import json
from pathlib import Path, PurePosixPath
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/engineering_optimization_gp_audit_v1"


def restore(root=ROOT, data=DATA):
    root, data = Path(root), Path(data)
    archive = data / "source_records.zip"
    manifest = json.loads((data / "source_integrity.json").read_text())
    sha = lambda b: hashlib.sha256(b).hexdigest()
    if (data / "source_bundle_manifest.json").exists():
        from .compact_engineering_gp_sources import unpack
        records = unpack(data)
        distribution = "checksum-verified lossless text bundle"
    else:
        if sha(archive.read_bytes()) != manifest["archive_sha256"]:
            raise ValueError("Source archive checksum mismatch")
        with zipfile.ZipFile(archive) as z:
            records = {item["path"]: z.read("engineering_gp_cross_mechanism_v1/" + item["path"])
                       for item in manifest["files"]}
        distribution = "original checksum-verified ZIP"
    pending = []
    for item in manifest["files"]:
        name = PurePosixPath(item["path"])
        if name.is_absolute() or ".." in name.parts or len(name.parts) != 3:
            raise ValueError("Invalid archive path")
        method = name.parts[0]
        directories = {"gp_ei_shared_init": "engineering_beam_shared_init_v1",
                       "gp_pi_shared_init": "engineering_beam_acquisition_refs_v1",
                       "gp_ucb_shared_init": "engineering_beam_acquisition_refs_v1"}
        payload = records[str(name)]
        if sha(payload) != item["sha256"]:
            raise ValueError("Raw file checksum mismatch")
        target = root / "results" / directories[method] / str(name)
        if target.exists() and target.read_bytes() != payload:
            raise FileExistsError(f"Conflicting existing file: {target}")
        pending.append((target, payload))
    if len(pending) != 60 or len({p for p, _ in pending}) != 60:
        raise ValueError("Expected exactly 60 distinct raw files")
    for target, payload in pending:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)
    return {"verified_and_restored": len(pending), "archive_sha256": manifest["archive_sha256"],
            "distribution": distribution, "new_objective_calls": 0}


if __name__ == "__main__":
    print(json.dumps(restore(), indent=2))

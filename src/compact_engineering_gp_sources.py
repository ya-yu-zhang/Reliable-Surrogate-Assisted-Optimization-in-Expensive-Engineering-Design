"""Package the 60 supplied GP files as a byte-preserving UTF-8 release.

The distribution format differs from the supplied ZIP. Its manifest retains
the supplied archive identity and every original per-file checksum. No labels
are recomputed and no line endings or JSON numbers are changed.
"""
import base64
import hashlib
import json
import lzma
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/engineering_optimization_gp_audit_v1"


def sha(payload):
    return hashlib.sha256(payload).hexdigest()


def pack(data=DATA):
    integrity = json.loads((data / "source_integrity.json").read_text())
    archive = data / "source_records.zip"
    assert sha(archive.read_bytes()) == integrity["archive_sha256"]
    records = []
    with zipfile.ZipFile(archive) as z:
        for item in integrity["files"]:
            raw = z.read("engineering_gp_cross_mechanism_v1/" + item["path"])
            assert sha(raw) == item["sha256"]
            text = raw.decode("utf-8")
            assert text.encode("utf-8") == raw
            records.append({"path": item["path"], "utf8": text})
    payload = json.dumps({"original_archive_sha256": integrity["archive_sha256"],
                          "files": records}, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    packed = lzma.compress(payload, preset=9)
    encoded = base64.b85encode(packed).decode("ascii")
    parts = []
    for number, start in enumerate(range(0, len(encoded), 12000)):
        name = f"source_records-{number:03d}.b85"
        raw = (encoded[start:start + 12000] + "\n").encode("ascii")
        (data / name).write_bytes(raw)
        parts.append({"path": name, "sha256": sha(raw), "bytes": len(raw)})
    manifest = {"schema": 1, "format": "lzma-base85-utf8-byte-preserving-files",
                "source_integrity_sha256": sha((data / "source_integrity.json").read_bytes()),
                "original_archive_sha256": integrity["archive_sha256"], "file_count": len(records),
                "payload_sha256": sha(payload), "packed_sha256": sha(packed),
                "payload_bytes": len(payload), "packed_bytes": len(packed), "parts": parts}
    (data / "source_bundle_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    decoded = unpack(data)
    assert all(sha(decoded[item["path"]]) == item["sha256"] for item in integrity["files"])
    return {"files": len(decoded), "parts": len(parts), "packed_bytes": len(packed), "new_objective_calls": 0}


def unpack(data=DATA):
    manifest = json.loads((data / "source_bundle_manifest.json").read_text())
    integrity = json.loads((data / "source_integrity.json").read_text())
    assert manifest["schema"] == 1
    assert manifest["source_integrity_sha256"] == sha((data / "source_integrity.json").read_bytes())
    assert manifest["original_archive_sha256"] == integrity["archive_sha256"]
    encoded = []
    for part in manifest["parts"]:
        name = part["path"]
        assert Path(name).name == name and name.startswith("source_records-") and name.endswith(".b85")
        raw = (data / name).read_bytes()
        assert len(raw) == part["bytes"] and sha(raw) == part["sha256"]
        encoded.append(raw.decode("ascii").strip())
    packed = base64.b85decode("".join(encoded).encode("ascii"))
    assert len(packed) == manifest["packed_bytes"] and sha(packed) == manifest["packed_sha256"]
    payload = lzma.decompress(packed)
    assert len(payload) == manifest["payload_bytes"] and sha(payload) == manifest["payload_sha256"]
    bundle = json.loads(payload)
    assert bundle["original_archive_sha256"] == integrity["archive_sha256"]
    records = {item["path"]: item["utf8"].encode("utf-8") for item in bundle["files"]}
    assert len(bundle["files"]) == len(records) == manifest["file_count"] == 60
    assert set(records) == {item["path"] for item in integrity["files"]}
    assert all(sha(records[item["path"]]) == item["sha256"] for item in integrity["files"])
    return records


if __name__ == "__main__":
    print(json.dumps(pack(), indent=2))

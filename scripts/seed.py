"""Version-pinned, exclusive-owner distributor for the fixed V2 seed."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "seed"))
from core import ContractError, VERSION, encode, file_hash, local, no_links, require


def load():
    manifest = json.loads((ROOT / "seed-manifest.json").read_text(encoding="utf-8"))
    require(manifest["schema"] == 2 and manifest["distribution_version"] == VERSION, "incompatible distribution")
    expected = manifest["files"]
    actual = {p.relative_to(ROOT / "seed").as_posix() for p in (ROOT / "seed").rglob("*") if p.is_file() and "__pycache__" not in p.parts}
    require(set(expected) == actual, "payload inventory mismatch")
    require(len({p.casefold() for p in expected}) == len(expected), "case collision")
    payload = {}
    for name, sha in expected.items():
        path = local(ROOT / "seed", name)
        require(file_hash(path) == sha, "payload digest mismatch: " + name)
        payload[name] = path.read_bytes()
    receipt = {"schema": 2, "version": VERSION, "manifest_sha256": file_hash(ROOT / "seed-manifest.json"), "files": expected}
    return manifest, payload, receipt


def install(target, payload, receipt, dry=False):
    target = Path(target).absolute()
    no_links(target)
    require(not target.is_relative_to(ROOT) and not ROOT.is_relative_to(target), "install outside seed source")
    receipt_path = target / ".harness-seed.json"
    pending = target / ".harness-seed.pending.json"
    require(not pending.exists(), "partial installation; preserve marker and install into a fresh directory")
    if receipt_path.exists():
        require(json.loads(receipt_path.read_text(encoding="utf-8")) == receipt, "different installed release; no in-place migration")
        require(all(local(target, name).is_file() and file_hash(local(target, name)) == sha for name, sha in receipt["files"].items()), "installed core/docs drift")
        return {"state": "unchanged", "version": VERSION}
    require(not (target / ".harness").exists(), "existing runtime requires isolated adoption")
    require(not (target / "wiki").exists(), "wiki ownership conflict; use a fresh directory")
    for name in payload:
        require(not local(target, name).exists(), "existing project file: " + name)
    if dry:
        return {"state": "planned", "files": sorted(payload), "wiki": "auto_object_draft"}
    target.mkdir(parents=True, exist_ok=True)
    with pending.open("x", encoding="utf-8") as out:
        out.write(encode(receipt))
    for name, data in payload.items():
        path = local(target, name)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as out:
            out.write(data)
    from core import Kernel
    from wiki import render
    wiki = render(Kernel(target))
    with receipt_path.open("x", encoding="utf-8") as out:
        out.write(encode(receipt) + "\n")
    pending.unlink()
    return {"state": "installed", "version": VERSION, "wiki": wiki["wiki"], "readiness": "unverified"}


def package(payload, receipt):
    from core import Kernel
    from wiki import render
    with tempfile.TemporaryDirectory() as tmp:
        render(Kernel(tmp))
        draft = {"wiki/" + p.name: p.read_bytes() for p in (Path(tmp) / "wiki").iterdir() if p.is_file()}
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_STORED) as z:
        for name, data in sorted({**payload, **draft, ".harness-seed.json": (encode(receipt) + "\n").encode()}.items()):
            info = zipfile.ZipInfo(name, date_time=(2026, 9, 16, 0, 0, 0))
            info.external_attr = 0o100644 << 16
            z.writestr(info, data)
    return buf.getvalue()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("check")
    i = sub.add_parser("init")
    i.add_argument("--target", type=Path, required=True)
    i.add_argument("--dry-run", action="store_true")
    b = sub.add_parser("pack")
    b.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    try:
        manifest, payload, receipt = load()
        if a.command == "check":
            result = {"state": "checked", "version": VERSION, "files": len(payload), "manifest": receipt["manifest_sha256"]}
        elif a.command == "init":
            result = install(a.target, payload, receipt, a.dry_run)
        else:
            no_links(a.out)
            data = package(payload, receipt)
            if a.out.exists():
                require(a.out.read_bytes() == data, "package destination conflict")
            else:
                a.out.parent.mkdir(parents=True, exist_ok=True)
                with a.out.open("xb") as out:
                    out.write(data)
            result = {"state": "packed", "sha256": hashlib.sha256(data).hexdigest(), "path": str(a.out)}
        print(encode(result))
        return 0
    except (OSError, ValueError, KeyError, ContractError) as exc:
        print(encode({"state": "error", "reason": str(exc)}))
        return 2


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())

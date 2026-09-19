"""Maintainer-only packaging step. Never run inside a consumer to bless drift."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
files = {p.relative_to(root / "seed").as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
         for p in sorted((root / "seed").rglob("*")) if p.is_file() and "__pycache__" not in p.parts}
manifest = {"schema": 2, "distribution_version": "2.0.0-dev.2", "contract": "fixed-v2-1", "operating_stages": ["V2", "V3_frozen"], "compatibility": "fresh installation; no legacy ledger import", "files": files}
(root / "seed-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Manifest: {len(files)} payload files")

"""Offline seed distributor; the separately supplied harness.py implements the local core."""
from __future__ import annotations

import argparse
import hashlib
import io
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import stat
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ".harness-seed.json"
PENDING = ".harness-seed.pending.json"


class SeedError(Exception):
    def __init__(self, code: int, message: str):
        super().__init__(message)
        self.code = code


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def encoded(value: dict) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def no_links(path: Path) -> None:
    for part in (path, *path.parents):
        try:
            info = part.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise SeedError(5, f"Symlink/junction/reparse path is unsupported: {part}")


def safe_relative(name: str) -> bool:
    p = PurePosixPath(name)
    return (bool(name) and not p.is_absolute() and p.as_posix() == name
            and "\\" not in name and ":" not in name
            and all(part not in {".", ".."} and part.rstrip(" .") == part for part in p.parts))


def load_seed(root: Path = ROOT) -> tuple[dict, dict[str, bytes], dict]:
    manifest_path = root / "seed-manifest.json"
    no_links(manifest_path)
    raw = manifest_path.read_bytes()
    manifest = json.loads(raw)
    if (type(manifest.get("schema_version")) is not int or manifest["schema_version"] != 1
            or type(manifest.get("contract_version")) is not int or manifest["contract_version"] not in (1, 2, 3, 4, 5, 6)):
        raise SeedError(2, "Unsupported seed manifest/contract version; use a compatible distributor")
    files = manifest.get("files")
    if not isinstance(files, dict) or not files:
        raise SeedError(2, "Missing seed file allowlist")
    if any(not safe_relative(name) for name in files) or len({n.casefold() for n in files}) != len(files):
        raise SeedError(2, "Unsafe or case-colliding seed path")
    payload = {}
    seed_root = root / "seed"
    no_links(seed_root)
    actual = set()
    for path in seed_root.rglob("*"):
        no_links(path)
        if path.is_file():
            actual.add(path.relative_to(seed_root).as_posix())
    if actual != set(files):
        raise SeedError(2, "Seed inventory differs from manifest")
    for name, expected in files.items():
        path = seed_root / name
        no_links(path)
        data = path.read_bytes()
        if sha(data) != expected:
            raise SeedError(2, f"Seed hash mismatch: {name}")
        payload[name] = data
    for name in ("docs/harness/objects.json", "docs/harness/relations.json"):
        if json.loads(payload[name]) != []:
            raise SeedError(2, "Seed must contain empty project registries")
    if payload["docs/harness/events.jsonl"].strip():
        raise SeedError(2, "Seed must not contain project events")
    release = json.loads(payload["docs/harness/releases/current-harness.json"])
    local_core = manifest["contract_version"] >= 4
    prevention = manifest["contract_version"] >= 5
    governed_wiki = manifest["contract_version"] >= 6
    enforcement = ["configured_test_dispatch_within_local_cli"] if local_core else []
    if prevention: enforcement.append("bootstrap_readiness_gate")
    if governed_wiki: enforcement.append("wiki_tree_and_access_binding")
    if (release.get("distribution_version") != manifest.get("distribution_version")
            or release.get("contract_version") != manifest["contract_version"]
            or release.get("capability_level") != ("local_core_preview" if local_core else "seed")
            or release.get("verified_capabilities") != []
            or release.get("automated_enforcement") != enforcement):
        raise SeedError(2, "Seed distribution identity or capability claims are inconsistent")
    if local_core and ("harness.py" not in payload or "docs/harness/runtime/README.md" not in payload
                       or release.get("distribution_kind") != "contract_seed_with_local_core"
                       or release.get("implemented_mechanisms") != ["strict_local_record_validation", "transactional_event_ledger",
                           "pinned_test_process_capture", "version_bound_task_status", "local_feedback_candidate", "isolated_ledger_restore"] + (["mandatory_bootstrap_artifact_gate"] if prevention else []) + (["interview_bound_document_hierarchy", "local_authenticated_wiki_sessions"] if governed_wiki else [])):
        raise SeedError(2, "Local core files and declared scope must be supplied together")
    if prevention and ("bootstrap.py" not in payload or "docs/harness/bootstrap/README.md" not in payload):
        raise SeedError(2, "Mandatory bootstrap gate missing")
    if governed_wiki and not {"wiki_core.py", "wiki_access.py"} <= set(payload):
        raise SeedError(2, "Governed wiki components missing")
    if manifest.get('wiki_presentation_profile') is not None or manifest['distribution_version']=='0.7.0':
        if (manifest.get('wiki_presentation_profile')!='newgame-style-wiki-1'
                or release.get('wiki_presentation_profile')!=manifest['wiki_presentation_profile']
                or not {'wiki_template.py','docs/harness/wiki/README.md'}<=set(payload)
                or any(b'wiki_template.py' not in payload[name] for name in ['AGENTS.md','BOOTSTRAP_PROMPT.md'])):
            raise SeedError(2, 'Default wiki presentation and bootstrap instructions missing')
    if manifest.get('wiki_draft_profile') is not None or manifest['distribution_version']=='0.8.0':
        if (manifest.get('wiki_draft_profile') != 'newgame-object-draft-1'
                or release.get('wiki_draft_profile') != manifest['wiki_draft_profile']
                or not {'wiki_draft.py', 'docs/wiki/draft-input.json'} <= set(payload)
                or any(b'wiki_draft.py' not in payload[n] for n in ['AGENTS.md', 'BOOTSTRAP_PROMPT.md'])):
            raise SeedError(2, 'Automatic object draft or first-run instructions missing')
    if manifest.get('wiki_graph_profile') is not None:
        if (manifest['wiki_graph_profile']!='object-node-map-1'
                or release.get('wiki_graph_profile')!=manifest['wiki_graph_profile']
                or 'wiki_graph.py' not in payload
                or b'graph.render(' not in payload.get('wiki_draft.py',b'')
                or any(b'object-node-map-1' not in payload[n] for n in ('AGENTS.md','BOOTSTRAP_PROMPT.md','docs/harness/contracts/views-state.md'))):
            raise SeedError(2, 'Object node map contract or renderer missing')
    receipt = {"schema_version": 1, "distribution_version": manifest["distribution_version"],
               "contract_version": manifest["contract_version"], "source_repository": manifest["source_repository"],
               "manifest_sha256": sha(raw), "files": files}
    return manifest, payload, receipt


def write_new(path: Path, data: bytes) -> None:
    no_links(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(data)


def installation_bundle(payload: dict[str, bytes], receipt: dict) -> tuple[dict, dict]:
    """Plan draft bytes before touching the target; separate generated ownership."""
    if 'wiki_draft.py' not in payload:
        return payload, receipt
    path = ROOT / 'seed/wiki_draft.py'
    if path.read_bytes() != payload['wiki_draft.py']:
        raise SeedError(2, 'Draft renderer differs from verified distribution')
    graph_path=ROOT/'seed/wiki_graph.py'
    if graph_path.read_bytes()!=payload.get('wiki_graph.py'):
        raise SeedError(2, 'Graph renderer differs from verified distribution')
    spec = importlib.util.spec_from_file_location('seed_wiki_draft', path)
    draft = importlib.util.module_from_spec(spec)
    previous_bytecode = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec.loader.exec_module(draft)
        generated = draft.bundle(json.loads(payload[draft.SOURCE]), sha(payload['wiki_draft.py']))
    except (ValueError, KeyError, TypeError) as exc:
        raise SeedError(2, f'Invalid default object draft: {exc}') from exc
    finally:
        sys.dont_write_bytecode = previous_bytecode
    files = {draft.OUTPUT + '/' + n: raw for n, raw in generated.items()}
    if set(files) & set(payload):
        raise SeedError(2, 'Generated draft overlaps seed-owned files')
    return {**payload, **files}, {**receipt, 'draft_profile': draft.PROFILE,
                                'draft_files': {n: sha(raw) for n, raw in files.items()}}


def initialize(target: Path, payload: dict[str, bytes], receipt: dict, dry_run: bool) -> dict:
    payload, receipt = installation_bundle(payload, receipt)
    target = Path(os.path.abspath(target.expanduser()))
    if target == ROOT or ROOT in target.parents:
        raise SeedError(5, "Install into a separate project, outside the distributor checkout")
    no_links(target)
    if target.exists() and not target.is_dir():
        raise SeedError(5, "Target must be a directory")
    for name in (*payload, RECEIPT, PENDING):
        dest = target / name
        no_links(dest)
        for parent in dest.parents:
            if parent.exists() and not parent.is_dir():
                raise SeedError(5, f"Non-directory ancestor: {parent}")
    if (target / PENDING).exists():
        raise SeedError(5, "Pending/partial installation exists; inspect it before recovery")
    if (target / RECEIPT).exists():
        try:
            existing = json.loads((target / RECEIPT).read_bytes())
        except (ValueError, OSError) as exc:
            raise SeedError(5, f"Invalid existing receipt: {exc}") from exc
        if existing != receipt:
            raise SeedError(5, "Different seed receipt; use the reviewed upgrade procedure")
        if any(not (target / n).is_file() or sha((target / n).read_bytes()) != sha(data)
               for n, data in payload.items()):
            raise SeedError(5, "Installed files changed; preserve project work and review instead of reinstalling")
        return {"outcome": "unchanged", "target": str(target), "dry_run": dry_run}
    conflicts = [n for n in payload if (target / n).exists()]
    if conflicts:
        raise SeedError(5, "Existing project files would be overwritten: " + ", ".join(conflicts))
    if dry_run:
        return {"outcome": "planned", "target": str(target), "files": sorted(payload), "dry_run": True}
    created = []
    try:
        target.mkdir(parents=True, exist_ok=True)
        try:
            write_new(target / PENDING, encoded({"manifest_sha256": receipt["manifest_sha256"]}))
        except FileExistsError as exc:
            raise SeedError(5, "Another installation started; no payload overwritten") from exc
        for name, data in sorted(payload.items()):
            write_new(target / name, data)
            created.append(name)
        write_new(target / RECEIPT, encoded(receipt))
        # Only our successful installation marker is removed, never project files.
        (target / PENDING).unlink()
    except OSError as exc:
        raise SeedError(9, f"Partial installation; preserve files and inspect {target / PENDING}; "
                        f"created={created}; error={exc}") from exc
    return {"outcome": "installed", "target": str(target), "files": len(payload),
            "manifest_sha256": receipt["manifest_sha256"],
            "wiki_draft": ".local/wiki-draft/index.html" if 'draft_files' in receipt else None,
            "bootstrap_ready": False}


def archive(payload: dict[str, bytes], receipt: dict) -> bytes:
    payload, receipt = installation_bundle(payload, receipt)
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_STORED) as bundle:
        for name, data in sorted({**payload, RECEIPT: encoded(receipt)}.items()):
            info = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            bundle.writestr(info, data)
    return stream.getvalue()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("check", help="Verify the seed inventory, hashes and empty-state boundary")
    install = commands.add_parser("init", help="Copy seed files without overwriting existing files")
    install.add_argument("--target", type=Path, required=True)
    install.add_argument("--dry-run", action="store_true")
    pack = commands.add_parser("pack", help="Create a reproducible seed-only ZIP")
    pack.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        manifest, payload, receipt = load_seed()
        if args.command == "check":
            result = {"outcome": "checked", "version": manifest["distribution_version"],
                      "files": len(payload), "manifest_sha256": receipt["manifest_sha256"]}
        elif args.command == "init":
            result = initialize(args.target, payload, receipt, args.dry_run)
        else:
            data = archive(payload, receipt)
            path = Path(os.path.abspath(args.out.expanduser()))
            no_links(path)
            if path.exists():
                if not path.is_file() or path.read_bytes() != data:
                    raise SeedError(5, "Archive target exists with different content")
                result = {"outcome": "unchanged", "path": str(path), "sha256": sha(data)}
            else:
                write_new(path, data)
                result = {"outcome": "packed", "path": str(path), "sha256": sha(data)}
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except SeedError as exc:
        print(json.dumps({"outcome": "error", "code": exc.code, "message": str(exc)}, ensure_ascii=False))
        return exc.code
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"outcome": "error", "code": 2, "message": str(exc)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    sys.exit(main())

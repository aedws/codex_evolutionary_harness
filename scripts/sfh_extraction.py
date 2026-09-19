"""Maintainer inventory/extraction against a pinned read-only SFH checkout."""
import argparse
from collections import Counter
import fnmatch
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "seed"))
from core import local, no_links
from source_catalog import CatalogError, canonical, compare, extract, fingerprint, need, read_json, save


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args])


def pinned_files(reference, revision):
    reference = reference.absolute()
    no_links(reference)
    need(re.fullmatch(r"[0-9a-f]{40}", revision), "full commit required")
    need(git(reference, "rev-parse", "HEAD").decode().strip() == revision, "reference commit mismatch")
    need(not git(reference, "status", "--porcelain", "--untracked-files=no").strip(), "tracked reference drift")
    files = []
    for entry in git(reference, "ls-tree", "-rz", "--long", revision).split(b"\0"):
        if not entry:
            continue
        header, raw_path = entry.split(b"\t", 1)
        mode, kind, blob, size = header.decode().split()
        path = raw_path.decode("utf-8")
        need(mode in {"100644", "100755"} and kind == "blob", "unsupported symlink/submodule source: " + path)
        actual = local(reference, path)
        need(actual.is_file(), "tracked source missing: " + path)
        h = hashlib.sha256()
        with actual.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                h.update(block)
        files.append({"path": path, "git_blob": blob, "git_size": int(size), "working_sha256": h.hexdigest()})
    return files


def inventory(reference, revision, catalog):
    files = pinned_files(reference, revision)
    family_by_id = {f["id"]: f for f in catalog["families"]}
    need(len(family_by_id) == len(catalog["families"]), "duplicate contract family")
    by_path = {f["path"]: f for f in files}
    for family in catalog["families"]:
        need(family["source_refs"] and all(x in by_path for x in family["source_refs"]), "missing family source: " + family["id"])
    units = []
    for item in files:
        name = item["path"]
        assigned = [f for f in catalog["families"] if any(fnmatch.fnmatchcase(name, pat) for pat in f["patterns"])]
        if not assigned:
            assigned = [family_by_id["SFH-DOMAIN-REVIEW"]]
        item.update({"families": [f["id"] for f in assigned], "stages": sorted(set(f["stage"] for f in assigned)),
                     "classification_basis": "inferred_by_static_analysis:path_patterns", "semantic_review": "queued",
                     "disposition": "review_required", "exclusion_approved": False})
        suffix = Path(name).suffix.lower()
        if suffix in {".uid", ".import"}:
            item["suggested_disposition"] = "generated_metadata; validate paired source and asset pipeline"
        elif suffix in {".png", ".ogg", ".ttf", ".woff", ".woff2", ".ico"}:
            item["suggested_disposition"] = "project_asset; inspect license/provenance/package contract"
        elif name.startswith("game/"):
            item["suggested_disposition"] = "project_implementation; extract reusable invariants before exclusion"
        else:
            item["suggested_disposition"] = "core_or_adapter_contract_review"
        if suffix == ".md":
            text = local(reference, name).read_text(encoding="utf-8-sig")
            for line, heading in enumerate(text.splitlines(), 1):
                if re.match(r"^#{1,6}\s+", heading):
                    units.append({"id": "UNIT-" + fingerprint([name, line, heading])[:20], "path": name, "line": line,
                                  "heading": heading.lstrip("# "), "source_sha256": item["working_sha256"], "families": item["families"], "state": "semantic_review_queued"})
    anchors = []
    for contract in catalog["contracts"]:
        need(contract["family"] in family_by_id and contract["tests_required"], "contract family/test obligation missing")
        for anchor in contract["anchors"]:
            path = anchor["path"]
            need(path in by_path, "contract anchor file missing")
            text = local(reference, path).read_text(encoding="utf-8-sig")
            lines = [i for i, s in enumerate(text.splitlines(), 1) if anchor["contains"] in s]
            need(lines, "contract anchor absent: " + contract["id"] + ":" + path)
            anchors.append({"contract": contract["id"], "path": path, "lines": lines, "source_sha256": by_path[path]["working_sha256"]})
    need(len({x["id"] for x in catalog["contracts"]}) == len(catalog["contracts"]), "duplicate contract ID")
    need(set(family_by_id) <= {c["family"] for c in catalog["contracts"]}, "family without extraction obligation")
    # Detect source changes during the scan, including ignored formatting differences.
    after = pinned_files(reference, revision)
    need([{k: f[k] for k in ("path", "git_blob", "git_size", "working_sha256")} for f in files] == after, "source changed during inventory")
    return {"schema": 1, "reference_commit": revision, "source_tree": git(reference, "rev-parse", "HEAD^{tree}").decode().strip(),
            "scope": "all_git_tracked_files", "inventory_only_not_semantic_acceptance": True,
            "coverage": {"tracked_files": len(files), "assigned_files": len(files), "unassigned_files": 0,
                         "families": len(family_by_id), "baseline_contracts": len(catalog["contracts"]), "markdown_sections_queued": len(units),
                         "files_semantically_completed": 0, "exclusions_approved": 0},
            "family_file_counts": dict(sorted(Counter(f for item in files for f in item["families"]).items())),
            "files": files, "review_units": units, "contract_anchors": anchors, "catalog_sha256": fingerprint(catalog)}


def check_plan(plan, catalog, inv):
    phases = plan["phases"]
    order = [s["id"] for s in phases]
    need(len(order) == len(set(order)) and order == [f"S{i:02}" for i in range(12)], "schedule phase inventory mismatch")
    for i, phase in enumerate(phases):
        need(set(phase["depends_on"]) <= set(order[:i]), "schedule dependency cycle or forward edge")
        need(phase["acceptance"] and phase["scope"], "phase gate missing")
    for family in catalog["families"]:
        need(family["stage"] in order, "unscheduled family")
    for contract in catalog["contracts"]:
        need(contract["stage"] in order and contract["implementation_target"] and contract["disposition"], "unscheduled contract")
        need(all(a["path"] in {f["path"] for f in inv["files"]} for a in contract["anchors"]), "contract source missing")
    need(inv["reference_commit"] == plan["source_commit"], "plan/source version mismatch")
    return {"state": "schedule_coverage_verified", "phases": len(phases), **inv["coverage"], "functionality_certified": False}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--reference", required=True, type=Path)
    p.add_argument("--commit", required=True)
    p.add_argument("--out", required=True, type=Path)
    args = p.parse_args()
    try:
        catalog, _ = read_json(ROOT / "docs/requirements/sfh-contract-catalog.json")
        plan, _ = read_json(ROOT / "docs/requirements/sfh-extraction-plan.json")
        inv = inventory(args.reference, args.commit, catalog)
        schedule = check_plan(plan, catalog, inv)
        source_path = "docs/assets/project-ontology.json"
        source, sha = read_json(local(args.reference, source_path))
        bundle = extract(source, namespace="sfh", revision=args.commit, source_path=source_path, source_sha256=sha)
        result = compare(bundle, source, sha)
        saves = {"inventory": save(args.out / "inventory.json", inv), "source_bundle": save(args.out / "sfh-source-bundle.json", bundle)}
        receipt = {"schedule": schedule, "source_comparison": result, "inventory_sha256": fingerprint(inv), "bundle_sha256": fingerprint(bundle),
                   "catalog_sha256": fingerprint(catalog), "reference_mutated": False, "seed_runtime_adoption": False}
        receipt_write = save(args.out / "receipt.json", receipt)
        print(canonical({**receipt, "writes": {**saves, "receipt": receipt_write}}))
        return 0
    except (OSError, ValueError, KeyError, TypeError, subprocess.CalledProcessError) as exc:
        print(canonical({"state": "error", "reason": str(exc)}))
        return 2


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())

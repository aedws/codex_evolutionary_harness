"""Lossless, offline source extraction. Source declarations never become verification."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import sys

PROFILE = "ontology-snapshot-1"
VIEW_TYPES = {"work_item": "Task", "decision": "Decision", "risk": "Decision", "principle": "Decision", "module": "Module"}


class CatalogError(ValueError):
    pass


def need(condition, message):
    if not condition:
        raise CatalogError(message)


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def fingerprint(value):
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def read_json(path):
    path = Path(path)
    from core import no_links
    no_links(path.absolute())
    need(path.stat().st_size <= 32 * 1024 * 1024, "snapshot exceeds 32 MiB")
    raw = path.read_bytes()
    def pairs(items):
        result = {}
        for key, value in items:
            need(key not in result, "duplicate JSON key: " + key)
            result[key] = value
        return result
    obj = json.loads(raw.decode("utf-8-sig"), object_pairs_hook=pairs,
                     parse_constant=lambda x: (_ for _ in ()).throw(CatalogError("non-finite JSON number")))
    canonical(obj)
    return obj, hashlib.sha256(raw).hexdigest()


def validate_source(source):
    need(isinstance(source, dict), "source must be an object")
    for field in ("objects", "relations", "object_types", "interfaces", "action_types", "lifecycle", "source_systems"):
        need(isinstance(source.get(field), list), "missing source collection: " + field)
    objects = source["objects"]
    need(objects and len(objects) <= 100000, "invalid object inventory")
    ids = [o["id"] for o in objects]
    need(all(isinstance(i, str) and i for i in ids) and len(set(ids)) == len(ids), "duplicate/invalid native object ID")
    by_id = {o["id"]: o for o in objects}
    types = {o["id"] for o in source["object_types"]}
    need(len(types) == len(source["object_types"]), "duplicate object type")
    for obj in objects:
        need(obj.get("type") in types, "unknown native object type")
    edges = source["relations"]
    need(len(edges) <= 1000000 and len({fingerprint(e) for e in edges}) == len(edges), "duplicate/oversized relation inventory")
    for edge in edges:
        need(edge.get("from") in by_id and edge.get("to") in by_id, "dangling relationship")
        need(isinstance(edge.get("type"), str) and edge["type"], "relationship type required")
        need(isinstance(edge.get("origin"), str) and edge["origin"], "relationship origin required")
    for interface in source["interfaces"]:
        need(isinstance(interface.get("required"), list) and isinstance(interface.get("applies_to"), list), "invalid interface")
        for obj in objects:
            if obj["type"] not in interface["applies_to"]:
                continue
            for field in interface["required"]:
                present = field in obj
                if field == "relations":
                    present = present or any(obj["id"] in (e["from"], e["to"]) for e in edges)
                elif field == "verified_by":
                    present = any(e["from"] == obj["id"] and e["type"] == "verified_by" for e in edges)
                need(present, f"missing interface field: {obj['id']}:{field}")
    actions = {a["id"]: a for a in source["action_types"]}
    need(len(actions) == len(source["action_types"]), "duplicate action type")
    for action in actions.values():
        need(action.get("actor") in by_id, "unresolved action actor")
        need(all(action.get(k) for k in ("input", "output", "guard")), "action contract incomplete")
    sources = {s["id"] for s in source["source_systems"]}
    for stage in source["lifecycle"]:
        need(stage.get("action") in actions, "unresolved lifecycle action")
        need(isinstance(stage.get("evidence"), list) and set(stage["evidence"]) <= sources, "unresolved lifecycle evidence")
    return {"objects": len(objects), "relations": len(edges), "object_types": len(types), "interfaces": len(source["interfaces"]), "actions": len(actions), "lifecycle_stages": len(source["lifecycle"])}


def extract(source, *, namespace, revision, source_path, source_sha256):
    counts = validate_source(source)
    need(isinstance(namespace, str) and re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,39}", namespace), "invalid source namespace")
    need(isinstance(revision, str) and revision and isinstance(source_path, str) and source_path, "source revision/path required")
    need(re.fullmatch(r"[0-9a-f]{64}", source_sha256), "source byte hash required")
    ref = {"namespace": namespace, "revision": revision, "path": source_path, "sha256": source_sha256, "semantic_sha256": fingerprint(source)}
    mapping = {obj["id"]: namespace + ":" + fingerprint([namespace, obj["id"]])[:24] for obj in source["objects"]}
    need(len(set(mapping.values())) == len(mapping), "normalized identity collision")
    objects = [{"id": mapping[obj["id"]], "native_id": obj["id"], "native_type": obj["type"],
                "view_type": VIEW_TYPES.get(obj["type"]), "record_layer": "oop_subject" if obj["type"] in VIEW_TYPES else "dop_support",
                "verification": "unverified", "source_record": copy.deepcopy(obj)} for obj in source["objects"]]
    relations = [{"id": namespace + ":edge:" + fingerprint(edge)[:24], "from": mapping[edge["from"]], "to": mapping[edge["to"]],
                  "type": edge["type"], "basis": "inferred_by_static_analysis", "origin": edge["origin"], "source_record": copy.deepcopy(edge)} for edge in source["relations"]]
    return {"schema": 1, "profile": PROFILE, "source": ref, "counts": counts,
            "source_metadata": copy.deepcopy({k: v for k, v in source.items() if k not in {"objects", "relations"}}),
            "objects": objects, "relations": relations,
            "authority": {"mode": "reference_only", "effects": [], "inherited_permissions": False},
            "assurance": {"structural": "validated", "semantic_equivalence": "source_records_preserved", "execution_equivalence": "unverified", "owner_acceptance": "pending"}}


def reconstruct(bundle):
    need(bundle.get("schema") == 1 and bundle.get("profile") == PROFILE, "unsupported extraction bundle")
    return {**copy.deepcopy(bundle["source_metadata"]), "objects": [copy.deepcopy(o["source_record"]) for o in bundle["objects"]],
            "relations": [copy.deepcopy(e["source_record"]) for e in bundle["relations"]]}


def verify(bundle):
    source = reconstruct(bundle)
    ref = bundle["source"]
    need(fingerprint(source) == ref["semantic_sha256"], "source reconstruction mismatch")
    expected = extract(source, namespace=ref["namespace"], revision=ref["revision"], source_path=ref["path"], source_sha256=ref["sha256"])
    need(canonical(expected) == canonical(bundle), "derived fields/authority/verification tampered")
    return {"state": "source_structure_verified", **expected["counts"], "semantic_sha256": ref["semantic_sha256"],
            "runtime_verification": "unverified", "permissions_inherited": False}


def compare(bundle, source, raw_sha):
    result = verify(bundle)
    need(bundle["source"]["sha256"] == raw_sha, "source bytes changed; re-extract under a new revision")
    need(canonical(reconstruct(bundle)) == canonical(source), "source content differs")
    return {**result, "roundtrip": "all_fields_equal"}


def save(path, value):
    from core import no_links
    path = Path(path).absolute()
    no_links(path)
    data = (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n").encode("utf-8")
    if path.exists():
        need(path.read_bytes() == data, "output ownership conflict; use a new path")
        return "unchanged"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as out:
        out.write(data)
    return "created"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    imp = sub.add_parser("extract")
    imp.add_argument("--source", type=Path, required=True)
    imp.add_argument("--namespace", required=True)
    imp.add_argument("--revision", required=True)
    imp.add_argument("--out", type=Path, required=True)
    check = sub.add_parser("verify")
    check.add_argument("--bundle", type=Path, required=True)
    check.add_argument("--source", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "extract":
            source, sha = read_json(args.source)
            bundle = extract(source, namespace=args.namespace, revision=args.revision, source_path=args.source.name, source_sha256=sha)
            result = {**verify(bundle), "write": save(args.out, bundle), "bundle_sha256": fingerprint(bundle)}
        else:
            bundle, _ = read_json(args.bundle)
            result = compare(bundle, *read_json(args.source)) if args.source else verify(bundle)
        print(canonical(result))
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(canonical({"state": "error", "reason": str(exc)}))
        return 2


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())

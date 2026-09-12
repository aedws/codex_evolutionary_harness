"""Read-only structural checks for the seed's contract coverage, not a runtime grader."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

from seed import ROOT, SeedError, load_seed, safe_relative


def check_review_packet(payload: dict, declared: dict) -> tuple[int, int]:
    spec = json.loads(payload["docs/harness/contracts/review-cases.json"])
    packet = json.loads(payload["docs/harness/templates/assurance-review.example.json"])
    expected = {"A01": {"V01", "V02"}, "A02": {"V03"}, "A03": {"E01"},
                "A04": {"E03"}, "A05": {"E04"}, "A06": {"X02"}, "A07": {"E02"}}
    areas = spec.get("areas", [])
    if (spec.get("schema_version") != 1 or spec.get("contract_version") != 3
            or spec.get("coverage_kind") != "planned_review_scenarios"
            or spec.get("runtime_status") != "unverified" or len(areas) != 7
            or {a.get("id") for a in areas} != set(expected)):
        raise SeedError(2, "Seven review areas must remain planned, complete and unique")
    if (packet.get("schema_version") != 1 or packet.get("contract_version") != 3
            or packet.get("template_only") is not True or packet.get("evidence_refs") != []
            or any(packet.get(k) is not None for k in
                   ("review_id", "execution_id", "change_digest", "reviewer_principal", "review_level"))
            or set(packet.get("areas", {})) != set(expected)):
        raise SeedError(2, "Review template must not inherit identities or evidence")
    total = 0
    for area in areas:
        refs = area.get("clause_refs", [])
        if (len(refs) != len(expected[area["id"]])
                or {r.get("id") for r in refs} != expected[area["id"]]
                or any(declared.get(r.get("id")) != r.get("path") for r in refs)):
            raise SeedError(2, "Review area clause references mismatch")
        fields = area.get("required_fields", [])
        if (not fields or any(not isinstance(f, str) or not f for f in fields)
                or len(fields) != len(set(fields)) or {"status", "evidence_refs"} & set(fields)):
            raise SeedError(2, "Review fields must be explicit and unique")
        blank = packet["areas"][area["id"]]
        if (set(blank) != set(fields) | {"status", "evidence_refs"}
                or blank.get("status") != "unknown" or blank.get("evidence_refs") != []
                or any(blank.get(f) is not None for f in fields)):
            raise SeedError(2, "Review template must keep unobserved fields unknown")
        scenarios = area.get("scenarios", [])
        if (len(scenarios) != 3
                or {s.get("kind") for s in scenarios} != {"accept", "reject", "inconclusive"}
                or any(not isinstance(s.get(k), str) or not s[k].strip()
                       for s in scenarios for k in ("given", "expected"))
                or any(s.get("runtime_status") != "planned_not_executed" for s in scenarios)):
            raise SeedError(2, "Each area needs planned accept/reject/inconclusive scenarios")
        total += len(scenarios)
    return len(areas), total


def check(root: Path = ROOT) -> dict:
    manifest, payload, _ = load_seed(root)
    if manifest["contract_version"] != 3:
        raise SeedError(2, "Detailed coverage checks require contract 3")
    prefix = "docs/harness/contracts/"
    coverage = json.loads(payload[prefix + "coverage.json"])
    if (coverage.get("schema_version") != 1 or coverage.get("contract_version") != 3
            or coverage.get("coverage_kind") != "documented_contract"
            or coverage.get("runtime_status") != "unverified"):
        raise SeedError(2, "Coverage must not claim implemented/runtime-verified goals")
    goals = coverage.get("goals", [])
    expected = {f"G{i:02}" for i in range(1, 18)}
    if len(goals) != 17 or {g.get("goal_id") for g in goals} != expected:
        raise SeedError(2, "All 17 goals must appear exactly once")
    declared = {}
    for name in ("feedback.md", "views-state.md", "execution.md", "evolution.md"):
        content = payload[prefix + name].decode("utf-8")
        for cid in re.findall(r"^## ([FVXE]\d{2})\b", content, re.M):
            if cid in declared:
                raise SeedError(2, "Duplicate contract clause ID")
            declared[cid] = name
    used = set()
    for goal in goals:
        if (not goal.get("acceptance_scenario") or not goal.get("clauses")
                or goal.get("runtime_eval_status") != "planned_not_executed"):
            raise SeedError(2, "Goal scenario must distinguish planned runtime evals")
        for clause in goal["clauses"]:
            if declared.get(clause.get("id")) != clause.get("path"):
                raise SeedError(2, "Coverage references a missing/mismatched clause")
            used.add(clause["id"])
    if used != set(declared):
        raise SeedError(2, "Every operational clause must trace to a goal")
    review_areas, review_scenarios = check_review_packet(payload, declared)
    config = json.loads(payload["docs/harness/feedback/config.json"])
    permissions = config["permissions"]
    if (any(permissions.get(k) is not False for k in ("submit", "merge", "release", "adopt"))
            or permissions.get("authorization_refs") != []
            or config["upstream"]["repository"] is not None
            or config["upstream"]["base_ref"] is not None
            or config["sharing"]["allowed_paths"] != []
            or config["sharing"]["export_authorization_refs"] != []):
        raise SeedError(2, "Seed must not inherit upstream/export authority")
    for name, id_key in (("feedback-candidate", "candidate_id"), ("skill-observation", "observation_id")):
        draft = json.loads(payload[f"docs/harness/templates/{name}.example.json"])
        if draft.get("template_only") is not True or draft.get(id_key) is not None or draft.get("evidence_refs") != []:
            raise SeedError(2, "Record examples must not ship live identities or evidence")
    overlay = json.loads(payload["docs/harness/overlays/project.json"])
    if (overlay["base_contract_version"] != 3 or overlay["id"] is not None
            or overlay["additions"]["skills"] != [] or overlay["eval_refs"] != []):
        raise SeedError(2, "Overlay must start with contract-3-compatible empty skill/eval bindings")
    # Check local Markdown links within the shipped payload; no network access.
    links = 0
    for name, data in payload.items():
        if not name.endswith(".md"):
            continue
        for target in re.findall(r"\]\(([^)]+)\)", data.decode("utf-8")):
            if "://" in target or target.startswith("#"):
                continue
            target = target.split("#", 1)[0]
            parts = list(Path(name).parent.parts)
            for part in target.split("/"):
                if part == "..":
                    if not parts:
                        raise SeedError(2, "Seed documentation link escapes payload")
                    parts.pop()
                elif part not in (".", ""):
                    parts.append(part)
            resolved = "/".join(parts)
            if not safe_relative(resolved) or resolved not in payload:
                raise SeedError(2, f"Broken seed link: {name} -> {target}")
            links += 1
    return {"result": "pass", "goals": len(goals), "clauses": len(declared), "links": links,
            "review_areas": review_areas, "planned_review_scenarios": review_scenarios,
            "scope": "structural coverage and safe distribution defaults; not runtime goal verification"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    try:
        print(json.dumps(check(args.root), ensure_ascii=False))
        return 0
    except (SeedError, ValueError, KeyError, TypeError, OSError) as exc:
        print(json.dumps({"result": "error", "message": str(exc)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

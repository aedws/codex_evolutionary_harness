"""Fixed V2 kernel. Standard library only; local trusted-operator boundary."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import sqlite3
import stat
import subprocess
import sys
import tempfile
import time

VERSION = "2.0.0-dev.1"
SCHEMA = 2
OBJECT_TYPES = {"Requirement", "Task", "Decision", "Module", "Test", "Release"}
OBSERVATIONS = {"expression_preference", "product_correctness", "authority_violation", "workflow_friction", "skill_change", "unknown"}
FIELDS = {"aliases", "context_order", "output_format", "module_navigation", "checklist"}
DEFAULT = {"aliases": {}, "context_order": [], "output_format": "detailed", "module_navigation": {}, "checklist": []}
ENGINE_FILES = ("core.py", "harness.py", "wiki.py")


class ContractError(Exception):
    pass


def require(ok, message):
    if not ok:
        raise ContractError(message)


def encode(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value):
    return hashlib.sha256(encode(value).encode()).hexdigest()


def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def no_links(path):
    for p in (path, *path.parents):
        if p.exists() or p.is_symlink():
            st = p.lstat()
            require(not stat.S_ISLNK(st.st_mode) and not getattr(st, "st_file_attributes", 0) & 0x400,
                    "symlink/junction/reparse paths are forbidden")


def local(root, name):
    require(isinstance(name, str) and bool(name), "nonempty relative path required")
    p = PurePosixPath(name)
    require(not p.is_absolute() and p.as_posix() == name and "\\" not in name and ":" not in name
            and all(x not in {".", ".."} and x.rstrip(" .") == x for x in p.parts), "unsafe path")
    out = root / name
    no_links(out)
    require(out.resolve().is_relative_to(root.resolve()), "path escapes project")
    return out


def identifier(value):
    require(isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,95}", value), "invalid identifier")
    return value


def object_id(value):
    identifier(value)
    require(value.casefold() not in {"index", "objects", "evolution", "projection", "con", "prn", "aux", "nul", *[x.casefold() for x in OBJECT_TYPES]}, "reserved object ID")
    require(not re.fullmatch(r"(?i)(com|lpt)[1-9](\..*)?", value), "reserved filename")
    return value


def engine_identity():
    root = Path(__file__).resolve().parent
    return {n: file_hash(root / n) for n in ENGINE_FILES}


def snapshot(root, names):
    require(isinstance(names, list) and names and len(set(names)) == len(names), "unique input files required")
    require(len({n.casefold() for n in names}) == len(names), "case-colliding inputs")
    result = {}
    for name in sorted(names):
        require(not name.startswith((".harness/", "wiki/")), "derived/runtime files cannot be inputs")
        p = local(root, name)
        require(p.is_file(), "missing input: " + name)
        result[name] = file_hash(p)
    return result


def overlay(value, inputs, objects):
    require(isinstance(value, dict) and not set(value) - FIELDS, "specialization cannot change authority/core/acceptance")
    out = {**DEFAULT, **value}
    require(out["output_format"] in {"compact", "detailed"}, "unsupported output format")
    require(isinstance(out["aliases"], dict) and len(out["aliases"]) <= 20, "alias budget exceeded")
    for key, action in out["aliases"].items():
        require(isinstance(key, str) and 1 <= len(key) <= 40 and key.casefold() not in {"next", "status", "deploy", "delete", "push", "merge", "release"}, "invalid alias")
        require(action in {"next_ready", "status"}, "aliases cannot grant effects")
    require(isinstance(out["context_order"], list) and len(set(out["context_order"])) == len(out["context_order"])
            and set(out["context_order"]) <= set(inputs), "context must reference registered inputs")
    require(isinstance(out["module_navigation"], dict), "invalid module navigation")
    require(all(k in objects and objects[k]["type"] == "Module" and v in inputs
                for k, v in out["module_navigation"].items()), "module navigation must use registered module/input")
    require(isinstance(out["checklist"], list) and len(out["checklist"]) <= 10
            and all(isinstance(x, str) and 0 < len(x) <= 200 for x in out["checklist"]), "invalid checklist")
    return out


def interpret(config, command, ready, authorized):
    """One task maximum. This returns advice, never executes an action."""
    action = {"next": "next_ready", "status": "status"}.get(command, config["aliases"].get(command))
    if action == "status":
        return {"action": "status", "tasks": []}
    if action == "next_ready":
        choices = sorted(set(ready) & set(authorized))
        return {"action": "task" if choices else "blocked", "tasks": choices[:1]}
    return {"action": "clarify", "tasks": []}


def evaluate(config, cases):
    rows = []
    for case in cases:
        actual = interpret(config, case["command"], case["ready"], case["authorized"])
        rows.append({"id": case["id"], "split": case["split"], "category": case["category"],
                     "actual": actual, "expected": case["expected"], "passed": actual == case["expected"]})
    return rows


def validate_suite(suite):
    require(isinstance(suite, list) and 6 <= len(suite) <= 200, "6..200 preregistered eval cases required")
    require(len({c["id"] for c in suite}) == len(suite), "duplicate case IDs")
    fingerprints = set()
    for c in suite:
        identifier(c["id"])
        fingerprint = digest({k: c[k] for k in ("command", "ready", "authorized", "expected")})
        require(fingerprint not in fingerprints, "duplicate evaluation input/oracle across splits")
        fingerprints.add(fingerprint)
        require(c["split"] in {"development", "selection", "holdout"}, "invalid eval split")
        require(c["category"] in {"intent", "authority", "regression"}, "invalid eval category")
        require(isinstance(c["command"], str) and len(c["command"]) <= 200, "invalid command")
        for group in (c["ready"], c["authorized"]):
            require(isinstance(group, list), "invalid fixture task set")
            for t in group:
                identifier(t)
        expected = c["expected"]
        require(set(expected) == {"action", "tasks"} and expected["action"] in {"task", "blocked", "clarify", "status"}, "invalid oracle")
        require(isinstance(expected["tasks"], list) and len(expected["tasks"]) <= 1
                and set(expected["tasks"]) <= set(c["ready"]) & set(c["authorized"]), "oracle expands authority")
        require((expected["action"] == "task") == bool(expected["tasks"]), "inconsistent oracle")
        # Fixed commands and dangerous verbs have an immutable oracle.
        if c["command"] in {"next", "status", "deploy", "delete", "push"}:
            require(expected == interpret(DEFAULT, c["command"], c["ready"], c["authorized"]), "fixed contract oracle mismatch")
    for split in ("selection", "holdout"):
        require(any(c["split"] == split and c["category"] == "intent" for c in suite), "intent coverage missing")
        require(any(c["split"] == split and c["category"] == "authority" and not c["authorized"] for c in suite), "authority denial coverage missing")
        require(any(c["split"] == split and c["category"] == "regression" and c["command"] == "next" for c in suite), "fixed regression coverage missing")


class Kernel:
    def __init__(self, root):
        self.root = Path(root).absolute()
        no_links(self.root)
        self.path = self.root / ".harness" / "ledger.sqlite3"
        no_links(self.path)

    def connect(self, create=False):
        require(create or self.path.is_file(), "project is not initialized")
        if create:
            self.path.parent.mkdir(parents=True, exist_ok=True)
        con = sqlite3.connect(self.path, timeout=10)
        con.execute("PRAGMA synchronous=FULL")
        if create:
            con.execute("CREATE TABLE IF NOT EXISTS events (seq INTEGER PRIMARY KEY, kind TEXT NOT NULL, body TEXT NOT NULL, prev TEXT NOT NULL, hash TEXT NOT NULL)")
            con.execute("CREATE TABLE IF NOT EXISTS operations (key TEXT PRIMARY KEY, request TEXT NOT NULL, result TEXT)")
        con.commit()
        return con

    def records(self, con):
        result, prev = [], "0" * 64
        for seq, kind, body, old, sha in con.execute("SELECT * FROM events ORDER BY seq"):
            require(seq == len(result) + 1 and old == prev and sha == digest([seq, kind, json.loads(body), prev]), "event chain corrupted")
            result.append({"seq": seq, "kind": kind, "data": json.loads(body), "hash": sha})
            prev = sha
        return result

    def emit(self, con, kind, body):
        row = con.execute("SELECT seq, hash FROM events ORDER BY seq DESC LIMIT 1").fetchone()
        seq, prev = (row[0] + 1, row[1]) if row else (1, "0" * 64)
        sha = digest([seq, kind, body, prev])
        con.execute("INSERT INTO events VALUES (?,?,?,?,?)", (seq, kind, encode(body), prev, sha))
        return seq

    def state(self, records):
        s = {"objects": {}, "tasks": {}, "runs": {}, "observations": {}, "candidates": {}, "evals": {}, "configs": {}, "resumes": [], "mvp": None, "active": None, "init": None, "epoch": 0}
        for e in records:
            d, kind = e["data"], e["kind"]
            if kind == "Initialized":
                s["init"] = d
                s["configs"][d["config_id"]] = d["config"]
                s["active"] = d["config_id"]
            elif kind == "ObjectRegistered":
                s["objects"][d["id"]] = d
            elif kind == "TaskRegistered":
                s["tasks"][d["id"]] = d
            elif kind in {"RunStarted", "RunFinished", "RunReconciled"}:
                s["runs"][d["id"]] = {**s["runs"].get(d["id"], {}), **d}
            elif kind == "ObservationRecorded":
                s["observations"][d["id"]] = d
            elif kind == "MvpAccepted":
                s["mvp"] = d
            elif kind == "ResumeReadback":
                s["resumes"].append(d)
            elif kind == "CandidateProposed":
                s["candidates"][d["id"]] = d
            elif kind == "CandidateEvaluated":
                s["evals"][d["candidate"]] = d
            elif kind == "ConfigAdopted":
                s["configs"][d["config_id"]] = d["config"]
                s["active"] = d["config_id"]
                s["epoch"] += 1
            elif kind == "ConfigRolledBack":
                s["active"] = d["config_id"]
                s["epoch"] += 1
        return s

    def check(self, s):
        require(s["init"] and s["init"]["schema"] == SCHEMA, "unsupported ledger schema")
        require(s["init"]["engine"] == engine_identity(), "engine drift: use a separate installation/migration")

    def owner(self, s, actor):
        require(actor == s["init"]["owner"], "owner operator required")

    def current_inputs(self, s):
        return snapshot(self.root, s["init"]["inputs"])

    def run_state(self, s, run):
        if run.get("state") != "passed":
            return run.get("state", "unknown")
        try:
            return "passed" if run["inputs"] == self.current_inputs(s) else "stale"
        except (OSError, ContractError):
            return "stale"

    def ready(self, s):
        reasons = []
        mvp = s["mvp"]
        run = s["runs"].get(mvp["run"]) if mvp else None
        if not run or self.run_state(s, run) != "passed":
            reasons.append("current version-bound test run and owner MVP acceptance required")
        if run:
            latest = [r for r in s["runs"].values() if r["task"] == run["task"]][-1]
            if latest["id"] != run["id"] or run["config_id"] != s["active"]:
                reasons.append("MVP acceptance must reference latest run under the active config")
        if not run or not any(x["run"] == run["id"] for x in s["resumes"]):
            reasons.append("checkpoint resume readback required")
        for kind in OBJECT_TYPES:
            if not any(o["type"] == kind for o in s["objects"].values()):
                reasons.append("wiki binding missing: " + kind)
        try:
            receipt = json.loads((self.root / "wiki/.generated.json").read_text(encoding="utf-8"))
            require(receipt and all(file_hash(local(self.root / "wiki", n)) == sha for n, sha in receipt.items()), "wiki drift")
        except (OSError, ValueError, ContractError):
            reasons.append("generated wiki missing or modified; rebuild/review before exploration")
        if not s["observations"]:
            reasons.append("classified operational observation required")
        if any(r.get("state") == "unknown" for r in s["runs"].values()):
            reasons.append("unresolved run outcome")
        return {"ready": not reasons, "reasons": sorted(reasons), "rule": "readiness-2.0", "run": run["id"] if run else None}

    def transact(self, command, data, key, actor):
        require(isinstance(data, dict), "request must be a JSON object")
        identifier(key)
        identifier(actor)
        request = digest({"command": command, "data": data, "actor": actor})
        con = self.connect(create=command == "init")
        try:
            con.execute("BEGIN IMMEDIATE")
            records = self.records(con)
            s = self.state(records)
            if command != "init":
                self.check(s)
            prior = con.execute("SELECT request,result FROM operations WHERE key=?", (key,)).fetchone()
            if prior:
                require(prior[0] == request, "idempotency key payload conflict")
                return json.loads(prior[1]) if prior[1] else {"state": "unknown", "operation": key, "retry": "reconcile_only"}
            con.execute("INSERT INTO operations VALUES (?,?,NULL)", (key, request))
            result = self.dispatch(con, s, command, data, actor, key)
            if command == "run":
                con.commit()  # Preserve reservation BEFORE any subprocess effect.
                return self.execute_run(con, s, result, key)
            con.execute("UPDATE operations SET result=? WHERE key=?", (encode(result), key))
            con.commit()
            return result
        except BaseException:
            con.rollback()
            raise
        finally:
            con.close()

    def dispatch(self, con, s, cmd, d, actor, key):
        if cmd == "init":
            require(not s["init"], "already initialized; preserve existing ledger")
            require(d.get("schema") == SCHEMA and d.get("owner") == actor, "schema/owner mismatch")
            for role in ("owner", "proposer", "evaluator"):
                identifier(d[role])
            require(len({d[k] for k in ("owner", "proposer", "evaluator")}) == 3, "proposer/evaluator/owner must be distinct operator labels")
            require(isinstance(d.get("authority_ref"), str) and d["authority_ref"].strip(), "owner interview/authority reference required")
            require(d.get("exposure") == "offline_local", "only offline_local is implemented; interview for external exposure")
            inputs = snapshot(self.root, d["inputs"])
            adapter = d["test_adapter"]
            require(set(adapter) == {"script", "args"} and adapter["script"] in inputs, "test script must be a pinned project input")
            require(isinstance(adapter["args"], list) and all(isinstance(x, str) for x in adapter["args"]), "invalid test arguments")
            validate_suite(d["eval_cases"])
            require(type(d["candidate_budget"]) is int and 1 <= d["candidate_budget"] <= 10, "candidate budget must be 1..10")
            require(d["model_context"] and isinstance(d["model_context"], str), "model/environment context required (offline allowed)")
            init = {**d, "engine": engine_identity(), "config": DEFAULT, "config_id": "V2-" + digest(DEFAULT)[:16], "version": VERSION}
            self.emit(con, "Initialized", init)
            self.emit(con, "ObjectRegistered", {"id": "RELEASE-V2", "type": "Release", "title": "고정 V2 기반", "purpose": "공통 계약과 전환 규칙", "sources": [], "relations": []})
            self.emit(con, "ObjectRegistered", {"id": "DECISION-AUTHORITY", "type": "Decision", "title": "오너 인터뷰·권한", "purpose": d["authority_ref"], "sources": [], "relations": ["RELEASE-V2"]})
            self.emit(con, "ObjectRegistered", {"id": "TEST-BASELINE", "type": "Test", "title": "프로젝트 기본 검사", "purpose": "오너가 등록한 실제 테스트 어댑터", "sources": [adapter["script"]], "relations": ["RELEASE-V2"]})
            return {"state": "V2", "config": init["config_id"], "readiness": "unverified"}
        self.owner(s, actor) if cmd in {"object", "task", "run", "mvp", "adopt", "rollback", "reconcile"} else None
        if cmd == "object":
            object_id(d["id"])
            require(d["id"] not in s["objects"], "object identity exists; no silent overwrite")
            require(d["type"] in OBJECT_TYPES - {"Task", "Release"}, "use task/release lifecycle")
            require(d.get("title") and d.get("purpose") and isinstance(d.get("sources"), list) and d["sources"], "purpose and real source bindings required")
            require(set(d["sources"]) <= set(s["init"]["inputs"]), "unregistered source")
            require(isinstance(d.get("relations"), list) and set(d["relations"]) <= set(s["objects"]), "unknown relation")
            body = {k: d[k] for k in ("id", "type", "title", "purpose", "sources", "relations")}
            self.emit(con, "ObjectRegistered", body)
            return {"object": d["id"]}
        if cmd == "task":
            object_id(d["id"])
            require(d["id"] not in s["objects"], "task exists")
            req = s["objects"].get(d["requirement"], {})
            require(req.get("type") == "Requirement", "registered Requirement required")
            require(d.get("purpose") and d.get("authority_ref"), "task scope and authority required")
            require(d.get("acceptance") in {"machine_verifiable", "human_verifiable", "mixed"}, "acceptance class required")
            deps = d.get("depends_on", [])
            require(isinstance(deps, list) and len(deps) == len(set(deps)) and set(deps) <= set(s["tasks"]), "dependencies must be existing tasks")
            body = {**d, "depends_on": deps, "config_id": s["active"], "epoch": s["epoch"], "engine": s["init"]["engine"], "authorized_actor": actor}
            self.emit(con, "TaskRegistered", body)
            self.emit(con, "ObjectRegistered", {"id": d["id"], "type": "Task", "title": d["id"], "purpose": d["purpose"], "sources": req["sources"], "relations": [d["requirement"], "TEST-BASELINE"]})
            return {"task": d["id"], "config": s["active"], "state": "unverified"}
        if cmd == "run":
            task = s["tasks"].get(d["task"])
            require(task and task["authorized_actor"] == actor, "task authority missing")
            for dep in task["depends_on"]:
                runs = [r for r in s["runs"].values() if r["task"] == dep]
                require(runs and self.run_state(s, runs[-1]) == "passed", "dependency has no current passing evidence")
            require(not any(r["task"] == d["task"] and r["state"] == "unknown" for r in s["runs"].values()), "unknown prior run; reconcile before retry")
            run = {"id": "RUN-" + key, "task": d["task"], "config_id": task["config_id"], "inputs": self.current_inputs(s), "state": "unknown", "operation": key}
            self.emit(con, "RunStarted", run)
            return run
        if cmd == "reconcile":
            run = s["runs"].get(d["run"])
            require(run and run["state"] == "unknown", "only unknown runs can be reconciled")
            require(d.get("reason") and d.get("process_stopped") is True, "owner must confirm process stopped; cannot fabricate pass")
            self.emit(con, "RunReconciled", {"id": run["id"], "state": "interrupted", "reason": d["reason"], "actor": actor})
            return {"run": run["id"], "state": "interrupted", "new_run_requires_new_key": True}
        if cmd == "observe":
            require(actor in {s["init"][k] for k in ("owner", "proposer", "evaluator")}, "unknown observer")
            identifier(d["id"])
            require(d["id"] not in s["observations"] and d["category"] in OBSERVATIONS, "observation identity/category conflict")
            require(d.get("task") in s["tasks"] and d.get("summary") and d.get("evidence_ref"), "task, summary and evidence reference required")
            if "suggestion" in d:
                require(d["category"] in {"expression_preference", "workflow_friction"}, "bugs and authority violations are not preferences")
                overlay(d["suggestion"], s["init"]["inputs"], s["objects"])
            self.emit(con, "ObservationRecorded", {**d, "actor": actor, "provenance": "operator_report", "active": s["active"], "inputs": self.current_inputs(s), "epoch": s["epoch"]})
            return {"observation": d["id"], "truth": "reported_not_independently_verified"}
        if cmd == "resume":
            require(actor in {s["init"][k] for k in ("owner", "proposer", "evaluator")}, "unknown operator")
            run = s["runs"].get(d["run"])
            require(run, "run missing")
            result = {"run": run["id"], "task": run["task"], "config": run["config_id"], "state": self.run_state(s, run)}
            self.emit(con, "ResumeReadback", result)
            return result
        if cmd == "mvp":
            run = s["runs"].get(d["run"])
            require(run and self.run_state(s, run) == "passed", "MVP needs current passed execution")
            require(d.get("user_flow") and d.get("decision_ref"), "human MVP decision and user flow required")
            self.emit(con, "MvpAccepted", {**d, "actor": actor, "classification": "human_verifiable"})
            return {"mvp": "owner_accepted", "not_full_product_acceptance": True}
        if cmd == "checkpoint":
            require(actor in {s["init"][k] for k in ("owner", "proposer", "evaluator")}, "unknown operator")
            readiness = self.ready(s)
            self.emit(con, "Checkpoint", {**readiness, "active": s["active"], "event_cut": len(self.records(con)), "inputs": self.current_inputs(s)})
            generated = []
            if readiness["ready"]:
                self.emit(con, "SpecializationReady", {**readiness, "active": s["active"], "authority": "exploration_only"})
                # Bounded, deterministic exploration. No external LLM or spend.
                used = {o for c in s["candidates"].values() for o in c["observations"]}
                for obs in s["observations"].values():
                    if obs["id"] not in used and obs.get("suggestion"):
                        if len(s["candidates"]) >= s["init"]["candidate_budget"]:
                            break
                        cid = "AUTO-" + digest([obs["id"], s["active"], s["epoch"]])[:20]
                        body = self.candidate(s, {"id": cid, "overlay": obs["suggestion"], "observations": [obs["id"]], "hypothesis": obs["summary"]}, s["init"]["proposer"])
                        self.emit(con, "CandidateProposed", body)
                        s["candidates"][cid] = body
                        generated.append(cid)
            return {**readiness, "candidates": generated, "active_unchanged": s["active"]}
        if cmd == "propose":
            require(actor == s["init"]["proposer"], "proposer operator required")
            body = self.candidate(s, d, actor)
            self.emit(con, "CandidateProposed", body)
            return {"candidate": body["id"], "state": "isolated", "active_unchanged": s["active"]}
        if cmd == "evaluate":
            require(actor == s["init"]["evaluator"], "independent evaluator operator required")
            c = s["candidates"].get(d["candidate"])
            require(c and c["id"] not in s["evals"], "missing/already evaluated candidate; no holdout retry")
            require(c["base"] == s["active"] and c["epoch"] == s["epoch"] and c["inputs"] == self.current_inputs(s), "stale candidate")
            base = evaluate(s["configs"][c["base"]], s["init"]["eval_cases"])
            new = evaluate(c["config"], s["init"]["eval_cases"])
            safety = all(x["passed"] for x in new if x["category"] in {"authority", "regression"})
            no_regression = all(not b["passed"] or n["passed"] for b, n in zip(base, new))
            improvement = all(sum(x["passed"] for x in new if x["split"] == split) > sum(x["passed"] for x in base if x["split"] == split) for split in ("selection", "holdout"))
            complexity = len(encode(c["config"]).encode("utf-8"))
            passed = safety and no_regression and improvement and complexity <= 4096
            result = {"candidate": c["id"], "passed": passed, "safety": safety, "no_regression": no_regression, "improved_both_splits": improvement,
                      "baseline": base, "candidate_results": new, "config_bytes": complexity, "actor": actor, "suite": digest(s["init"]["eval_cases"]), "inputs": c["inputs"],
                      "scope": "deterministic_command_resolution_only", "quality_generalization": "unverified"}
            self.emit(con, "CandidateEvaluated", result)
            return result
        if cmd == "adopt":
            c = s["candidates"].get(d["candidate"])
            ev = s["evals"].get(d["candidate"])
            require(c and ev and ev["passed"], "passed independent comparison required")
            require(self.ready(s)["ready"] and c["inputs"] == self.current_inputs(s) and c["base"] == s["active"] and c["epoch"] == s["epoch"], "stale adoption evidence")
            require(d.get("decision_ref"), "explicit scoped owner decision required")
            cid = "V3-" + digest([c["config"], c["id"], s["init"]["model_context"]])[:20]
            self.emit(con, "ConfigAdopted", {"config_id": cid, "config": c["config"], "candidate": c["id"], "previous": s["active"], "decision_ref": d["decision_ref"], "actor": actor, "eval_digest": digest(ev)})
            self.emit(con, "ObjectRegistered", {"id": "RELEASE-" + cid, "type": "Release", "title": "고정된 프로젝트 V3", "purpose": c["hypothesis"], "sources": [], "relations": ["RELEASE-V2", "DECISION-AUTHORITY"]})
            return {"state": "V3_frozen", "config": cid, "in_flight_tasks": "keep_start_config"}
        if cmd == "rollback":
            require(d["config"] in s["configs"] and d["config"] != s["active"] and d.get("reason"), "known different config and reason required")
            self.emit(con, "ConfigRolledBack", {"config_id": d["config"], "previous": s["active"], "reason": d["reason"], "actor": actor})
            return {"config": d["config"], "scope": "future_tasks_only", "data_rollback": False}
        raise ContractError("unknown command")

    def candidate(self, s, d, actor):
        identifier(d["id"])
        require(self.ready(s)["ready"], "specialization readiness not met")
        require(d["id"] not in s["candidates"] and len(s["candidates"]) < s["init"]["candidate_budget"], "candidate conflict/budget exhausted")
        require(isinstance(d["observations"], list) and d["observations"] and set(d["observations"]) <= set(s["observations"]), "observation lineage required")
        require(all(s["observations"][x]["category"] in {"expression_preference", "workflow_friction"} for x in d["observations"]), "correctness/authority fixes are not preference specialization")
        require(d.get("hypothesis"), "hypothesis required")
        merged = {**s["configs"][s["active"]], **d["overlay"]}
        config = overlay(merged, s["init"]["inputs"], s["objects"])
        require(config != s["configs"][s["active"]], "no change")
        return {"id": d["id"], "base": s["active"], "epoch": s["epoch"], "config": config, "inputs": self.current_inputs(s), "observations": d["observations"], "hypothesis": d["hypothesis"], "proposer": actor, "suite": digest(s["init"]["eval_cases"])}

    def execute_run(self, con, s, run, key):
        adapter = s["init"]["test_adapter"]
        started = time.monotonic()
        env = {k: v for k, v in os.environ.items() if k in {"SystemRoot", "WINDIR", "TEMP", "TMP", "PATH"}}
        env.update({"PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8"})
        code, state = None, "failed"
        with tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr:
            try:
                result = subprocess.run([sys.executable, "-I", "-B", str(local(self.root, adapter["script"])), *adapter["args"]], cwd=self.root, env=env, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr, timeout=30)
                code = result.returncode
                state = "passed" if code == 0 else "failed"
            except subprocess.TimeoutExpired:
                state = "unknown"  # Descendants/external effects are not proven stopped.
            except OSError:
                state = "failed"
            sizes = [f.tell() for f in (stdout, stderr)]
            stdout.seek(0)
            stderr.seek(0)
            output = {"stdout": stdout.read(65536).decode("utf-8", errors="replace"), "stderr": stderr.read(65536).decode("utf-8", errors="replace")}
        if max(sizes) > 65536 and state != "unknown":
            state = "failed"
        try:
            if self.current_inputs(s) != run["inputs"]:
                state = "stale" if state != "unknown" else state
        except (OSError, ContractError):
            state = "stale" if state != "unknown" else state
        result = {**run, **output, "state": state, "returncode": code, "duration_ms": round((time.monotonic() - started) * 1000), "output_bytes": sizes}
        con.execute("BEGIN IMMEDIATE")
        latest = self.state(self.records(con))
        require(latest["runs"][run["id"]]["state"] == "unknown", "run reconciled concurrently; preserve separate outcome")
        self.emit(con, "RunFinished", result)
        con.execute("UPDATE operations SET result=? WHERE key=?", (encode(result), key))
        con.commit()
        return result

    def inspect(self):
        require(self.path.is_file(), "project is not initialized")
        no_links(self.path)
        con = sqlite3.connect(self.path.as_uri() + "?mode=ro", uri=True)
        try:
            records = self.records(con)
            s = self.state(records)
            self.check(s)
            return s, records
        finally:
            con.close()

    def view(self):
        s, records = self.inspect()
        objects = []
        for obj in s["objects"].values():
            runs = [r for r in s["runs"].values() if r["task"] == obj["id"]]
            last = runs[-1] if runs else None
            state = self.run_state(s, last) if last else "unverified"
            if obj["type"] == "Release":
                state = "active" if obj["id"] == "RELEASE-" + s["active"] or (obj["id"] == "RELEASE-V2" and s["active"].startswith("V2-")) else "pinned_history"
            rule = "active-config-events-2.0" if obj["type"] == "Release" else "task-latest-run-2.0" if obj["type"] == "Task" else "no-verification-binding-2.0"
            config_id = (s["init"]["config_id"] if obj["id"] == "RELEASE-V2" else obj["id"].removeprefix("RELEASE-")) if obj["type"] == "Release" else s["tasks"].get(obj["id"], {}).get("config_id")
            objects.append({**obj, "state": state, "human_acceptance": "pending" if obj["id"] in s["tasks"] and s["tasks"][obj["id"]]["acceptance"] != "machine_verifiable" else "not_claimed",
                            "lineage": {"rule": rule, "run": last["id"] if last else None, "inputs": last["inputs"] if last else {}, "config": config_id, "event_head": records[-1]["hash"]}})
        return {"schema": SCHEMA, "active": s["active"], "readiness": self.ready(s), "objects": objects, "dop_counts": {k: len(s[k]) for k in ("runs", "observations", "candidates", "evals")}, "event_head": records[-1]["hash"], "rule": "oop-projection-2.0", "config": s["configs"][s["active"]]}

    def resolve(self, task, command):
        s, _ = self.inspect()
        require(task in s["tasks"], "registered task required")
        pin = s["tasks"][task]
        # Only this explicit task is authorized by this call; no widening to all tasks.
        config = s["configs"][pin["config_id"]]
        runs = [r for r in s["runs"].values() if r["task"] == task]
        ready = not runs or self.run_state(s, runs[-1]) not in {"passed", "unknown"}
        for dep in pin["depends_on"]:
            dep_runs = [r for r in s["runs"].values() if r["task"] == dep]
            ready = ready and bool(dep_runs) and self.run_state(s, dep_runs[-1]) == "passed"
        result = interpret(config, command, [task] if ready else [], [task])
        return {**result, "config": pin["config_id"], "advice_only": True,
                "context_order": config["context_order"] + sorted(set(s["init"]["inputs"]) - set(config["context_order"])),
                "checklist": config["checklist"], "output_format": config["output_format"], "module_navigation": config["module_navigation"]}

    def backup(self, destination):
        target = Path(destination).absolute()
        no_links(target)
        require(not target.exists(), "backup target exists")
        self.inspect()
        target.parent.mkdir(parents=True, exist_ok=True)
        # Reserve exclusively, then use SQLite's transactionally consistent backup API.
        with target.open("xb"):
            pass
        src = self.connect()
        dst = sqlite3.connect(target)
        try:
            src.backup(dst)
            require(dst.execute("PRAGMA integrity_check").fetchone()[0] == "ok", "backup integrity failure")
            self.records(dst)
        finally:
            dst.close()
            src.close()
        return {"backup": str(target), "sha256": file_hash(target), "scope": "ledger_only_no_project_files"}

    def restore(self, source, expected_sha):
        source = Path(source).absolute()
        no_links(source)
        require(source.is_file() and file_hash(source) == expected_sha, "backup digest mismatch")
        require(not self.path.exists(), "restore only into a fresh ledger; preserve original history")
        src = sqlite3.connect(source.as_uri() + "?mode=ro", uri=True)
        try:
            require(src.execute("PRAGMA integrity_check").fetchone()[0] == "ok", "backup integrity failure")
            records = self.records(src)
            self.check(self.state(records))
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("xb"):
                pass
            dst = sqlite3.connect(self.path)
            try:
                src.backup(dst)
            finally:
                dst.close()
        finally:
            src.close()
        return {"state": "restored", "events": len(records), "source_sha256": expected_sha, "project_inputs": "recheck_required"}

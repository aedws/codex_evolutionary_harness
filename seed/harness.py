"""Local evidence-ledger core. Configured test commands only; not an OS sandbox or IAM service."""
from __future__ import annotations

import argparse
import base64
from contextlib import contextmanager
from datetime import datetime, timezone
import getpass
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import sqlite3
import stat
import subprocess
import sys
import threading
import time
import uuid

VERSION = "0.4.0"
STORAGE_VERSION = 1
RULE_VERSION = "local-verification-1"
KINDS = {"initialized", "task_defined", "run_started", "run_finished", "run_invalidated",
         "run_reconciled", "candidate_recorded"}
ZERO = "0" * 64
LIMITS = ["Only declared input files and configured test processes are observed.",
          "Policy pins constrain this CLI; they do not sandbox child processes or authenticate human approval.",
          "An OS/file owner can bypass this application; hashes are not signatures.",
          "External effects, role isolation, human acceptance and V3/V4 controllers are not implemented."]


class HarnessError(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def require(condition, message, code=2):
    if not condition:
        raise HarnessError(code, message)


def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
                      allow_nan=False).encode("utf-8")


def digest(value):
    return hashlib.sha256(value).hexdigest()


def strict_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "Duplicate JSON key: " + key)
            result[key] = value
        return result
    def invalid(value):
        raise HarnessError(2, "Non-finite JSON number: " + value)
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid)


def fields(value, required):
    require(type(value) is dict and set(value) == set(required), "Missing or unsupported fields")


def text(value):
    require(type(value) is str and bool(value.strip()), "Expected nonempty string")


def identity(value):
    text(value)
    require(bool(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}", value)), "Invalid stable ID")


def strings(value, nonempty=False):
    require(type(value) is list and (not nonempty or bool(value)), "Expected string list")
    for item in value:
        text(item)
    require(len(value) == len(set(value)), "Duplicate list entries")


def safe_path(name):
    text(name)
    path = PurePosixPath(name)
    require(bool(path.parts) and not path.is_absolute() and path.as_posix() == name and ":" not in name and "\\" not in name
            and all(p not in {".", ".."} and p.rstrip(" .") == p for p in path.parts)
            and path.parts[0].casefold() != ".harness", "Unsafe input path")


def no_links(path):
    for part in (path, *path.parents):
        try:
            info = part.lstat()
        except FileNotFoundError:
            continue
        require(not stat.S_ISLNK(info.st_mode) and not getattr(info, "st_file_attributes", 0) & 0x400,
                "Symlink/junction/reparse paths unsupported", 5)


def load(path):
    path = Path(path).absolute()
    no_links(path)
    require(path.stat().st_size <= 64 * 1024 * 1024, "Input exceeds 64 MiB limit")
    return strict_json(path.read_bytes())


def validate_policy(policy):
    fields(policy, {"schema_version", "project_id", "authority_ref", "commands", "max_output_bytes"})
    require(type(policy["schema_version"]) is int and policy["schema_version"] == 1, "Unsupported policy schema")
    identity(policy["project_id"])
    text(policy["authority_ref"])
    require(type(policy["max_output_bytes"]) is int and 1024 <= policy["max_output_bytes"] <= 1048576,
            "Output budget must be 1024..1048576 bytes")
    require(type(policy["commands"]) is dict and len(policy["commands"]) <= 32, "Commands must be an object with at most 32 tests")
    for key, command in policy["commands"].items():
        identity(key)
        fields(command, {"argv", "timeout_seconds"})
        # Repeated arguments are legitimate, unlike sets of test IDs.
        require(type(command["argv"]) is list and bool(command["argv"]), "Command argv required")
        for arg in command["argv"]:
            text(arg)
        require(Path(command["argv"][0]).is_absolute(), "Pin an absolute executable path")
        require(type(command["timeout_seconds"]) is int and 1 <= command["timeout_seconds"] <= 300,
                "Timeout must be 1..300 seconds")
    return policy


def validate_task(spec):
    fields(spec, {"schema_version", "id", "title", "purpose", "acceptance_class", "criteria",
                  "target_paths", "required_tests"})
    require(type(spec["schema_version"]) is int and spec["schema_version"] == 1, "Unsupported task schema")
    identity(spec["id"])
    text(spec["title"])
    text(spec["purpose"])
    text(spec["acceptance_class"])
    require(spec["acceptance_class"] in {"machine_verifiable", "human_verifiable", "mixed"}, "Unknown acceptance class")
    strings(spec["criteria"], True)
    strings(spec["target_paths"], True)
    strings(spec["required_tests"])
    require(len(spec["target_paths"]) <= 256 and len(spec["required_tests"]) <= 32, "Input/test population exceeds local-core limits")
    require(len({p.casefold() for p in spec["target_paths"]}) == len(spec["target_paths"]), "Case-colliding inputs")
    for path in spec["target_paths"]:
        safe_path(path)
    for test in spec["required_tests"]:
        identity(test)
    return spec


def now():
    return datetime.now(timezone.utc).isoformat()


def hash_string(value):
    require(type(value) is str and bool(re.fullmatch(r"[0-9a-f]{64}", value)), "Invalid SHA-256")


def validate_snapshot(value):
    fields(value, {"files", "executables", "commands", "task_digest", "policy_digest", "engine_digest"})
    for key in ("files", "executables", "commands"):
        require(type(value[key]) is dict, "Snapshot entries must be objects")
        for name, hashed in value[key].items():
            safe_path(name) if key == "files" else identity(name)
            hash_string(hashed)
    for key in ("task_digest", "policy_digest", "engine_digest"):
        hash_string(value[key])


def completion(results, required, snapshot, after):
    if snapshot != after:
        return "stale"
    outcomes = {item["test_id"]: item["outcome"] for item in results}
    if any(x in {"timeout", "output_limit", "effect_unknown", "environment_failure"} for x in outcomes.values()):
        return "unknown"
    if any(x == "failed" for x in outcomes.values()):
        return "failed"
    if not required or set(outcomes) != set(required):
        return "unverified"
    return "passed"


def validate_event_payloads(events):
    """Validate semantic lineage as well as bytes. Recomputed hashes alone cannot repair bad records."""
    tasks, runs, finished, operations = {}, {}, {}, set()
    common = {"schema_version", "at", "actor"}
    shapes = {
        "initialized": {"project_id", "policy_path", "policy_digest", "workspace", "engine_digest"},
        "task_defined": {"spec", "revision", "operation_key", "request_digest"},
        "run_started": {"run_id", "task_id", "task_revision", "snapshot", "operation_key", "request_digest"},
        "run_finished": {"run_id", "results", "after_snapshot", "completion"},
        "run_invalidated": {"run_id", "reason", "operation_key", "request_digest", "operator_attestation_only"},
        "run_reconciled": {"run_id", "reason", "operation_key", "request_digest", "operator_attestation_only"},
        "candidate_recorded": {"spec", "operation_key", "request_digest", "disposition"},
    }
    candidates = set()
    for event in events:
        kind, body = event["kind"], event["payload"]
        fields(body, common | shapes[kind])
        text(body["actor"])
        text(body["at"])
        require(datetime.fromisoformat(body["at"]).utcoffset() is not None, "Timestamp must be timezone-aware")
        if "operation_key" in body:
            identity(body["operation_key"])
            hash_string(body["request_digest"])
            require(body["operation_key"] not in operations, "Duplicate logical operation in ledger", 5)
            operations.add(body["operation_key"])
        if kind == "initialized":
            identity(body["project_id"])
            for name in ("workspace", "policy_path"):
                text(body[name])
                require(Path(body[name]).is_absolute(), "Genesis path must be absolute")
            hash_string(body["engine_digest"])
            hash_string(body["policy_digest"])
        elif kind == "task_defined":
            spec = validate_task(body["spec"])
            revision = tasks.get(spec["id"], {}).get("revision", 0) + 1
            require(type(body["revision"]) is int and body["revision"] == revision, "Invalid task revision lineage", 5)
            tasks[spec["id"]] = body
        elif kind == "run_started":
            identity(body["run_id"])
            require(body["run_id"] not in runs and body["task_id"] in tasks, "Run identity/task reference invalid", 5)
            require(type(body["task_revision"]) is int and body["task_revision"] == tasks[body["task_id"]]["revision"], "Run revision mismatch", 5)
            validate_snapshot(body["snapshot"])
            spec = tasks[body["task_id"]]["spec"]
            require(body["snapshot"]["task_digest"] == digest(encoded(spec)), "Run task digest mismatch", 5)
            require(set(body["snapshot"]["files"]) == set(spec["target_paths"])
                    and set(body["snapshot"]["commands"]) == set(spec["required_tests"])
                    and set(body["snapshot"]["executables"]) == set(spec["required_tests"]), "Run input population mismatch", 5)
            runs[body["run_id"]] = (body, spec)
        elif kind == "run_finished":
            require(body["run_id"] in runs and body["run_id"] not in finished, "Unknown or duplicate terminal run", 5)
            run, spec = runs[body["run_id"]]
            results = body["results"]
            require(type(results) is list, "Results must be a list")
            seen = set()
            for result in results:
                fields(result, {"test_id", "command_digest", "outcome", "exit_code", "stdout", "stderr", "duration_ms", "detail"})
                require(result["test_id"] in spec["required_tests"] and result["test_id"] not in seen, "Unexpected/duplicate test result", 5)
                seen.add(result["test_id"])
                require(result["command_digest"] == run["snapshot"]["commands"][result["test_id"]], "Command digest mismatch", 5)
                require(result["outcome"] in {"passed", "failed", "environment_failure", "timeout", "output_limit", "effect_unknown"}, "Unknown result outcome", 5)
                require(result["exit_code"] is None or type(result["exit_code"]) is int, "Invalid exit code")
                require(result["outcome"] != "passed" or result["exit_code"] == 0, "Passed result needs exit 0", 5)
                require(result["outcome"] != "failed" or (type(result["exit_code"]) is int and result["exit_code"] != 0), "Failed result needs nonzero exit", 5)
                require(type(result["duration_ms"]) is int and result["duration_ms"] >= 0, "Invalid duration")
                require(type(result["detail"]) is str, "Invalid detail")
                for key in ("stdout", "stderr"):
                    require(type(result[key]) is str, "Captured output must be base64")
                    require(len(base64.b64decode(result[key], validate=True)) <= 1048576, "Captured output exceeds budget")
            if body["after_snapshot"] is not None:
                validate_snapshot(body["after_snapshot"])
            require(body["completion"] == completion(results, spec["required_tests"], run["snapshot"], body["after_snapshot"]), "Forged completion contradicts raw observations", 5)
            finished[body["run_id"]] = body
        elif kind in {"run_invalidated", "run_reconciled"}:
            require(body["run_id"] in runs, "Unknown run annotation", 5)
            text(body["reason"])
            require(type(body["operator_attestation_only"]) is bool
                    and body["operator_attestation_only"] == (kind == "run_reconciled"), "Invalid reconciliation assertion")
        elif kind == "candidate_recorded":
            spec = body["spec"]
            fields(spec, {"id", "task_id", "scope", "hypothesis", "counterexamples", "run_ids"})
            identity(spec["id"])
            text(spec["hypothesis"])
            strings(spec["counterexamples"])
            strings(spec["run_ids"], True)
            require(spec["scope"] in {"execution-local", "project", "domain", "core"}, "Unknown candidate scope")
            require(spec["id"] not in candidates and spec["task_id"] in tasks, "Candidate identity/task conflict", 5)
            candidates.add(spec["id"])
            require(all(r in finished and runs[r][0]["task_id"] == spec["task_id"] for r in spec["run_ids"]), "Candidate evidence lineage mismatch", 5)
            require(body["disposition"] == "local_proposal_only", "Candidate cannot self-promote", 5)


def execute_process(command, root, budget):
    """Bound captured output and parent-process time; descendants are not an OS sandbox."""
    env = {k: os.environ[k] for k in ("PATH", "SystemRoot", "WINDIR", "TEMP", "TMP", "HOME", "USERPROFILE") if k in os.environ}
    env.update(PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8")
    begin = time.monotonic()
    buffers = [bytearray(), bytearray()]
    overflow = threading.Event()
    reader_error = threading.Event()
    try:
        process = subprocess.Popen(command["argv"], cwd=root, env=env, stdin=subprocess.DEVNULL,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False,
                                   creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except OSError as exc:
        return {"outcome": "environment_failure", "exit_code": None, "stdout": "", "stderr": "",
                "duration_ms": 0, "detail": str(exc)}
    def capture(stream, buf):
        try:
            while True:
                data = stream.read(4096)
                if not data:
                    break
                available = max(0, budget - len(buf))
                buf.extend(data[:available])
                if len(data) > available:
                    overflow.set()
                    break
        except OSError:
            reader_error.set()
        finally:
            stream.close()
    readers = [threading.Thread(target=capture, args=(stream, buf), daemon=True)
               for stream, buf in zip((process.stdout, process.stderr), buffers)]
    for reader in readers:
        reader.start()
    outcome = None
    try:
        while process.poll() is None:
            if overflow.is_set():
                outcome = "output_limit"
                break
            if time.monotonic() - begin > command["timeout_seconds"]:
                outcome = "timeout"
                break
            time.sleep(0.01)
    finally:
        if process.poll() is None:
            process.kill()
        process.wait()
    for reader in readers:
        reader.join(timeout=1)
    if reader_error.is_set() or any(reader.is_alive() for reader in readers):
        outcome = "effect_unknown"  # A descendant may still hold the inherited stream.
    elif overflow.is_set():
        outcome = "output_limit"
    outcome = outcome or ("passed" if process.returncode == 0 else "failed")
    return {"outcome": outcome, "exit_code": process.returncode,
            "stdout": base64.b64encode(bytes(buffers[0])).decode(),
            "stderr": base64.b64encode(bytes(buffers[1])).decode(),
            "duration_ms": round((time.monotonic() - begin) * 1000),
            "detail": "Descendant cleanup and external effects are unverified." if outcome in {"timeout", "output_limit", "effect_unknown"} else ""}


class Core:
    def __init__(self, root):
        self.root = Path(root).absolute()
        self.directory = self.root / ".harness"
        self.path = self.directory / "ledger.sqlite3"
        no_links(self.path)

    def connect(self, write=False):
        no_links(self.path)
        require(self.path.is_file(), "Runtime not initialized; reads never initialize", 5)
        mode = "rw" if write else "ro"
        db = sqlite3.connect(self.path.as_uri() + "?mode=" + mode, uri=True, timeout=2)
        try:
            require(db.execute("PRAGMA user_version").fetchone()[0] == STORAGE_VERSION, "Unsupported storage schema")
        except BaseException:
            db.close()
            raise
        return db

    @contextmanager
    def transaction(self):
        db = self.connect(True)
        try:
            db.execute("BEGIN IMMEDIATE")
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    @staticmethod
    def append(db, kind, body):
        previous = db.execute("SELECT seq,hash FROM events ORDER BY seq DESC LIMIT 1").fetchone()
        seq, prev = (previous[0] + 1, previous[1]) if previous else (1, ZERO)
        payload = dict(body, schema_version=1, at=now(), actor=getpass.getuser())
        raw = encoded(payload).decode()
        hashed = digest(encoded([seq, kind, payload, prev]))
        db.execute("INSERT INTO events VALUES(?,?,?,?,?)", (seq, kind, raw, prev, hashed))
        return seq

    @staticmethod
    def events(db):
        require(db.execute("PRAGMA quick_check").fetchone()[0] == "ok", "SQLite integrity error", 5)
        output, prev = [], ZERO
        for seq, kind, raw, before, hashed in db.execute("SELECT seq,kind,payload,previous,hash FROM events ORDER BY seq"):
            require(seq == len(output) + 1 and before == prev, "Broken event sequence/hash chain", 5)
            require(kind in KINDS, "Unsupported event kind; replay refused", 5)
            payload = strict_json(raw)
            require(type(payload) is dict, "Event payload must be an object", 5)
            require(payload.get("schema_version") == 1 and type(payload.get("schema_version")) is int, "Unsupported event schema", 5)
            require(digest(encoded([seq, kind, payload, before])) == hashed, "Event digest mismatch", 5)
            require(raw == encoded(payload).decode(), "Noncanonical stored event", 5)
            output.append({"seq": seq, "kind": kind, "payload": payload, "previous": before, "hash": hashed})
            prev = hashed
        require(bool(output) and output[0]["kind"] == "initialized"
                and sum(e["kind"] == "initialized" for e in output) == 1, "Invalid genesis", 5)
        validate_event_payloads(output)
        return output

    def read(self):
        db = self.connect()
        try:
            return self.events(db)
        finally:
            db.close()

    def initialize(self, policy_path):
        policy_path = Path(policy_path).absolute()
        policy = validate_policy(load(policy_path))
        require(self.root.is_dir(), "Create/select a project directory before init")
        if self.path.exists():
            events = self.read()
            initial = events[0]["payload"]
            require(initial["workspace"] == str(self.root) and initial["policy_path"] == str(policy_path)
                    and initial["policy_digest"] == digest(encoded(policy)), "Different initialization; never overwrite", 5)
            return {"outcome": "unchanged", "project_id": policy["project_id"]}
        self.directory.mkdir(exist_ok=True)
        ignored = self.directory / ".gitignore"
        if not ignored.exists():
            with ignored.open("xb") as stream:
                stream.write(b"*\n")
        with self.path.open("xb"):
            pass
        db = sqlite3.connect(self.path)
        try:
            db.executescript("""CREATE TABLE events(seq INTEGER PRIMARY KEY,kind TEXT NOT NULL,payload TEXT NOT NULL,
                               previous TEXT NOT NULL,hash TEXT NOT NULL UNIQUE);
                               CREATE TRIGGER preserve_events_update BEFORE UPDATE ON events BEGIN SELECT RAISE(ABORT,'append-only'); END;
                               CREATE TRIGGER preserve_events_delete BEFORE DELETE ON events BEGIN SELECT RAISE(ABORT,'append-only'); END;
                               PRAGMA user_version=1;""")
            self.append(db, "initialized", {"project_id": policy["project_id"], "policy_path": str(policy_path),
                         "policy_digest": digest(encoded(policy)), "workspace": str(self.root),
                         "engine_digest": digest(Path(__file__).read_bytes())})
            db.commit()
        finally:
            db.close()
        return {"outcome": "initialized", "project_id": policy["project_id"], "limits": LIMITS}

    def policy(self, events):
        initial = events[0]["payload"]
        require(initial["workspace"] == str(self.root), "Restored elsewhere: execution authority is not transferred", 5)
        require(initial["engine_digest"] == digest(Path(__file__).read_bytes()), "Engine drift; reviewed migration required", 5)
        policy = validate_policy(load(initial["policy_path"]))
        require(digest(encoded(policy)) == initial["policy_digest"], "Pinned policy changed; dispatch blocked", 5)
        return policy

    @staticmethod
    def task(events, task_id):
        matches = [e for e in events if e["kind"] == "task_defined" and e["payload"]["spec"]["id"] == task_id]
        require(bool(matches), "Unknown task", 5)
        event = matches[-1]
        validate_task(event["payload"]["spec"])
        return event["payload"]

    @staticmethod
    def pending(events):
        ended = {e["payload"]["run_id"] for e in events if e["kind"] == "run_reconciled"
                 or (e["kind"] == "run_finished" and not any(r["outcome"] in {"timeout", "output_limit", "effect_unknown"} for r in e["payload"]["results"]))}
        return [e for e in events if e["kind"] == "run_started" and e["payload"]["run_id"] not in ended]

    @staticmethod
    def replay_key(events, key, request):
        identity(key)
        found = [e for e in events if e["payload"].get("operation_key") == key]
        if found:
            require(found[0]["payload"]["request_digest"] == request, "Idempotency key reused with different inputs", 5)
            return found[0]
        return None

    def define_task(self, spec, key, expected_revision=0):
        validate_task(spec)
        request = digest(encoded({"kind": "task_defined", "spec": spec, "expected_revision": expected_revision}))
        with self.transaction() as db:
            events = self.events(db)
            existing = self.replay_key(events, key, request)
            if existing:
                return {"outcome": "unchanged", "event": existing["seq"]}
            require(not self.pending(events), "Pending execution; preserve inputs until reconciled", 5)
            previous = [e for e in events if e["kind"] == "task_defined" and e["payload"]["spec"]["id"] == spec["id"]]
            revision = previous[-1]["payload"]["revision"] if previous else 0
            require(type(expected_revision) is int and revision == expected_revision, "Task revision conflict", 5)
            seq = self.append(db, "task_defined", {"spec": spec, "revision": revision + 1,
                              "operation_key": key, "request_digest": request})
        return {"outcome": "recorded", "revision": revision + 1, "event": seq}

    def snapshot(self, spec, policy):
        files = {}
        for name in spec["target_paths"]:
            path = self.root / name
            no_links(path)
            require(path.is_file(), "Declared input missing: " + name, 5)
            require(path.stat().st_size <= 64 * 1024 * 1024, "Declared input exceeds 64 MiB; use a reviewed data adapter", 5)
            files[name] = digest(path.read_bytes())
        executables, commands = {}, {}
        for test in spec["required_tests"]:
            require(test in policy["commands"], "Test is not in pinned command policy: " + test, 4)
            path = Path(policy["commands"][test]["argv"][0])
            no_links(path)
            require(path.is_file(), "Configured executable unavailable", 5)
            executables[test] = digest(path.read_bytes())
            commands[test] = digest(encoded(policy["commands"][test]))
        return {"files": files, "executables": executables, "commands": commands, "task_digest": digest(encoded(spec)),
                "policy_digest": digest(encoded(policy)), "engine_digest": digest(Path(__file__).read_bytes())}

    def run(self, task_id, key):
        with self.transaction() as db:
            events = self.events(db)
            task = self.task(events, task_id)
            spec, policy = task["spec"], self.policy(events)
            require(bool(spec["required_tests"]), "Required-test population unknown/empty; no vacuous pass", 4)
            snapshot = self.snapshot(spec, policy)
            request = digest(encoded({"kind": "run_started", "task_id": task_id, "revision": task["revision"], "snapshot": snapshot}))
            replay = self.replay_key(events, key, request)
            if replay:
                finished = [e for e in events if e["kind"] == "run_finished" and e["payload"]["run_id"] == replay["payload"]["run_id"]]
                require(bool(finished), "Prior dispatch incomplete/reconciled; no blind retry", 5)
                return {"outcome": "unchanged", "run_id": replay["payload"]["run_id"], "result": finished[-1]["payload"],
                        "exit_code": 0 if finished[-1]["payload"]["completion"] == "passed" else 6}
            require(not self.pending(events), "Another execution is pending; do not steal its lease", 5)
            run_id = "RUN-" + uuid.uuid4().hex
            self.append(db, "run_started", {"run_id": run_id, "task_id": task_id, "task_revision": task["revision"],
                         "snapshot": snapshot, "operation_key": key, "request_digest": request})
        results = []
        # A crash after start leaves a visible pending run; no auto-success or automatic redispatch.
        for test in spec["required_tests"]:
            self.policy(self.read())  # Recheck the frozen policy before every dispatch.
            current = self.snapshot(spec, policy)
            if current != snapshot:
                break
            result = execute_process(policy["commands"][test], self.root, policy["max_output_bytes"])
            results.append(dict(result, test_id=test, command_digest=digest(encoded(policy["commands"][test]))))
            if result["outcome"] in {"timeout", "output_limit", "effect_unknown"}:
                break
        try:
            after = self.snapshot(spec, self.policy(self.read()))
        except (HarnessError, OSError):
            after = None
        with self.transaction() as db:
            events = self.events(db)
            require(any(e["payload"]["run_id"] == run_id for e in self.pending(events)), "Run changed during execution", 5)
            outcome = completion(results, spec["required_tests"], snapshot, after)
            self.append(db, "run_finished", {"run_id": run_id, "results": results, "after_snapshot": after, "completion": outcome})
        return {"outcome": "observed", "run_id": run_id, "status": self.status(task_id), "exit_code": 0 if outcome == "passed" else 6}

    def status(self, task_id):
        events = self.read()
        task = self.task(events, task_id)
        spec = task["spec"]
        reasons, current = [], None
        try:
            current = self.snapshot(spec, self.policy(events))
        except (HarnessError, OSError) as exc:
            reasons.append("input_or_policy_unavailable: " + str(exc))
        starts = [e for e in events if e["kind"] == "run_started" and e["payload"]["task_id"] == task_id]
        verification, evidence = "unverified", []
        if not spec["required_tests"]:
            verification = "unknown"
            reasons.append("required_tests_unknown_or_empty")
        elif starts:
            start = starts[-1]
            run = start["payload"]
            evidence.append(start["seq"])
            end = [e for e in events if e["kind"] == "run_finished" and e["payload"]["run_id"] == run["run_id"]]
            invalid = [e for e in events if e["kind"] in {"run_invalidated", "run_reconciled"} and e["payload"]["run_id"] == run["run_id"]]
            if invalid:
                evidence.extend(e["seq"] for e in invalid)
                verification = "unverified"
                reasons.append("latest_run_invalidated_or_reconciled; older pass not revived")
            elif not end:
                verification = "running"
                reasons.append("latest_attempt_has_no_terminal_observation")
            elif len(end) != 1:
                verification = "conflicted"
                reasons.append("contradictory_terminal_observations")
            else:
                evidence.append(end[0]["seq"])
                result = end[0]["payload"]
                if current is None or run["task_revision"] != task["revision"] or run["snapshot"] != current or result["after_snapshot"] != current:
                    verification = "stale"
                    reasons.append("target/task/policy/engine drift or incomplete target observation")
                else:
                    outcomes = {x["test_id"]: x["outcome"] for x in result["results"]}
                    if any(x in {"timeout", "output_limit", "effect_unknown", "environment_failure"} for x in outcomes.values()):
                        verification = "unknown"
                        reasons.append("environment/observation failure; effects outside CLI may be unknown")
                    elif any(x == "failed" for x in outcomes.values()):
                        verification = "failed"
                        reasons.append("latest_required_attempt_failed")
                    elif set(outcomes) != set(spec["required_tests"]):
                        verification = "unverified"
                        reasons.append("required_results_missing")
                    else:
                        verification = "passed"
                        reasons.append("all_configured_required_processes_exit_zero_for_exact_inputs")
        else:
            reasons.append("no_observed_run")
        acceptance = "human_pending" if spec["acceptance_class"] in {"human_verifiable", "mixed"} else (
            "machine_checks_passed" if verification == "passed" else "pending")
        return {"task_id": task_id, "title": spec["title"], "purpose": spec["purpose"], "task_revision": task["revision"],
                "verification": verification, "acceptance": acceptance, "delivery": "unobserved",
                "readiness": "configured_local_tests_only" if current is not None and bool(spec["required_tests"]) else "blocked",
                "reasons": reasons, "evidence_event_sequences": evidence, "event_watermark": events[-1]["seq"],
                "event_head": events[-1]["hash"], "input_snapshot": current, "rule_version": RULE_VERSION,
                "next_action": "inspect evidence and human acceptance; review feedback" if verification == "passed" else "resolve reasons or run with a new operation key",
                "limits": LIMITS}

    def note_run(self, run_id, reason, key, reconcile=False, confirm_stopped=False):
        text(reason)
        kind = "run_reconciled" if reconcile else "run_invalidated"
        request = digest(encoded({"kind": kind, "run_id": run_id, "reason": reason}))
        with self.transaction() as db:
            events = self.events(db)
            if self.replay_key(events, key, request):
                return {"outcome": "unchanged"}
            require(any(e["kind"] == "run_started" and e["payload"]["run_id"] == run_id for e in events), "Unknown run", 5)
            if reconcile:
                require(confirm_stopped, "Explicit operator confirmation that execution stopped is required", 4)
                require(any(e["payload"]["run_id"] == run_id for e in self.pending(events)), "Run is not pending", 5)
            self.append(db, kind, {"run_id": run_id, "reason": reason, "operation_key": key,
                        "request_digest": request, "operator_attestation_only": reconcile})
        return {"outcome": "recorded", "limits": ["Reconciliation is an operator attestation, not automatic process-death or compensation proof."]}

    def candidate(self, spec, key):
        fields(spec, {"id", "task_id", "scope", "hypothesis", "counterexamples", "run_ids"})
        identity(spec["id"])
        text(spec["scope"])
        require(spec["scope"] in {"execution-local", "project", "domain", "core"}, "Unknown scope")
        text(spec["hypothesis"])
        strings(spec["counterexamples"])
        strings(spec["run_ids"], True)
        request = digest(encoded({"kind": "candidate_recorded", "spec": spec}))
        with self.transaction() as db:
            events = self.events(db)
            self.task(events, spec["task_id"])
            if self.replay_key(events, key, request):
                return {"outcome": "unchanged"}
            require(not any(e["kind"] == "candidate_recorded" and e["payload"]["spec"]["id"] == spec["id"] for e in events), "Candidate identity conflict", 5)
            actual = {e["payload"]["run_id"] for e in events if e["kind"] == "run_started" and e["payload"]["task_id"] == spec["task_id"]}
            ended = {e["payload"]["run_id"] for e in events if e["kind"] == "run_finished"}
            require(set(spec["run_ids"]) <= actual & ended, "Candidate evidence must resolve to this task's observed runs", 5)
            self.append(db, "candidate_recorded", {"spec": spec, "operation_key": key, "request_digest": request,
                        "disposition": "local_proposal_only"})
        return {"outcome": "local_proposal_only", "candidate_id": spec["id"], "upstream_effects": []}

    def backup(self, target):
        events = self.read()
        target = Path(target).absolute()
        no_links(target)
        raw = encoded({"backup_format": 1, "events": events})
        require(len(raw) <= 64 * 1024 * 1024, "Backup exceeds local restore format budget; preserve ledger and plan migration", 5)
        if target.exists():
            require(target.is_file() and target.read_bytes() == raw, "Backup destination conflict", 5)
            return {"outcome": "unchanged", "sha256": digest(raw)}
        with target.open("xb") as stream:
            stream.write(raw)
        return {"outcome": "backup_created", "path": str(target), "sha256": digest(raw), "event_head": events[-1]["hash"]}

    def restore(self, backup_path):
        backup = load(backup_path)
        fields(backup, {"backup_format", "events"})
        require(type(backup["backup_format"]) is int and backup["backup_format"] == 1, "Unsupported backup")
        require(type(backup["events"]) is list and bool(backup["events"]), "Backup events must be a nonempty list")
        for event in backup["events"]:
            fields(event, {"seq", "kind", "payload", "previous", "hash"})
            require(type(event["seq"]) is int and event["seq"] > 0, "Event sequence must be a positive integer")
        if self.path.exists():
            require(self.read() == backup["events"], "Active ledger cannot be overwritten; preserve later history", 5)
            return {"outcome": "unchanged", "event_head": backup["events"][-1]["hash"]}
        # Validate in memory before any target write.
        db = sqlite3.connect(":memory:")
        try:
            db.execute("CREATE TABLE events(seq INTEGER PRIMARY KEY,kind TEXT,payload TEXT,previous TEXT,hash TEXT UNIQUE)")
            for event in backup["events"]:
                fields(event, {"seq", "kind", "payload", "previous", "hash"})
                db.execute("INSERT INTO events VALUES(?,?,?,?,?)", (event["seq"], event["kind"], encoded(event["payload"]).decode(), event["previous"], event["hash"]))
            events = self.events(db)
        finally:
            db.close()
        self.directory.mkdir(parents=True, exist_ok=True)
        no_links(self.path)
        ignored = self.directory / ".gitignore"
        if not ignored.exists():
            with ignored.open("xb") as stream:
                stream.write(b"*\n")
        with self.path.open("xb"):
            pass
        dest = sqlite3.connect(self.path)
        try:
            dest.executescript("CREATE TABLE events(seq INTEGER PRIMARY KEY,kind TEXT NOT NULL,payload TEXT NOT NULL,previous TEXT NOT NULL,hash TEXT NOT NULL UNIQUE); PRAGMA user_version=1;")
            for event in events:
                dest.execute("INSERT INTO events VALUES(?,?,?,?,?)", (event["seq"], event["kind"], encoded(event["payload"]).decode(), event["previous"], event["hash"]))
            dest.executescript("CREATE TRIGGER preserve_events_update BEFORE UPDATE ON events BEGIN SELECT RAISE(ABORT,'append-only'); END; CREATE TRIGGER preserve_events_delete BEFORE DELETE ON events BEGIN SELECT RAISE(ABORT,'append-only'); END;")
            dest.commit()
        finally:
            dest.close()
        return {"outcome": "restored_for_inspection", "event_head": events[-1]["hash"], "limits": ["No live ledger overwritten; execution authority is not transferred to a new workspace."]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent)
    commands = parser.add_subparsers(dest="command", required=True)
    init = commands.add_parser("init")
    init.add_argument("--policy", type=Path, required=True)
    task = commands.add_parser("task")
    task.add_argument("--spec", type=Path, required=True)
    task.add_argument("--key", required=True)
    task.add_argument("--expected-revision", type=int, default=0)
    run = commands.add_parser("run")
    run.add_argument("--task", required=True)
    run.add_argument("--key", required=True)
    for name in ("status", "view"):
        item = commands.add_parser(name)
        item.add_argument("--task", required=True)
    for name in ("invalidate", "reconcile"):
        item = commands.add_parser(name)
        item.add_argument("--run", required=True)
        item.add_argument("--reason", required=True)
        item.add_argument("--key", required=True)
        if name == "reconcile":
            item.add_argument("--confirm-stopped", action="store_true")
    candidate = commands.add_parser("candidate")
    candidate.add_argument("--spec", type=Path, required=True)
    candidate.add_argument("--key", required=True)
    commands.add_parser("check")
    commands.add_parser("list")
    backup = commands.add_parser("backup")
    backup.add_argument("--out", type=Path, required=True)
    restore = commands.add_parser("restore")
    restore.add_argument("--backup", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        core = Core(args.root)
        if args.command == "init":
            result = core.initialize(args.policy)
        elif args.command == "task":
            result = core.define_task(load(args.spec), args.key, args.expected_revision)
        elif args.command == "run":
            result = core.run(args.task, args.key)
        elif args.command in {"status", "view"}:
            result = core.status(args.task)
            if args.command == "view":
                print("# " + result["task_id"] + " — " + result["title"])
                for field in ("purpose", "verification", "acceptance", "delivery", "reasons", "evidence_event_sequences", "event_head", "rule_version", "next_action", "limits"):
                    print("\n- " + field + ": " + json.dumps(result[field], ensure_ascii=False))
                return 0
        elif args.command in {"invalidate", "reconcile"}:
            result = core.note_run(args.run, args.reason, args.key, args.command == "reconcile", getattr(args, "confirm_stopped", False))
        elif args.command == "candidate":
            result = core.candidate(load(args.spec), args.key)
        elif args.command == "backup":
            result = core.backup(args.out)
        elif args.command == "restore":
            result = core.restore(args.backup)
        else:
            events = core.read()
            if args.command == "list":
                ids = sorted({e["payload"]["spec"]["id"] for e in events if e["kind"] == "task_defined"})
                result = {"tasks": [core.status(task_id) for task_id in ids]}
            else:
                result = {"outcome": "integrity_checked", "events": len(events), "head": events[-1]["hash"], "pending_runs": [e["payload"]["run_id"] for e in core.pending(events)], "limits": LIMITS}
        print(encoded(result).decode())
        if args.command == "run":
            return result["exit_code"]
        return 0
    except HarnessError as exc:
        print(encoded({"outcome": "error", "code": exc.code, "message": str(exc)}).decode())
        return exc.code
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        print(encoded({"outcome": "error", "code": 2, "message": str(exc)}).decode())
        return 2
    except (OSError, ValueError, KeyError, TypeError, sqlite3.Error) as exc:
        print(encoded({"outcome": "error", "code": 5, "message": str(exc)}).decode())
        return 5


if __name__ == "__main__":
    # Stable CLI encoding, including redirected output on Windows non-UTF-8 locales.
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    raise SystemExit(main())

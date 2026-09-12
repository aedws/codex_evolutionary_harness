import base64
from contextlib import redirect_stdout
import importlib.util
import io
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[1] / "seed/harness.py"
spec = importlib.util.spec_from_file_location("harness_runtime", SOURCE)
h = importlib.util.module_from_spec(spec)
spec.loader.exec_module(h)


class RuntimeTests(unittest.TestCase):
    def test_policy_mutation_during_real_test_cannot_return_success(self):
        script = "import json\nfrom pathlib import Path\np=Path(" + repr(str(self.policy_path)) + ")\nv=json.loads(p.read_bytes())\nv['max_output_bytes']=8192\np.write_text(json.dumps(v))\n"
        (self.root / "check.py").write_text(script, encoding="utf-8")
        result = self.core.run("TASK-1", "mutate-policy")
        self.assertEqual(result["exit_code"], 6)
        self.assertEqual(result["status"]["verification"], "stale")
        self.assertIsNone(self.core.read()[-1]["payload"]["after_snapshot"])

    def test_dot_path_and_collection_enum_are_rejected(self):
        for spec in (dict(self.task, target_paths=["."]), dict(self.task, acceptance_class=[])):
            with self.assertRaises(h.HarnessError) as caught:
                self.core.define_task(spec, "invalid-type")
            self.assertEqual(caught.exception.code, 2)

    def test_boolean_backup_sequence_rejected_before_target_write(self):
        backup = self.base / "backup.json"
        self.core.backup(backup)
        value = json.loads(backup.read_bytes())
        value["events"][0]["seq"] = True
        backup.write_bytes(h.encoded(value))
        target = self.base / "invalid-restore"
        with self.assertRaises(h.HarnessError):
            h.Core(target).restore(backup)
        self.assertFalse(target.exists())

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / "project"
        self.root.mkdir()
        (self.root / "input.txt").write_text("original", encoding="utf-8")
        (self.root / "check.py").write_text("print('observed test output')\n", encoding="utf-8")
        self.policy = {"schema_version": 1, "project_id": "PROJECT-TEST", "authority_ref": "test-fixture-owner",
                       "commands": {"check": {"argv": [sys.executable, "check.py"], "timeout_seconds": 2}},
                       "max_output_bytes": 4096}
        self.policy_path = self.base / "policy.json"
        self.policy_path.write_bytes(h.encoded(self.policy))
        self.core = h.Core(self.root)
        self.core.initialize(self.policy_path)
        self.task = {"schema_version": 1, "id": "TASK-1", "title": "Inspect fixture", "purpose": "Exercise scoped runtime",
                     "acceptance_class": "mixed", "criteria": ["Configured check succeeds; subjective acceptance remains human"],
                     "target_paths": ["input.txt", "check.py"], "required_tests": ["check"]}
        self.core.define_task(self.task, "define-1")

    def file_state(self, root=None):
        root = root or self.root
        return {p.relative_to(root).as_posix(): (p.read_bytes(), p.stat().st_mtime_ns)
                for p in root.rglob("*") if p.is_file()}

    def candidate(self, run_id):
        return {"id": "CAND-1", "task_id": "TASK-1", "scope": "core", "hypothesis": "A scoped proposal, not proven generality",
                "counterexamples": ["Different project remains untested"], "run_ids": [run_id]}

    def test_real_run_evidence_replay_and_human_boundary(self):
        self.assertEqual(self.core.status("TASK-1")["verification"], "unverified")
        first = self.core.run("TASK-1", "run-1")
        self.assertEqual(first["status"]["verification"], "passed")
        self.assertEqual(first["status"]["acceptance"], "human_pending")
        self.assertEqual(first["status"]["delivery"], "unobserved")
        terminal = self.core.read()[-1]["payload"]
        self.assertIn(b"observed test output", base64.b64decode(terminal["results"][0]["stdout"]))
        before = self.file_state()
        replay = self.core.run("TASK-1", "run-1")
        self.assertEqual((replay["outcome"], replay["exit_code"]), ("unchanged", 0))
        self.assertEqual(self.file_state(), before)

    def test_read_commands_do_not_write_or_initialize(self):
        before = self.file_state()
        one = self.core.status("TASK-1")
        self.assertEqual(one, self.core.status("TASK-1"))
        self.core.read()
        self.assertEqual(self.file_state(), before)
        missing = self.base / "absent"
        with self.assertRaises(h.HarnessError):
            h.Core(missing).read()
        self.assertFalse(missing.exists())

    def test_task_replay_and_revision_cas(self):
        self.assertEqual(self.core.define_task(self.task, "define-1")["outcome"], "unchanged")
        modified = dict(self.task, title="Changed")
        with self.assertRaises(h.HarnessError):
            self.core.define_task(modified, "define-1")
        with self.assertRaises(h.HarnessError):
            self.core.define_task(modified, "define-2", 0)
        self.assertEqual(self.core.define_task(modified, "define-2", 1)["revision"], 2)

    def test_empty_required_tests_cannot_pass(self):
        self.core.define_task(dict(self.task, required_tests=[]), "revise", 1)
        self.assertEqual(self.core.status("TASK-1")["verification"], "unknown")
        before = self.core.read()
        with self.assertRaises(h.HarnessError):
            self.core.run("TASK-1", "run-empty")
        self.assertEqual(self.core.read(), before)

    def test_policy_denies_unlisted_direct_test(self):
        self.core.define_task(dict(self.task, required_tests=["not-granted"]), "revise", 1)
        before = self.core.read()
        with self.assertRaisesRegex(h.HarnessError, "not in pinned"):
            self.core.run("TASK-1", "unlisted")
        self.assertEqual(self.core.read(), before)

    def test_policy_drift_blocks_dispatch_and_stales_claim(self):
        self.core.run("TASK-1", "run-1")
        self.policy["commands"]["check"]["argv"].append("--different")
        self.policy_path.write_bytes(h.encoded(self.policy))
        with self.assertRaisesRegex(h.HarnessError, "Pinned policy changed"):
            self.core.run("TASK-1", "run-2")
        self.assertEqual(self.core.status("TASK-1")["verification"], "stale")

    def test_code_or_data_drift_invalidates_pass_and_old_key(self):
        self.core.run("TASK-1", "run-1")
        (self.root / "input.txt").write_text("changed", encoding="utf-8")
        self.assertEqual(self.core.status("TASK-1")["verification"], "stale")
        with self.assertRaisesRegex(h.HarnessError, "different inputs"):
            self.core.run("TASK-1", "run-1")
        self.assertEqual(self.core.run("TASK-1", "run-2")["status"]["verification"], "passed")

    def test_missing_input_does_not_reuse_old_pass(self):
        self.core.run("TASK-1", "run-1")
        (self.root / "input.txt").unlink()
        status = self.core.status("TASK-1")
        self.assertEqual((status["verification"], status["readiness"]), ("stale", "blocked"))

    def test_failure_replay_retains_nonzero_exit(self):
        (self.root / "check.py").write_text("raise SystemExit(7)\n", encoding="utf-8")
        result = self.core.run("TASK-1", "failed-1")
        self.assertEqual((result["status"]["verification"], result["exit_code"]), ("failed", 6))
        self.assertEqual(self.core.run("TASK-1", "failed-1")["exit_code"], 6)

    def test_new_failed_attempt_hides_no_older_success(self):
        # The fixture deliberately supplies an external control outside the declared input scope.
        # This tests latest-attempt ordering, not completeness of dependency discovery.
        (self.root / "check.py").write_text("from pathlib import Path\nraise SystemExit(1 if Path('fail.flag').exists() else 0)\n", encoding="utf-8")
        self.core.run("TASK-1", "pass-first")
        (self.root / "fail.flag").write_text("fail", encoding="utf-8")
        self.core.run("TASK-1", "fail-second")
        self.assertEqual(self.core.status("TASK-1")["verification"], "failed")

    def test_latest_running_attempt_is_visible_and_competing_run_blocked(self):
        self.core.run("TASK-1", "earlier-pass")
        real_execute = h.execute_process
        def during(command, root, budget):
            self.assertEqual(self.core.status("TASK-1")["verification"], "running")
            with self.assertRaises(h.HarnessError):
                self.core.run("TASK-1", "competing")
            return real_execute(command, root, budget)
        with patch.object(h, "execute_process", side_effect=during):
            self.core.run("TASK-1", "current")

    def test_crash_stays_pending_until_explicit_reconciliation(self):
        with patch.object(h, "execute_process", side_effect=RuntimeError("simulated interruption")):
            with self.assertRaises(RuntimeError):
                self.core.run("TASK-1", "crashed")
        pending = self.core.pending(self.core.read())[0]["payload"]["run_id"]
        for key in ("crashed", "new-attempt"):
            with self.assertRaises(h.HarnessError):
                self.core.run("TASK-1", key)
        with self.assertRaises(h.HarnessError):
            self.core.note_run(pending, "operator inspected", "recover", True)
        self.core.note_run(pending, "operator confirmed the interrupted fixture stopped", "recover", True, True)
        self.assertEqual(self.core.status("TASK-1")["verification"], "unverified")
        self.assertEqual(self.core.run("TASK-1", "new-after-reconcile")["exit_code"], 0)

    def test_timeout_stays_unknown_and_blocks_new_effects(self):
        (self.root / "check.py").write_text("import time\ntime.sleep(10)\n", encoding="utf-8")
        result = self.core.run("TASK-1", "timeout")
        self.assertEqual(result["status"]["verification"], "unknown")
        self.assertTrue(self.core.pending(self.core.read()))
        with self.assertRaises(h.HarnessError):
            self.core.run("TASK-1", "timeout-again")

    def test_output_limit_cannot_be_a_pass(self):
        (self.root / "check.py").write_text("print('x' * 100000)\n", encoding="utf-8")
        result = self.core.run("TASK-1", "large-output")
        self.assertEqual(result["status"]["verification"], "unknown")
        terminal = self.core.read()[-1]["payload"]
        self.assertLessEqual(len(base64.b64decode(terminal["results"][0]["stdout"])), 4096)

    def test_mutating_test_input_stales_its_result(self):
        (self.root / "check.py").write_text("from pathlib import Path\nPath('input.txt').write_text('modified')\n", encoding="utf-8")
        self.assertEqual(self.core.run("TASK-1", "mutates-input")["status"]["verification"], "stale")

    def test_invalidation_preserves_history_without_reviving_previous_pass(self):
        self.core.run("TASK-1", "first")
        second = self.core.run("TASK-1", "second")
        before = self.core.read()
        self.core.note_run(second["run_id"], "fixture acceptance no longer sufficient", "invalidate")
        self.assertEqual(self.core.read()[:len(before)], before)
        self.assertEqual(self.core.status("TASK-1")["verification"], "unverified")

    def test_candidate_remains_local_and_requires_own_run_evidence(self):
        run = self.core.run("TASK-1", "run")
        candidate = self.candidate(run["run_id"])
        self.assertEqual(self.core.candidate(candidate, "candidate")["outcome"], "local_proposal_only")
        self.assertEqual(self.core.candidate(candidate, "candidate")["outcome"], "unchanged")
        with self.assertRaises(h.HarnessError):
            self.core.candidate(dict(candidate, id="CAND-2", run_ids=["RUN-nonexistent"]), "bad-ref")
        self.core.define_task(dict(self.task, id="TASK-2"), "second-task")
        with self.assertRaises(h.HarnessError):
            self.core.candidate(dict(candidate, id="CAND-3", task_id="TASK-2"), "wrong-task")

    def test_backup_restore_preserves_event_identity_and_blocks_active_overwrite(self):
        self.core.run("TASK-1", "run")
        backup = self.base / "backup.json"
        self.core.backup(backup)
        self.assertEqual(self.core.backup(backup)["outcome"], "unchanged")
        restored = h.Core(self.base / "restored")
        restored.restore(backup)
        self.assertEqual(restored.read(), self.core.read())
        self.assertEqual(restored.restore(backup)["outcome"], "unchanged")
        with self.assertRaisesRegex(h.HarnessError, "authority is not transferred"):
            restored.run("TASK-1", "restored-run")
        self.core.define_task(dict(self.task, title="later work"), "later-task", 1)
        after = self.core.read()
        with self.assertRaises(h.HarnessError):
            self.core.restore(backup)
        self.assertEqual(self.core.read(), after)

    def test_invalid_backup_creates_no_workspace(self):
        backup = self.base / "bad.json"
        self.core.backup(backup)
        value = h.load(backup)
        value["events"][0]["hash"] = "0" * 64
        backup.write_bytes(h.encoded(value))
        missing = self.base / "not-created"
        with self.assertRaises(h.HarnessError):
            h.Core(missing).restore(backup)
        self.assertFalse(missing.exists())

    def test_semantically_forged_backup_rejected_even_with_rehashed_chain(self):
        self.core.run("TASK-1", "run")
        value = {"backup_format": 1, "events": self.core.read()}
        last = value["events"][-1]
        last["payload"]["results"][0]["exit_code"] = 13
        last["hash"] = h.digest(h.encoded([last["seq"], last["kind"], last["payload"], last["previous"]]))
        backup = self.base / "forged.json"
        backup.write_bytes(h.encoded(value))
        with self.assertRaisesRegex(h.HarnessError, "exit 0"):
            h.Core(self.base / "restored").restore(backup)

    def test_append_only_triggers_and_unknown_event_replay(self):
        db = self.core.connect(True)
        with self.assertRaises(sqlite3.DatabaseError):
            db.execute("DELETE FROM events")
        db.rollback()
        h.Core.append(db, "future_required_event", {})
        db.commit()
        db.close()
        with self.assertRaisesRegex(h.HarnessError, "Unsupported event kind"):
            self.core.read()

    def test_strict_json_types_and_unsafe_input_paths(self):
        for raw in ('{"x":1,"x":2}', '{"x":NaN}', '{"x":Infinity}'):
            with self.assertRaises(h.HarnessError):
                h.strict_json(raw)
        for policy in (dict(self.policy, schema_version=True), dict(self.policy, max_output_bytes=True)):
            with self.assertRaises(h.HarnessError):
                h.validate_policy(policy)
        for name in ("../secret", "C:/secret", "dir//file", ".harness/ledger.sqlite3", "a\\b", "FILE. "):
            with self.assertRaises(h.HarnessError):
                h.validate_task(dict(self.task, target_paths=[name]))
        with self.assertRaises(h.HarnessError):
            h.validate_task(dict(self.task, verified=True))

    def test_initialization_repeat_preserves_existing_work(self):
        before = self.file_state()
        self.assertEqual(self.core.initialize(self.policy_path)["outcome"], "unchanged")
        self.assertEqual(self.file_state(), before)

    def test_cli_failure_and_replay_return_same_failure_code(self):
        (self.root / "check.py").write_text("raise SystemExit(9)\n", encoding="utf-8")
        command = ["--root", str(self.root), "run", "--task", "TASK-1", "--key", "cli-failure"]
        for expected_outcome in ("observed", "unchanged"):
            output = io.StringIO()
            with redirect_stdout(output):
                self.assertEqual(h.main(command), 6)
            self.assertEqual(json.loads(output.getvalue())["outcome"], expected_outcome)

    def test_cli_malformed_json_rejected_without_record_mutation(self):
        invalid = self.base / "invalid.json"
        invalid.write_bytes(b'{"schema_version":')
        before = self.core.read()
        with redirect_stdout(io.StringIO()):
            self.assertEqual(h.main(["--root", str(self.root), "task", "--spec", str(invalid), "--key", "invalid"]), 2)
        self.assertEqual(self.core.read(), before)


if __name__ == "__main__":
    unittest.main()

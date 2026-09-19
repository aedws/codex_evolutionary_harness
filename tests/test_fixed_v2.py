import concurrent.futures
import importlib.util
import io
import json
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest
import zipfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "seed"))
from core import ContractError, DEFAULT, Kernel, digest, encode, engine_identity, evaluate, file_hash, interpret, overlay, validate_suite
from wiki import render


def cases():
    rows = []
    for split in ("selection", "holdout"):
        for name, command, authorized, expected in (
            ("intent", "다음 진행", ["T1"], {"action": "task", "tasks": ["T1"]}),
            ("authority", "다음 진행", [], {"action": "blocked", "tasks": []}),
            ("regression", "next", ["T2", "T1"], {"action": "task", "tasks": ["T1"]}),
            ("danger", "deploy", ["T1"], {"action": "clarify", "tasks": []}),
        ):
            rows.append({"id": split + "-" + name, "split": split, "category": name if name != "danger" else "authority", "command": command,
                         "ready": ["T1", "T2"], "authorized": authorized, "expected": expected})
    for row in rows:
        if row["split"] == "holdout":
            row["ready"] = ["H1", "H2", "H3"]
            row["authorized"] = [x.replace("T", "H") for x in row["authorized"]]
            row["expected"]["tasks"] = [x.replace("T", "H") for x in row["expected"]["tasks"]]
    return rows


def setup():
    return {"schema": 2, "owner": "owner", "proposer": "proposer", "evaluator": "evaluator", "authority_ref": "synthetic test owner choice",
            "exposure": "offline_local", "inputs": ["product.py", "test_product.py"], "test_adapter": {"script": "test_product.py", "args": []},
            "candidate_budget": 3, "model_context": "offline deterministic fixtures, no LLM", "eval_cases": cases()}


class Fixture(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "product.py").write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")
        (self.root / "test_product.py").write_text("import runpy\np = runpy.run_path('product.py')\nassert p['add'](2,3) == 5\n", encoding="utf-8")
        self.k = Kernel(self.root)
        self.counter = 0
        self.tx("init", setup())
        self.tx("object", {"id": "REQ", "type": "Requirement", "title": "덧셈", "purpose": "두 수 합계", "sources": ["product.py"], "relations": []})
        self.tx("object", {"id": "MOD", "type": "Module", "title": "계산", "purpose": "덧셈 구현", "sources": ["product.py"], "relations": ["REQ"]})
        self.task("T1")

    def tx(self, cmd, data, actor="owner", key=None):
        self.counter += 1
        result = self.k.transact(cmd, data, key or f"op-{self.counter}", actor)
        render(self.k)
        return result

    def task(self, name, deps=None):
        return self.tx("task", {"id": name, "requirement": "REQ", "purpose": "합계 구현 검증", "authority_ref": "test owner scope", "acceptance": "mixed", "depends_on": deps or []})

    def prepared(self):
        run = self.tx("run", {"task": "T1"})
        self.assertEqual(run["state"], "passed")
        self.tx("resume", {"run": run["id"]})
        self.tx("mvp", {"run": run["id"], "user_flow": "2+3 returns 5", "decision_ref": "synthetic owner acceptance"})
        self.tx("observe", {"id": "OBS", "task": "T1", "category": "expression_preference", "summary": "다음 진행을 next로 해석", "evidence_ref": "synthetic fixture", "suggestion": {"aliases": {"다음 진행": "next_ready"}}})
        return run

    def candidate(self):
        self.prepared()
        checkpoint = self.tx("checkpoint", {})
        self.assertTrue(checkpoint["ready"])
        return checkpoint["candidates"][0]


class LifecycleTests(Fixture):
    def test_full_lifecycle_fixed_v3_and_in_flight_pin(self):
        cid = self.candidate()
        prior = self.task("T2")["config"]
        result = self.tx("evaluate", {"candidate": cid}, "evaluator")
        self.assertTrue(result["passed"])
        adopted = self.tx("adopt", {"candidate": cid, "decision_ref": "synthetic owner approval"})
        self.assertEqual(self.k.resolve("T2", "다음 진행")["action"], "clarify")
        self.assertEqual(self.k.resolve("T2", "다음 진행")["config"], prior)
        self.task("T3")
        self.assertIn("채택 완료 · V3 운용 중", (self.root / "wiki/evolution.html").read_text(encoding="utf-8"))
        release = next(o for o in self.k.view()["objects"] if o["id"] == "RELEASE-" + adopted["config"])
        self.assertEqual(release["lineage"]["rule"], "active-config-events-2.0")
        resolved = self.k.resolve("T3", "다음 진행")
        self.assertEqual(resolved["tasks"], ["T3"])
        self.assertEqual(resolved["config"], adopted["config"])
        for _ in range(3):
            self.assertEqual(self.k.resolve("T3", "다음 진행"), resolved)
        run = self.tx("run", {"task": "T2"})
        self.assertEqual(run["config_id"], prior)

    def test_readiness_does_not_adopt(self):
        self.candidate()
        self.assertTrue(self.k.view()["active"].startswith("V2-"))

    def test_no_mvp_blocks(self):
        self.tx("run", {"task": "T1"})
        self.assertFalse(self.tx("checkpoint", {})["ready"])

    def test_newer_run_invalidates_old_mvp_acceptance(self):
        self.prepared()
        self.tx("run", {"task": "T1"})
        self.assertFalse(self.k.view()["readiness"]["ready"])

    def test_no_resume_blocks(self):
        run = self.tx("run", {"task": "T1"})
        self.tx("mvp", {"run": run["id"], "user_flow": "sum", "decision_ref": "owner"})
        self.assertFalse(self.tx("checkpoint", {})["ready"])

    def test_engine_drift_blocks(self):
        with patch("core.engine_identity", return_value={}):
            with self.assertRaisesRegex(ContractError, "engine drift"):
                self.k.view()

    def test_stale_input_blocks_adoption(self):
        cid = self.candidate()
        self.tx("evaluate", {"candidate": cid}, "evaluator")
        (self.root / "product.py").write_text("def add(a,b): return a-b\n", encoding="utf-8")
        self.assertEqual(next(o for o in self.k.view()["objects"] if o["id"] == "T1")["state"], "stale")
        with self.assertRaises(ContractError):
            self.tx("adopt", {"candidate": cid, "decision_ref": "owner"})

    def test_failure_supersedes_old_pass(self):
        self.prepared()
        (self.root / "product.py").write_text("def add(a,b): return 0\n", encoding="utf-8")
        self.assertEqual(self.tx("run", {"task": "T1"})["state"], "failed")
        self.assertEqual(next(o for o in self.k.view()["objects"] if o["id"] == "T1")["state"], "failed")

    def test_no_improvement_stays_v2(self):
        self.prepared()
        self.tx("propose", {"id": "C1", "overlay": {"output_format": "compact"}, "observations": ["OBS"], "hypothesis": "shorter output"}, "proposer")
        ev = self.tx("evaluate", {"candidate": "C1"}, "evaluator")
        self.assertFalse(ev["passed"])
        with self.assertRaises(ContractError):
            self.tx("adopt", {"candidate": "C1", "decision_ref": "owner"})

    def test_frozen_config_and_rollback_epoch(self):
        cid = self.candidate()
        old = self.k.view()["active"]
        self.tx("evaluate", {"candidate": cid}, "evaluator")
        self.tx("adopt", {"candidate": cid, "decision_ref": "owner"})
        self.tx("rollback", {"config": old, "reason": "synthetic rollback drill"})
        self.assertEqual(self.k.view()["active"], old)
        with self.assertRaisesRegex(ContractError, "stale"):
            self.tx("adopt", {"candidate": cid, "decision_ref": "old eval invalid after rollback"})

    def test_dependent_task_gate_and_completed_task_not_next(self):
        self.task("T2", ["T1"])
        self.assertEqual(self.k.resolve("T2", "next")["action"], "blocked")
        with self.assertRaises(ContractError):
            self.tx("run", {"task": "T2"})
        self.tx("run", {"task": "T1"})
        self.assertEqual(self.k.resolve("T1", "next")["action"], "blocked")
        self.assertEqual(self.k.resolve("T2", "next")["tasks"], ["T2"])


class IntegrityTests(Fixture):
    def test_idempotency_exactly_one_run(self):
        before = len(self.k.inspect()[1])
        a = self.tx("run", {"task": "T1"}, key="same-run")
        b = self.tx("run", {"task": "T1"}, key="same-run")
        self.assertEqual(a, b)
        self.assertEqual(len(self.k.inspect()[1]) - before, 2)

    def test_key_conflict(self):
        self.tx("checkpoint", {}, key="same")
        with self.assertRaisesRegex(ContractError, "payload conflict"):
            self.tx("checkpoint", {"different": True}, key="same")

    def test_concurrent_idempotent_checkpoint(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            answers = list(pool.map(lambda _: self.k.transact("checkpoint", {}, "parallel", "owner"), range(4)))
        self.assertTrue(all(x == answers[0] for x in answers))
        self.assertEqual(sum(e["kind"] == "Checkpoint" for e in self.k.inspect()[1]), 1)

    def test_unknown_reservation_does_not_retry(self):
        con = self.k.connect()
        request = digest({"command": "run", "data": {"task": "T1"}, "actor": "owner"})
        con.execute("INSERT INTO operations VALUES (?,?,NULL)", ("crash", request))
        self.k.emit(con, "RunStarted", {"id": "RUN-crash", "task": "T1", "state": "unknown", "config_id": self.k.view()["active"], "inputs": {}})
        con.commit()
        con.close()
        self.assertEqual(self.tx("run", {"task": "T1"}, key="crash")["retry"], "reconcile_only")
        with self.assertRaises(ContractError):
            self.tx("run", {"task": "T1"})
        self.tx("reconcile", {"run": "RUN-crash", "process_stopped": True, "reason": "injected reservation; no process was started"})
        self.assertEqual(self.tx("run", {"task": "T1"})["state"], "passed")

    def test_corrupt_event_is_detected(self):
        con = sqlite3.connect(self.k.path)
        con.execute("UPDATE events SET body='{}' WHERE seq=2")
        con.commit()
        con.close()
        with self.assertRaisesRegex(ContractError, "chain corrupted"):
            self.k.view()

    def test_readonly_inspection_preserves_ledger_bytes(self):
        before = file_hash(self.k.path)
        self.k.view()
        self.k.inspect()
        self.assertEqual(before, file_hash(self.k.path))

    def test_backup_restore_exact_chain_no_overwrite(self):
        self.prepared()
        backup = self.k.backup(self.root / "backup.db")
        target = self.root / "restored"
        target.mkdir()
        for name in ("product.py", "test_product.py"):
            shutil.copyfile(self.root / name, target / name)
        restored = Kernel(target)
        restored.restore(self.root / "backup.db", backup["sha256"])
        render(restored)
        self.assertEqual(self.k.inspect()[1], restored.inspect()[1])
        with self.assertRaises(ContractError):
            restored.restore(self.root / "backup.db", backup["sha256"])

    def test_backup_digest_mismatch(self):
        self.k.backup(self.root / "backup.db")
        with self.assertRaises(ContractError):
            Kernel(self.root / "fresh").restore(self.root / "backup.db", "0" * 64)

    def test_snapshot_change_during_run(self):
        (self.root / "test_product.py").write_text("from pathlib import Path\nPath('product.py').write_text('changed')\n", encoding="utf-8")
        self.assertEqual(self.tx("run", {"task": "T1"})["state"], "stale")

    def test_timeout_is_unknown_not_retryable(self):
        with patch("core.subprocess.run", side_effect=subprocess.TimeoutExpired("fixture", 30)):
            self.assertEqual(self.tx("run", {"task": "T1"})["state"], "unknown")

    def test_excess_output_fails(self):
        (self.root / "test_product.py").write_text("print('a'*70000)\n", encoding="utf-8")
        result = self.tx("run", {"task": "T1"})
        self.assertEqual(result["state"], "failed")
        self.assertLessEqual(len(result["stdout"]), 65536)


class BoundaryTests(Fixture):
    def test_roles_are_enforced_at_cli_boundary(self):
        cid = self.candidate()
        for actor in ("owner", "proposer", "intruder"):
            with self.assertRaises(ContractError):
                self.tx("evaluate", {"candidate": cid}, actor)
        self.tx("evaluate", {"candidate": cid}, "evaluator")
        with self.assertRaises(ContractError):
            self.tx("adopt", {"candidate": cid, "decision_ref": "invalid"}, "proposer")

    def test_forbidden_overlay_and_danger_aliases(self):
        for value in ({"permissions": ["deploy"]}, {"acceptance": "always_pass"}, {"aliases": {"deploy": "next_ready"}}, {"aliases": {"ship": "deploy"}}, {"context_order": ["../secret"]}):
            with self.subTest(value=value), self.assertRaises(ContractError):
                overlay(value, [], {})

    def test_correction_categories_do_not_become_preferences(self):
        for category in ("product_correctness", "authority_violation", "skill_change"):
            with self.subTest(category=category), self.assertRaises(ContractError):
                self.tx("observe", {"id": "BAD", "task": "T1", "category": category, "summary": "error", "evidence_ref": "fixture", "suggestion": {"output_format": "compact"}})

    def test_candidate_budget_and_single_holdout(self):
        cid = self.candidate()
        self.tx("evaluate", {"candidate": cid}, "evaluator")
        with self.assertRaises(ContractError):
            self.tx("evaluate", {"candidate": cid}, "evaluator")
        for i in range(2):
            self.tx("propose", {"id": f"C{i}", "overlay": {"output_format": "compact", "checklist": [str(i)]}, "observations": ["OBS"], "hypothesis": "test"}, "proposer")
        with self.assertRaisesRegex(ContractError, "budget"):
            self.tx("propose", {"id": "C9", "overlay": {"output_format": "compact"}, "observations": ["OBS"], "hypothesis": "test"}, "proposer")

    def test_suite_cannot_weaken_hard_oracle(self):
        suite = cases()
        suite[-1]["expected"] = {"action": "task", "tasks": ["H1"]}
        with self.assertRaisesRegex(ContractError, "oracle mismatch"):
            validate_suite(suite)

    def test_suite_missing_holdout_rejected(self):
        with self.assertRaises(ContractError):
            validate_suite(cases()[:4])

    def test_duplicate_split_input_rejected(self):
        rows = cases()
        rows[-1] = {**rows[0], "id": "duplicate", "split": "holdout"}
        with self.assertRaisesRegex(ContractError, "duplicate evaluation"):
            validate_suite(rows)

    def test_reserved_wiki_object_id_rejected(self):
        with self.assertRaises(ContractError):
            self.tx("object", {"id": "index", "type": "Module", "title": "bad", "purpose": "bad", "sources": ["product.py"], "relations": []})

    def test_at_most_one_authorized_task(self):
        config = {**DEFAULT, "aliases": {"go": "next_ready"}}
        self.assertEqual(interpret(config, "go", ["A", "B", "C"], ["B", "C"])["tasks"], ["B"])
        self.assertEqual(interpret(config, "go", ["A"], ["B"])["action"], "blocked")

    def test_no_proposal_before_ready(self):
        with self.assertRaises(ContractError):
            self.tx("propose", {"id": "C", "overlay": {}, "observations": [], "hypothesis": "ready narration"}, "proposer")


class WikiTests(Fixture):
    def test_wiki_hierarchy_objects_not_run_nodes(self):
        self.prepared()
        result = render(self.k)
        self.assertEqual(result["objects"], 6)
        self.assertTrue((self.root / "wiki/Requirement.html").exists())
        self.assertTrue((self.root / "wiki/T1.html").exists())
        self.assertFalse(list((self.root / "wiki").glob("RUN-*.html")))
        text = (self.root / "wiki/T1.html").read_text(encoding="utf-8")
        for marker in ("연결 상태", "이 상태가 생성된 이유", "RUN-", "REQ.html"):
            self.assertIn(marker, text)

    def test_manual_wiki_edits_block_exploration(self):
        self.prepared()
        (self.root / "wiki/index.html").write_text("manual edit", encoding="utf-8")
        self.assertFalse(self.k.view()["readiness"]["ready"])
        with self.assertRaisesRegex(ContractError, "user edit"):
            render(self.k)

    def test_html_escaped(self):
        self.tx("object", {"id": "EVIL", "type": "Module", "title": "<script>alert(1)</script>", "purpose": "<img src=x>", "sources": ["product.py"], "relations": ["REQ"]})
        text = (self.root / "wiki/EVIL.html").read_text(encoding="utf-8")
        self.assertNotIn("<script>", text)
        self.assertIn("&lt;script&gt;", text)

    def test_deterministic_state_replay(self):
        self.prepared()
        a = self.k.view()
        b = Kernel(self.root).view()
        self.assertEqual(a, b)


class RepeatedSpecializationTests(unittest.TestCase):
    def test_three_fresh_v2_trials_produce_contract_compatible_v3(self):
        results = []
        for i in range(3):
            fixture = Fixture()
            fixture.setUp()
            try:
                fixture.prepared()
                cid = fixture.tx("checkpoint", {})["candidates"][0]
                result = fixture.tx("evaluate", {"candidate": cid}, "evaluator")
                fixture.tx("adopt", {"candidate": cid, "decision_ref": f"synthetic trial {i}"})
                results.append((result["passed"], result["safety"], fixture.k.view()["active"]))
            finally:
                fixture.doCleanups()
        self.assertTrue(all(passed and safety and version.startswith("V3-") for passed, safety, version in results))


class DistributionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location("distributor", ROOT / "scripts/seed.py")
        cls.dist = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.dist)

    def test_distribution_install_replay_and_auto_draft(self):
        _, payload, receipt = self.dist.load()
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "project"
            self.assertEqual(self.dist.install(p, payload, receipt)["state"], "installed")
            self.assertTrue((p / "wiki/index.html").exists())
            self.assertEqual(self.dist.install(p, payload, receipt)["state"], "unchanged")
            (p / "core.py").write_text("drift", encoding="utf-8")
            with self.assertRaises(ContractError):
                self.dist.install(p, payload, receipt)

    def test_existing_files_not_overwritten(self):
        _, payload, receipt = self.dist.load()
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            (p / "AGENTS.md").write_text("owner instructions", encoding="utf-8")
            with self.assertRaises(ContractError):
                self.dist.install(p, payload, receipt)
            self.assertEqual((p / "AGENTS.md").read_text(), "owner instructions")

    def test_package_reproducible(self):
        _, payload, receipt = self.dist.load()
        data = self.dist.package(payload, receipt)
        self.assertEqual(data, self.dist.package(payload, receipt))
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            self.assertIn("wiki/index.html", archive.namelist())
            self.assertIn("wiki/Requirement.html", archive.namelist())

    def test_partial_install_blocks_retry(self):
        _, payload, receipt = self.dist.load()
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            (p / ".harness-seed.pending.json").write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(ContractError, "partial installation"):
                self.dist.install(p, payload, receipt)


if __name__ == "__main__":
    unittest.main()

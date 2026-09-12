"""Real CLI flows from installed seed files, including concurrent process dispatch."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import seed


class InstalledRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.project = self.base / "project"
        _, payload, receipt = seed.load_seed(ROOT)
        seed.initialize(self.project, payload, receipt, False)
        self.engine = self.project / "harness.py"
        self.write("product.py", "def add(a, b): return a + b\n")
        self.write("data.json", '{"expected": 5}\n')
        self.write("checks.py", "import json\nfrom product import add\nfrom pathlib import Path\nassert add(2,3)==json.loads(Path('data.json').read_text())['expected']\nprint('actual product assertion passed')\n")
        self.policy = self.base / "policy.json"
        self.policy.write_text(json.dumps({"schema_version": 1, "project_id": "CLI-FIXTURE",
            "authority_ref": "synthetic-test-only", "commands": {"check": {
                "argv": [sys.executable, "checks.py"], "timeout_seconds": 10}}, "max_output_bytes": 4096}), encoding="utf-8")
        spec = {"schema_version": 1, "id": "TASK-CLI", "title": "덧셈 검사",
                "purpose": "Verify installed local execution path", "acceptance_class": "mixed",
                "criteria": ["Addition agrees with declared data", "Human acceptance remains pending"],
                "target_paths": ["product.py", "data.json", "checks.py"], "required_tests": ["check"]}
        self.write("task.json", json.dumps(spec))
        self.cli("init", "--policy", str(self.policy))
        self.cli("task", "--spec", "task.json", "--key", "define")

    def write(self, name, value):
        (self.project / name).write_text(value, encoding="utf-8")

    def cli(self, *args, expected=0, root=None, markdown=False):
        command = [sys.executable, "-B", str(self.engine)]
        if root is not None:
            command += ["--root", str(root)]
        result = subprocess.run(command + list(args), cwd=self.project, capture_output=True,
                                text=True, encoding="utf-8", timeout=20)
        self.assertEqual(result.returncode, expected, (result.stdout, result.stderr))
        self.assertFalse(result.stderr)
        return result.stdout if markdown else json.loads(result.stdout)

    def test_installed_seed_failure_feedback_and_isolated_restore(self):
        first = self.cli("run", "--task", "TASK-CLI", "--key", "pass-1")
        self.assertEqual(first["status"]["verification"], "passed")
        self.assertEqual(first["status"]["acceptance"], "human_pending")
        before = self.cli("check")
        self.assertEqual(self.cli("run", "--task", "TASK-CLI", "--key", "pass-1")["outcome"], "unchanged")
        self.assertEqual(self.cli("check"), before)
        self.write("data.json", '{"expected": 6}\n')
        self.assertEqual(self.cli("status", "--task", "TASK-CLI")["verification"], "stale")
        failed = self.cli("run", "--task", "TASK-CLI", "--key", "failure-1", expected=6)
        self.assertEqual(failed["status"]["verification"], "failed")
        self.cli("run", "--task", "TASK-CLI", "--key", "failure-1", expected=6)
        self.write("data.json", '{"expected": 5}\n')
        self.assertEqual(self.cli("run", "--task", "TASK-CLI", "--key", "fixed-1")["status"]["verification"], "passed")
        candidate = {"id": "CAND-CLI", "task_id": "TASK-CLI", "scope": "core",
                     "hypothesis": "Data expectation changes need explicit review", "counterexamples": ["No independent project evaluated"],
                     "run_ids": [failed["run_id"]]}
        self.write("candidate.json", json.dumps(candidate))
        self.assertEqual(self.cli("candidate", "--spec", "candidate.json", "--key", "candidate-1")["outcome"], "local_proposal_only")
        view = self.cli("view", "--task", "TASK-CLI", markdown=True)
        for required in ("TASK-CLI", "덧셈 검사", "purpose", "evidence_event_sequences", "rule_version", "human_pending"):
            self.assertIn(required, view)
        backup = self.base / "backup.json"
        self.cli("backup", "--out", str(backup))
        inspection = self.base / "inspection"
        self.cli("restore", "--backup", str(backup), root=inspection)
        self.assertEqual(self.cli("check", root=inspection)["head"], self.cli("check")["head"])
        self.assertEqual(self.cli("restore", "--backup", str(backup), root=inspection)["outcome"], "unchanged")
        self.cli("run", "--task", "TASK-CLI", "--key", "no-transferred-authority", root=inspection, expected=5)
        self.cli("invalidate", "--run", first["run_id"], "--reason", "Fixture later observation", "--key", "annotate")
        self.cli("restore", "--backup", str(backup), expected=5)

    def test_two_real_cli_processes_cannot_dispatch_concurrently(self):
        self.write("checks.py", "from pathlib import Path\nimport time\nPath('started.marker').write_text('started')\ntime.sleep(2)\n")
        process = subprocess.Popen([sys.executable, "-B", str(self.engine), "run", "--task", "TASK-CLI", "--key", "first"],
                                   cwd=self.project, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            deadline = time.monotonic() + 10
            while not (self.project / "started.marker").exists() and time.monotonic() < deadline:
                time.sleep(0.02)
            self.assertTrue((self.project / "started.marker").exists())
            blocked = self.cli("run", "--task", "TASK-CLI", "--key", "second", expected=5)
            self.assertIn("pending", blocked["message"])
            out, err = process.communicate(timeout=10)
            self.assertEqual(process.returncode, 0, (out, err))
            self.assertEqual(self.cli("check")["events"], 4)
        finally:
            if process.poll() is None:
                process.kill()
                process.communicate(timeout=5)


if __name__ == "__main__":
    unittest.main()

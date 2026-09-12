import importlib.util
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("seed", ROOT / "scripts/seed.py")
seed = importlib.util.module_from_spec(spec)
spec.loader.exec_module(seed)


class SeedTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.target = Path(self.temp.name) / "project"
        self.manifest, self.payload, self.receipt = seed.load_seed()

    def test_seed_is_clean_and_archive_contains_only_seed_and_receipt(self):
        data = seed.archive(self.payload, self.receipt)
        self.assertEqual(data, seed.archive(self.payload, self.receipt))
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            self.assertEqual(set(archive.namelist()), set(self.payload) | {seed.RECEIPT})
            for name in self.payload:
                self.assertEqual(archive.read(name), self.payload[name])
            self.assertEqual(json.loads(archive.read("docs/harness/objects.json")), [])
            self.assertEqual(archive.read("docs/harness/events.jsonl"), b"")

    def test_dry_run_does_not_create_target(self):
        self.assertEqual(seed.initialize(self.target, self.payload, self.receipt, True)["outcome"], "planned")
        self.assertFalse(self.target.exists())

    def test_install_preserves_unrelated_file_and_replay_is_noop(self):
        self.target.mkdir()
        extra = self.target / "app.txt"
        extra.write_bytes(b"existing work")
        self.assertEqual(seed.initialize(self.target, self.payload, self.receipt, False)["outcome"], "installed")
        before = {p.relative_to(self.target).as_posix(): (p.read_bytes(), p.stat().st_mtime_ns)
                  for p in self.target.rglob("*") if p.is_file()}
        self.assertEqual(seed.initialize(self.target, self.payload, self.receipt, False)["outcome"], "unchanged")
        after = {p.relative_to(self.target).as_posix(): (p.read_bytes(), p.stat().st_mtime_ns)
                 for p in self.target.rglob("*") if p.is_file()}
        self.assertEqual(before, after)
        self.assertEqual(extra.read_bytes(), b"existing work")

    def test_conflict_checks_all_files_before_writing(self):
        self.target.mkdir()
        (self.target / "AGENTS.md").write_bytes(b"owner rules")
        with self.assertRaises(seed.SeedError) as raised:
            seed.initialize(self.target, self.payload, self.receipt, False)
        self.assertEqual(raised.exception.code, 5)
        self.assertEqual(list(self.target.iterdir()), [self.target / "AGENTS.md"])
        self.assertEqual((self.target / "AGENTS.md").read_bytes(), b"owner rules")

    def test_changed_project_records_are_not_reinstalled(self):
        seed.initialize(self.target, self.payload, self.receipt, False)
        path = self.target / "docs/harness/events.jsonl"
        path.write_bytes(b'{"event_id":"PROJECT-WORK"}\n')
        with self.assertRaises(seed.SeedError):
            seed.initialize(self.target, self.payload, self.receipt, False)
        self.assertIn(b"PROJECT-WORK", path.read_bytes())

    def test_partial_write_remains_visible_and_retry_is_blocked(self):
        original = seed.write_new
        def failing(path, data):
            if path.name == "BOOTSTRAP_PROMPT.md":
                raise OSError("simulated disk full")
            return original(path, data)
        with patch.object(seed, "write_new", side_effect=failing):
            with self.assertRaises(seed.SeedError) as raised:
                seed.initialize(self.target, self.payload, self.receipt, False)
        self.assertEqual(raised.exception.code, 9)
        self.assertTrue((self.target / seed.PENDING).exists())
        self.assertTrue((self.target / "AGENTS.md").exists())
        with self.assertRaises(seed.SeedError) as raised:
            seed.initialize(self.target, self.payload, self.receipt, False)
        self.assertEqual(raised.exception.code, 5)

    def test_pending_installation_blocks_competing_writer(self):
        self.target.mkdir()
        (self.target / seed.PENDING).write_bytes(b"{}")
        with self.assertRaises(seed.SeedError):
            seed.initialize(self.target, self.payload, self.receipt, False)
        self.assertFalse((self.target / "AGENTS.md").exists())

    def test_source_tamper_and_unsupported_manifest_are_rejected(self):
        copy = Path(self.temp.name) / "source"
        shutil.copytree(ROOT / "seed", copy / "seed")
        shutil.copyfile(ROOT / "seed-manifest.json", copy / "seed-manifest.json")
        (copy / "seed/AGENTS.md").write_bytes(b"tampered")
        with self.assertRaises(seed.SeedError):
            seed.load_seed(copy)
        manifest = dict(self.manifest, schema_version=999)
        (copy / "seed-manifest.json").write_bytes(seed.encoded(manifest))
        with self.assertRaises(seed.SeedError):
            seed.load_seed(copy)

    def test_unsafe_paths_are_rejected(self):
        for name in ("../outside", "C:/outside", "/outside", "a/../b", "a\\b", "a//b", "a./b "):
            self.assertFalse(seed.safe_relative(name), name)

    def test_non_directory_ancestor_does_not_write(self):
        self.target.mkdir()
        (self.target / "docs").write_bytes(b"user file")
        with self.assertRaises(seed.SeedError):
            seed.initialize(self.target, self.payload, self.receipt, False)
        self.assertFalse((self.target / "AGENTS.md").exists())

    def test_receipt_mismatch_cannot_overwrite_installation(self):
        seed.initialize(self.target, self.payload, self.receipt, False)
        receipt = self.target / seed.RECEIPT
        receipt.write_bytes(b"{}")
        with self.assertRaises(seed.SeedError):
            seed.initialize(self.target, self.payload, self.receipt, False)
        self.assertEqual(receipt.read_bytes(), b"{}")

    def test_installation_inside_distributor_is_rejected(self):
        with self.assertRaises(seed.SeedError):
            seed.initialize(ROOT / "must-not-create", self.payload, self.receipt, True)
        self.assertFalse((ROOT / "must-not-create").exists())

    def test_reparse_point_is_rejected_before_writing(self):
        class ReparseInfo:
            st_mode = 0
            st_file_attributes = 0x400
        with patch.object(Path, "lstat", return_value=ReparseInfo()):
            with self.assertRaises(seed.SeedError) as raised:
                seed.initialize(self.target, self.payload, self.receipt, False)
        self.assertEqual(raised.exception.code, 5)
        self.assertFalse(self.target.exists())


if __name__ == "__main__":
    unittest.main()

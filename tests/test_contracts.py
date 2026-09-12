import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import check_contracts
from seed import SeedError


class ContractDistributionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        shutil.copytree(ROOT / "seed", self.root / "seed")
        shutil.copyfile(ROOT / "seed-manifest.json", self.root / "seed-manifest.json")

    def change_json(self, relative, mutation):
        path = self.root / "seed" / relative
        value = json.loads(path.read_bytes())
        mutation(value)
        path.write_bytes((json.dumps(value) + "\n").encode())
        # An internally hash-consistent package must still fail semantic defaults/coverage checks.
        manifest_path = self.root / "seed-manifest.json"
        manifest = json.loads(manifest_path.read_bytes())
        manifest["files"][relative] = hashlib.sha256(path.read_bytes()).hexdigest()
        manifest_path.write_bytes((json.dumps(manifest) + "\n").encode())

    def test_all_goals_and_clauses_resolve_without_runtime_claim(self):
        result = check_contracts.check(self.root)
        self.assertEqual((result["goals"], result["clauses"]), (17, 23))

    def test_missing_goal_rejected(self):
        self.change_json("docs/harness/contracts/coverage.json", lambda x: x["goals"].pop())
        with self.assertRaisesRegex(SeedError, "17 goals"):
            check_contracts.check(self.root)

    def test_duplicate_goal_rejected(self):
        self.change_json("docs/harness/contracts/coverage.json",
                         lambda x: x["goals"][1].update(goal_id="G01"))
        with self.assertRaisesRegex(SeedError, "17 goals"):
            check_contracts.check(self.root)

    def test_dangling_clause_rejected(self):
        self.change_json("docs/harness/contracts/coverage.json",
                         lambda x: x["goals"][0]["clauses"][0].update(id="V99"))
        with self.assertRaisesRegex(SeedError, "missing/mismatched"):
            check_contracts.check(self.root)

    def test_inherited_submission_authority_rejected(self):
        self.change_json("docs/harness/feedback/config.json",
                         lambda x: x["permissions"].update(submit=True))
        with self.assertRaisesRegex(SeedError, "authority"):
            check_contracts.check(self.root)

    def test_fake_runtime_verification_rejected(self):
        self.change_json("docs/harness/contracts/coverage.json",
                         lambda x: x.update(runtime_status="verified"))
        with self.assertRaisesRegex(SeedError, "runtime-verified"):
            check_contracts.check(self.root)

    def test_origin_evidence_not_shipped_in_example(self):
        self.change_json("docs/harness/templates/feedback-candidate.example.json",
                         lambda x: x.update(evidence_refs=["PRIVATE-ORIGIN-EVIDENCE"]))
        with self.assertRaisesRegex(SeedError, "live identities or evidence"):
            check_contracts.check(self.root)

    def test_review_area_cannot_be_omitted(self):
        self.change_json("docs/harness/contracts/review-cases.json", lambda x: x["areas"].pop())
        with self.assertRaisesRegex(SeedError, "Seven review areas"):
            check_contracts.check(self.root)

    def test_review_rejection_case_cannot_be_removed(self):
        self.change_json("docs/harness/contracts/review-cases.json",
                         lambda x: x["areas"][0]["scenarios"].pop(1))
        with self.assertRaisesRegex(SeedError, "accept/reject/inconclusive"):
            check_contracts.check(self.root)

    def test_planned_review_cannot_claim_observed_runtime_success(self):
        self.change_json("docs/harness/contracts/review-cases.json",
                         lambda x: x["areas"][0]["scenarios"][0].update(runtime_status="passed"))
        with self.assertRaisesRegex(SeedError, "planned accept"):
            check_contracts.check(self.root)

    def test_review_template_cannot_inherit_an_approver(self):
        self.change_json("docs/harness/templates/assurance-review.example.json",
                         lambda x: x["areas"]["A06"].update(capability_grants_and_authority="owner-approved"))
        with self.assertRaisesRegex(SeedError, "unobserved fields unknown"):
            check_contracts.check(self.root)

    def test_review_template_cannot_drop_uncertainty_field(self):
        self.change_json("docs/harness/templates/assurance-review.example.json",
                         lambda x: x["areas"]["A07"].pop("margins_estimator_uncertainty"))
        with self.assertRaisesRegex(SeedError, "unobserved fields unknown"):
            check_contracts.check(self.root)


if __name__ == "__main__":
    unittest.main()

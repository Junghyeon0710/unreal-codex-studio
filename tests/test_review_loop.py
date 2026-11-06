import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import review_loop as loop


class ReviewLoopTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "Source").mkdir()
        self.source = self.root / "Source/Door.cpp"
        self.source.write_text("initial", encoding="utf-8")
        self.journal = self.root / ".studio/door.json"
        self.evidence = self.root / "result.json"
        self.evidence.write_text('{"status":"passed"}', encoding="utf-8")
        self.init()

    def tearDown(self):
        self.temp.cleanup()

    def init(self, max_repairs=3):
        return loop.initialize(self.journal, self.root, "implementation-agent", "review-agent", "coordinator",
                               ["Source"], ["Door opens and closes"], ["runtime"], max_repairs)

    def submit(self, addressed=()):
        return loop.submit(self.journal, "implementation-agent", "Implemented behavior", addressed)

    def report(self, verdict="approve"):
        item = loop.load(self.journal)["rounds"][-1]
        findings = [] if verdict == "approve" else [{"id": "R1", "severity": "P1", "location": "Source/Door.cpp:1",
            "trigger": "Last occupant leaves", "consequence": "Door stays open", "evidence": "Runtime assertion fails"}]
        return {"digest": item["snapshot"]["digest"], "verdict": verdict, "summary": "Independent inspection", "findings": findings}

    def approve(self):
        return loop.review(self.journal, "review-agent", self.report())

    def verify(self, status="passed"):
        return loop.verify(self.journal, "coordinator", "runtime", status, self.evidence, "Observed actual test result")

    def test_requires_distinct_participants(self):
        self.journal.unlink()
        with self.assertRaises(ValueError):
            loop.initialize(self.journal, self.root, "same", "same", "coordinator", ["Source"], ["works"], ["runtime"])

    def test_rejects_self_review_and_unknown_verifier(self):
        self.submit()
        with self.assertRaises(ValueError):
            loop.review(self.journal, "implementation-agent", self.report())
        with self.assertRaises(ValueError):
            loop.verify(self.journal, "implementation-agent", "runtime", "passed", self.evidence, "Test")

    def test_review_and_required_checks_needed(self):
        self.assertFalse(loop.status(self.journal)["ready"])
        self.submit()
        self.verify()
        self.assertEqual(loop.status(self.journal)["state"], "awaiting_review")
        self.approve()
        self.assertTrue(loop.status(self.journal)["ready"])

    def test_failure_or_not_run_never_passes_gate(self):
        self.submit(); self.approve()
        for result in ("failed", "not_run"):
            self.verify(result)
            self.assertFalse(loop.status(self.journal)["ready"])
        self.verify("passed")
        self.assertTrue(loop.status(self.journal)["ready"])

    def test_source_change_addition_and_deletion_stale_approval(self):
        self.submit(); self.approve(); self.verify()
        self.source.write_text("changed")
        self.assertEqual(loop.status(self.journal)["state"], "stale")
        self.source.write_text("initial")
        extra = self.root / "Source/New.h"
        extra.write_text("new")
        self.assertEqual(loop.status(self.journal)["state"], "stale")
        extra.unlink(); self.source.unlink()
        self.assertEqual(loop.status(self.journal)["state"], "stale")

    def test_reviewer_cannot_approve_changed_or_wrong_digest(self):
        self.submit()
        report = self.report(); report["digest"] = "another-snapshot"
        with self.assertRaises(ValueError):
            loop.review(self.journal, "review-agent", report)
        report = self.report(); self.source.write_text("changed")
        with self.assertRaises(ValueError):
            loop.review(self.journal, "review-agent", report)

    def test_stale_pending_review_can_be_explicitly_superseded_without_losing_history(self):
        self.submit(); self.verify()
        previous = loop.load(self.journal)["rounds"][0]
        old_report = self.report()
        self.source.write_text("changed before review")
        with self.assertRaises(ValueError):
            loop.review(self.journal, "review-agent", old_report)
        with self.assertRaises(ValueError):
            self.submit()
        loop.submit(self.journal, "implementation-agent", "Source changed during pending review",
                    supersede_pending=True)
        data = loop.load(self.journal)
        self.assertEqual(data["rounds"][0], previous)
        self.assertEqual(data["events"][-2]["kind"], "pending_review_superseded")
        self.assertEqual(data["events"][-2]["replacement_round"], 2)
        self.assertEqual(loop.status(self.journal)["state"], "awaiting_review")
        with self.assertRaises(ValueError):
            loop.review(self.journal, "review-agent", old_report)
        self.approve()
        self.assertFalse(loop.status(self.journal)["ready"])
        self.verify()
        self.assertTrue(loop.status(self.journal)["ready"])

    def test_pending_supersession_requires_changed_source_and_obeys_repair_budget(self):
        self.submit()
        with self.assertRaises(ValueError):
            loop.submit(self.journal, "implementation-agent", "No change", supersede_pending=True)
        self.journal.unlink(); self.init(max_repairs=0); self.submit()
        self.source.write_text("changed")
        with self.assertRaises(ValueError):
            loop.submit(self.journal, "implementation-agent", "Changed", supersede_pending=True)
        self.assertEqual(len(loop.load(self.journal)["rounds"]), 1)

    def test_evidence_changes_invalidate_completion(self):
        self.submit(); self.approve(); self.verify()
        self.evidence.write_text('{"status":"failed"}')
        self.assertFalse(loop.status(self.journal)["ready"])
        self.evidence.unlink()
        self.assertFalse(loop.status(self.journal)["ready"])

    def test_repair_requires_findings_and_fresh_review_and_verification(self):
        self.submit(); self.verify()
        loop.review(self.journal, "review-agent", self.report("request_changes"))
        self.source.write_text("fixed")
        with self.assertRaises(ValueError):
            self.submit()
        self.submit(["R1"])
        self.assertFalse(loop.status(self.journal)["ready"])
        self.approve()
        self.assertEqual(loop.status(self.journal)["state"], "awaiting_verification")
        self.verify()
        self.assertTrue(loop.status(self.journal)["ready"])
        self.assertEqual(len(loop.load(self.journal)["rounds"]), 2)

    def test_repair_budget_and_immutable_review(self):
        self.journal.unlink(); self.init(max_repairs=0)
        self.submit()
        loop.review(self.journal, "review-agent", self.report("request_changes"))
        with self.assertRaises(ValueError):
            self.approve()
        with self.assertRaises(ValueError):
            self.submit(["R1"])
        self.assertEqual(loop.status(self.journal)["state"], "repair_limit_reached")

    def test_scope_escape_and_journal_in_scope_rejected(self):
        self.journal.unlink()
        for scope in ("../outside", ".studio", "."):
            with self.assertRaises(ValueError):
                loop.initialize(self.journal, self.root, "a", "b", "c", [scope], ["works"], ["runtime"])


if __name__ == "__main__":
    unittest.main()

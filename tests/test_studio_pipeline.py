import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import studio_pipeline as p


class StudioTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root/'Source').mkdir()
        self.source = self.root/'Source/door.cpp'
        self.source.write_text('initial')
        self.journal = self.root/'journal.json'
        self.people = {r: {'id': 'host-' + r, 'model': 'gpt-6.1-sol'} for r in p.ROLES}
        self.people['coordinator'] = {'id': 'host-coordinator', 'model': 'gpt-6-astra'}
        p.initialize(self.journal, self.root, self.people, ['Source'], ['door works'], profile='strict-five')
        self.submit()

    def tearDown(self):
        self.tmp.cleanup()

    def submit(self):
        self.digest = p.submit(self.journal, 'host-implementer', 'source ready')['snapshot']['digest']
        p.review(self.journal, 'host-reviewer', {'digest': self.digest, 'verdict': 'approve',
            'summary': 'independent source inspection', 'findings': []})

    def record(self, stage):
        evidence = self.root/(stage + '.txt')
        evidence.write_text('observed ' + stage)
        return p.record(self.journal, 'host-' + stage, stage, 'passed', evidence, 'observed result', self.digest)

    def editor(self):
        p.custody(self.journal, 'host-editor', 'acquire')
        self.record('editor')
        p.custody(self.journal, 'host-editor', 'release')

    def complete(self):
        self.editor()
        self.record('verification')
        self.record('qa')
        self.assertTrue(p.status(self.journal)['ready'])

    def test_all_five_specialists_required(self):
        self.assertFalse(p.status(self.journal)['ready'])
        self.editor()
        self.assertFalse(p.status(self.journal)['ready'])
        self.record('verification')
        self.assertFalse(p.status(self.journal)['ready'])
        self.record('qa')
        self.assertTrue(p.status(self.journal)['ready'])

    def test_separation_and_explicit_models(self):
        self.people['qa']['id'] = 'HOST-IMPLEMENTER'
        with self.assertRaises(ValueError):
            p.initialize(self.root/'bad.json', self.root, self.people, ['Source'], ['x'], profile='strict-five')
        self.people['qa']['id'] = 'host-qa'
        self.people['qa']['model'] = 'other-model'
        with self.assertRaises(ValueError):
            p.initialize(self.root/'bad.json', self.root, self.people, ['Source'], ['x'], profile='strict-five')
        with self.assertRaises(ValueError):
            p.custody(self.journal, 'host-coordinator', 'acquire')

    def test_custody_and_order(self):
        with self.assertRaises(ValueError): self.record('editor')
        with self.assertRaises(ValueError): self.record('qa')
        p.custody(self.journal, 'host-editor', 'acquire')
        with self.assertRaises(ValueError): p.custody(self.journal, 'host-editor', 'acquire')
        self.record('editor')
        with self.assertRaises(ValueError): self.record('verification')
        with self.assertRaises(ValueError): p.submit(self.journal, 'host-implementer', 'repair')
        self.assertFalse(p.status(self.journal)['ready'])
        p.custody(self.journal, 'host-editor', 'release')
        self.record('verification')
        self.record('qa')
        self.assertTrue(p.status(self.journal)['ready'])

    def test_stale_source_and_evidence(self):
        self.complete()
        self.source.write_text('changed')
        self.assertFalse(p.status(self.journal)['ready'])
        with self.assertRaises(ValueError): self.record('qa')
        self.submit()
        with self.assertRaises(ValueError):
            p.record(self.journal, 'host-editor', 'editor', 'passed', self.root/'editor.txt', 'old', self.digest)
        self.complete()
        (self.root/'editor.txt').write_text('tampered')
        self.assertFalse(p.status(self.journal)['ready'])
        with self.assertRaises(ValueError): self.record('qa')

    def test_old_artifact_and_digest_rejected(self):
        old = self.root/'old.txt'
        old.write_text('old')
        self.submit()
        p.custody(self.journal, 'host-editor', 'acquire')
        with self.assertRaisesRegex(ValueError, 'predates'):
            p.record(self.journal, 'host-editor', 'editor', 'passed', old, 'old', self.digest)
        with self.assertRaisesRegex(ValueError, 'digest'):
            p.record(self.journal, 'host-editor', 'editor', 'passed', old, 'old', 'stale')

    def test_rerun_invalidates_downstream(self):
        self.complete()
        self.editor()
        self.assertFalse(p.status(self.journal)['ready'])
        with self.assertRaises(ValueError): self.record('qa')
        with self.assertRaisesRegex(ValueError, 'predates'):
            p.record(self.journal, 'host-verification', 'verification', 'passed',
                self.root/'verification.txt', 'stale replay', self.digest)

    def test_bounded_repairs(self):
        for _ in range(3): self.submit()
        with self.assertRaisesRegex(ValueError, 'limit'):
            self.submit()


if __name__ == '__main__': unittest.main()

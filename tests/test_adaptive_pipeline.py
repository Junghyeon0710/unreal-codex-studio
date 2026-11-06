import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
import studio_pipeline as p


class AdaptiveTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        (self.root/'Content').mkdir();self.source=self.root/'Content/material.txt';self.source.write_text('initial')
        self.j=self.root/'session.json'
        self.people={'coordinator':{'id':'actual-manager','model':'gpt-6-astra'},
                     'artist':{'id':'actual-artist','model':'gpt-6.1-sol'}}
        self.stages=[{'name':'content-check','owner':'artist','checks':['inspect'], 'depends_on':[]}]
        p.initialize(self.j,self.root,self.people,['Content'],['material correct'],stages=self.stages)

    def tearDown(self):self.tmp.cleanup()

    def submit(self,actor='actual-artist'):
        self.digest=p.submit(self.j,actor,'Task snapshot')['snapshot']['digest']

    def record(self,name='content-check',checks=None,actor='actual-artist'):
        evidence=self.root/(name+'.json');evidence.write_text('{}')
        return p.record(self.j,actor,name,'passed',evidence,'observed',self.digest,checks or {'inspect':'passed'})

    def test_one_expert_no_editor_review_qa(self):
        self.submit();self.assertFalse(p.status(self.j)['ready'])
        self.record();self.assertTrue(p.status(self.j)['ready'])
        with self.assertRaisesRegex(ValueError,'No independent reviewer'):
            p.review(self.j,'actual-artist',{})
        with self.assertRaisesRegex(ValueError,'editor owner'):
            p.custody(self.j,'actual-artist','acquire')

    def test_selected_checks_cannot_be_missing_or_failed(self):
        self.submit()
        with self.assertRaisesRegex(ValueError,'every selected'):
            self.record(checks={'other':'passed'})
        with self.assertRaisesRegex(ValueError,'all selected'):
            self.record(checks={'inspect':'failed'})
        with self.assertRaisesRegex(ValueError,'not selected'):
            self.record(name='qa')
        self.assertFalse(p.status(self.j)['ready'])

    def test_reviewer_optional_but_independent_when_selected(self):
        self.people['reviewer']={'id':'ACTUAL-ARTIST','model':'gpt-6.1-sol'}
        with self.assertRaisesRegex(ValueError,'reviewer must differ'):
            p.revise_plan(self.j,'actual-manager','Review useful',self.people,self.stages)
        self.people['reviewer']['id']='actual-reviewer'
        p.revise_plan(self.j,'actual-manager','Executable behavior needs independent review',self.people,self.stages)
        self.submit();self.assertEqual('awaiting_review',p.status(self.j)['state'])
        with self.assertRaises(ValueError):self.record()
        p.review(self.j,'actual-reviewer',{'digest':self.digest,'verdict':'approve','summary':'reviewed','findings':[]})
        self.record();self.assertTrue(p.status(self.j)['ready'])

    def test_plan_change_preserves_failure_requires_fresh_snapshot(self):
        self.submit();self.record()
        old=p.load(self.j)['rounds'][0]
        p.revise_plan(self.j,'actual-manager','Acceptance narrowed: read-only material inspection suffices',self.people,[])
        self.assertEqual('plan_changed',p.status(self.j)['state'])
        self.assertEqual(old,p.load(self.j)['rounds'][0])
        self.submit('actual-manager');self.assertTrue(p.status(self.j)['ready'])
        self.assertEqual(2,len(p.load(self.j)['studio']['plan_history']))

    def test_replan_pending_review_without_source_change(self):
        self.people['reviewer']={'id':'actual-reviewer','model':'gpt-6.1-sol'}
        p.revise_plan(self.j,'actual-manager','Review warranted',self.people,self.stages)
        self.submit()
        p.revise_plan(self.j,'actual-manager','Reassign independent reviewer',dict(self.people,reviewer={'id':'new-reviewer','model':'gpt-6.1-sol'}),self.stages)
        self.submit();self.assertEqual('awaiting_review',p.status(self.j)['state'])
        self.assertIsNone(p.load(self.j)['rounds'][0]['review'])

    def test_dependencies_stale_replay_and_independent_branches(self):
        stages=self.stages+[{'name':'followup','owner':'artist','checks':['inspect'],'depends_on':['content-check']},
                            {'name':'parallel','owner':'artist','checks':['inspect'],'depends_on':[]}]
        p.revise_plan(self.j,'actual-manager','Two dependent observations plus independent check',self.people,stages)
        self.submit()
        with self.assertRaises(ValueError):self.record('followup')
        self.record();self.record('followup');self.record('parallel');self.assertTrue(p.status(self.j)['ready'])
        self.record();self.assertFalse(p.status(self.j)['ready'])
        with self.assertRaisesRegex(ValueError,'predates'):
            p.record(self.j,'actual-artist','followup','passed',self.root/'followup.json','old',self.digest,{'inspect':'passed'})
        self.record('followup');self.assertTrue(p.status(self.j)['ready'])
        (self.root/'parallel.json').write_text('tampered');self.assertFalse(p.status(self.j)['ready'])
        self.source.write_text('changed');self.assertEqual('stale',p.status(self.j)['state'])

    def test_asset_only_custody_and_baseline(self):
        stages=[dict(self.stages[0],uses_editor=True)]
        p.revise_plan(self.j,'actual-manager','Actual material editor work',self.people,stages)
        p.custody(self.j,'actual-artist','acquire')
        self.source.write_text('edited by asset specialist')
        with self.assertRaises(ValueError):self.submit()
        with self.assertRaises(ValueError):p.custody(self.j,'actual-artist','acquire')
        p.custody(self.j,'actual-artist','release')
        self.submit('actual-manager')
        with self.assertRaises(ValueError):self.record()
        p.custody(self.j,'actual-artist','acquire');self.record()
        self.assertFalse(p.status(self.j)['ready'])
        p.custody(self.j,'actual-artist','release');self.assertTrue(p.status(self.j)['ready'])

    def test_review_only_uses_coordinator_baseline(self):
        people={'coordinator':self.people['coordinator'],
                'reviewer':{'id':'actual-reviewer','model':'gpt-6.1-sol'}}
        j=self.root/'review-only.json'
        p.initialize(j,self.root,people,['Content'],['review existing content'])
        snap=p.submit(j,'actual-manager','Existing content baseline')['snapshot']['digest']
        self.assertEqual('awaiting_review',p.status(j)['state'])
        p.review(j,'actual-reviewer',{'digest':snap,'verdict':'approve','summary':'read-only inspection','findings':[]})
        self.assertTrue(p.status(j)['ready'])

    def test_historical_strict_journal_remains_loadable(self):
        people={r:{'id':r,'model':'gpt-6.1-sol'} for r in p.ROLES}
        people['coordinator']={'id':'manager','model':'gpt-6-astra'}
        j=self.root/'legacy.json';p.initialize(j,self.root,people,['Content'],['door'],profile='strict-five')
        self.assertNotIn('profile',p.load(j)['studio'])
        p.submit(j,'implementer','historical');self.assertEqual('awaiting_review',p.status(j)['state'])


if __name__=='__main__':unittest.main()

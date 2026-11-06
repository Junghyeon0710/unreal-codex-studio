import contextlib
import io
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import validate
import studio_pipeline as pipeline


class ModelConfigurationTests(unittest.TestCase):
    def test_optional_or_alternate_config_identifiers(self):
        for config in ({},{'model':'other-provider/model-v2'},{'model':'gpt-6-astra'}):
            validate.validate_model(config)
        validate.validate_model({'default_subagent_model':'custom-model'},'default_subagent_model')

    def test_invalid_config_values(self):
        for value in ('',' ','model name','\tmodel',None,17,[],{},'INHERIT'):
            with self.subTest(value=value),self.assertRaises(ValueError):
                validate.validate_model({'model':value})

    def test_validator_accepts_all_role_omissions_and_alternate_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)
            for name in ('.codex','.agents'):
                shutil.copytree(validate.ROOT/name,target/name,ignore=shutil.ignore_patterns('__pycache__'))
            config=target/'.codex/config.toml'
            original=config.read_text(encoding='utf-8')
            config.write_text(original.replace('model = "gpt-6-astra"','model = "custom/root-v1"'),encoding='utf-8')
            for path in (target/'.codex/agents').glob('*.toml'):
                s=path.read_text(encoding='utf-8')
                path.write_text('\n'.join(line for line in s.splitlines() if not line.startswith('model ='))+'\n',encoding='utf-8')
            with patch.object(validate,'ROOT',target),contextlib.redirect_stdout(io.StringIO()):
                self.assertFalse(validate.main())
            config.write_text('\n'.join(line for line in original.splitlines() if not line.startswith('model ='))+'\n',encoding='utf-8')
            with patch.object(validate,'ROOT',target),contextlib.redirect_stdout(io.StringIO()):
                self.assertFalse(validate.main())
            role=target/'.codex/agents/code-reviewer.toml'
            role.write_text(role.read_text(encoding='utf-8')+'model = "alternate/review-v3"\n',encoding='utf-8')
            with patch.object(validate,'ROOT',target),contextlib.redirect_stdout(io.StringIO()):
                self.assertFalse(validate.main())
            role.write_text(role.read_text(encoding='utf-8').replace('alternate/review-v3',''),encoding='utf-8')
            with patch.object(validate,'ROOT',target),contextlib.redirect_stdout(io.StringIO()):
                self.assertTrue(validate.main())

    def test_participants_require_resolved_model_not_config_omission(self):
        for value in ('custom/provider-v2','gpt-6.1-sol'):
            self.assertEqual(value,pipeline.actual_model(value,'worker'))
        for value in (None,'',' ',False,[],{},'inherit','InHeRiT','model name'):
            with self.subTest(value=value),self.assertRaises(ValueError):
                pipeline.actual_model(value,'worker')

    def test_adaptive_alternate_models_preserve_separation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'Source').mkdir()
            people={'coordinator':{'id':'actual-manager','model':'other/director'},
                    'code':{'id':'actual-author','model':'custom/code'},
                    'reviewer':{'id':'actual-reviewer','model':'another/review'}}
            journal=root/'alternate.json'
            data=pipeline.initialize(journal,root,people,['Source'],['source only'])
            self.assertEqual(people,data['studio']['participants'])
            people['reviewer']['id']='ACTUAL-AUTHOR'
            with self.assertRaisesRegex(ValueError,'reviewer must differ'):
                pipeline.initialize(root/'invalid.json',root,people,['Source'],['source only'])
            people['reviewer']['id']='actual-reviewer'
            del people['code']['model']
            with self.assertRaisesRegex(ValueError,'resolved model'):
                pipeline.initialize(root/'missing.json',root,people,['Source'],['source only'])


if __name__=='__main__':unittest.main()

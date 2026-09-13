import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('bootstrap_gate',ROOT/'seed/bootstrap.py')
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)


class BootstrapTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        self.ids=['REQ-1','TASK-1','DEC-1','MOD-1','TEST-1','REL-1']
        for name,next_page in [('a.html','b.html'),('b.html','c.html'),('c.html','a.html')]:
            (self.root/name).write_text(' '.join(self.ids)+f'<a href="{next_page}">next</a>',encoding='utf-8')
        self.binding={'schema_version':1,'profile':b.PROFILE,'entrypoint':'a.html','documents':['a.html','b.html','c.html'],
            'categories':{k:['a.html'] for k in b.CATEGORIES},'object_views':[{'id':i,'type':t,'path':'a.html','purpose':'Fixture purpose','source_refs':['b.html'],'next_action':'Inspect evidence','rule':'fixture-1','acceptance_class':'mixed','unknowns':['Human acceptance pending']} for i,t in zip(self.ids,sorted(b.TYPES))],
            'relations':[{'from':'REQ-1','to':'TASK-1','basis':'confirmed_by_user'}],
            'journeys':[{'role':r,'paths':['a.html','b.html','c.html']} for r in ['owner','developer','reviewer']],
            'input_sha256':{n:hashlib.sha256((self.root/n).read_bytes()).hexdigest() for n in ['a.html','b.html','c.html']},'validation_task':'TASK-1'}

    def test_complete_artifacts_are_only_wiki_ready(self):
        self.assertEqual(b.artifacts(self.root,self.binding)['state'],'wiki_ready')
        self.assertEqual(b.artifacts(self.root,self.binding),b.artifacts(self.root,self.binding))

    def test_api_pass_without_wiki_cannot_be_bootstrap_ready(self):
        with self.assertRaises(b.BootstrapError):b.artifacts(self.root,{'api_tests':'passed'})

    def test_mandatory_categories_and_types_cannot_be_omitted(self):
        value=copy.deepcopy(self.binding);value['categories'].pop('onboarding')
        with self.assertRaisesRegex(b.BootstrapError,'nine'):b.artifacts(self.root,value)
        value=copy.deepcopy(self.binding);value['object_views'].pop()
        with self.assertRaises(b.BootstrapError):b.artifacts(self.root,value)

    def test_stale_missing_and_unsafe_source_rejected(self):
        (self.root/'b.html').write_text('changed')
        with self.assertRaisesRegex(b.BootstrapError,'stale'):b.artifacts(self.root,self.binding)
        (self.root/'b.html').unlink()
        with self.assertRaisesRegex(b.BootstrapError,'missing'):b.artifacts(self.root,self.binding)
        with self.assertRaisesRegex(b.BootstrapError,'Unsafe'):b.path(self.root,'../escape')

    def test_orphan_and_dangling_relationship_rejected(self):
        value=copy.deepcopy(self.binding);value['relations'][0]['to']='MISSING'
        with self.assertRaisesRegex(b.BootstrapError,'endpoint'):b.artifacts(self.root,value)
        (self.root/'a.html').write_text(' '.join(self.ids))
        value=copy.deepcopy(self.binding);value['input_sha256']['a.html']=hashlib.sha256((self.root/'a.html').read_bytes()).hexdigest()
        with self.assertRaisesRegex(b.BootstrapError,'Orphan'):b.artifacts(self.root,value)

    def test_duplicate_keys_and_self_approval_field_rejected(self):
        with self.assertRaises(b.BootstrapError):b.strict('{"schema_version":1,"schema_version":1}')
        value=copy.deepcopy(self.binding);value['approved']=True
        with self.assertRaises(b.BootstrapError):b.artifacts(self.root,value)

    def test_final_readiness_requires_current_real_run(self):
        shutil.copyfile(ROOT/'seed/harness.py',self.root/'harness.py')
        spec=importlib.util.spec_from_file_location('fixture_runtime',self.root/'harness.py')
        h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
        policy={'schema_version':1,'project_id':'FIXTURE','authority_ref':'fixture-owner','commands':{'check':{'argv':[sys.executable,'-c','print("fixture check")'],'timeout_seconds':2}},'max_output_bytes':1024}
        (self.root/'policy.json').write_bytes(h.encoded(policy));core=h.Core(self.root);core.initialize(self.root/'policy.json')
        core.define_task({'schema_version':1,'id':'TASK-1','title':'Bootstrap fixture','purpose':'Observe real run','acceptance_class':'mixed','criteria':['Fixture check'],'target_paths':['a.html'],'required_tests':['check']},'register')
        with self.assertRaisesRegex(b.BootstrapError,'not currently passed'):b.evaluate(self.root,self.binding)
        core.run('TASK-1','check-1')
        result=b.evaluate(self.root,self.binding)
        self.assertEqual(result['state'],'bootstrap_ready');self.assertEqual(result['human_acceptance'],'human_pending')

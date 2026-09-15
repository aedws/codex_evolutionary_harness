import copy
import importlib.util
import json
from pathlib import Path
import struct
import shutil
import subprocess
import sys
import tempfile
import unittest
import zlib

ROOT=Path(__file__).resolve().parents[1]
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
q=module('quality_tests','seed/wiki_quality.py');w=module('quality_draft','seed/wiki_draft.py')


class QualityTests(unittest.TestCase):
    def setUp(self):
        self.data=json.loads((ROOT/'seed/docs/wiki/draft-input.json').read_bytes())
        generated=w.bundle(self.data);self.files={n:b for n,b in generated.items() if n.endswith('.html')};self.contract=json.loads(generated['quality-contract.json'])
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
    def image(self,width):
        # Synthetic transport fixture only: no claim that a browser was observed.
        def chunk(name,data):return struct.pack('!I',len(data))+name+data+struct.pack('!I',zlib.crc32(name+data)&0xffffffff)
        raw=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('!IIBBBBB',width,800,8,2,0,0,0))+chunk(b'IDAT',zlib.compress((b'\0'+b'\xff'*(width*3))*800))+chunk(b'IEND',b'')
        name=str(width)+'.png';(self.root/name).write_bytes(raw);return {'path':name,'sha256':q.sha(raw)}
    def review(self):
        report=q.audit(self.files,self.contract)
        images={width:self.image(width) for width in (390,1280)}
        names=['index.html','workflows.html','DRAFT-TASK-001.html']
        value=dict(schema_version=1,profile=q.PROFILE,snapshot=report['snapshot'],observer='synthetic-test-not-human-approval',reference={'label':'synthetic reference fixture','image':images[1280]},observations=[dict(page=n,width=width,html_sha256=q.sha(self.files[n]),image=images[width],checks={k:True for k in q.CHECKS}) for n in names for width in (390,1280)])
        return report,value
    def test_deterministic_two_domain_drafts_keep_pending_acceptance(self):
        for title in ['Warehouse','Garden']:
            d=copy.deepcopy(self.data);d['project_name']=title;bundle=w.bundle(d);r=json.loads(bundle['quality.json'])
            self.assertEqual(r['state'],'structure_passed');self.assertEqual(r['visual'],'pending');self.assertFalse(r['bootstrap_ready'])
            self.assertEqual(bundle,w.bundle(d))
    def test_no_graph_broken_link_huge_prose_and_script_block(self):
        for replacement in [b'<script>bad</script>',b'<a href="missing.html">missing</a>',b'<p>'+b'x'*601+b'</p>',b'<svg><use href="https://example.test/x.svg"></use></svg>',b'<style>@import "external.css"</style>',b'<p>unclosed']:
            files=dict(self.files);files['index.html']+=replacement
            self.assertEqual(q.audit(files,self.contract)['state'],'blocked')
        files=dict(self.files);files['DRAFT-TASK-001.html']=files['DRAFT-TASK-001.html'].replace(b'data-graph-profile="object-node-map-1"',b'data-disabled="true"')
        self.assertIn('object_graph_missing',[f['code'] for f in q.audit(files,self.contract)['failures']])
    def test_inventory_kind_and_hierarchy_cannot_weaken_checks(self):
        for fault in ['topic','kind','parent','type']:
            c=copy.deepcopy(self.contract)
            if fault=='topic':c['pages'].pop('start')
            if fault=='kind':c['pages']['DRAFT-TASK-001']['kind']='topic'
            if fault=='parent':c['pages']['workflows']['parent']='product'
            if fault=='type':c['pages']['DRAFT-TASK-001']['object_type']='requirement'
            with self.assertRaises(ValueError):q.audit(self.files,c)
    def test_project_requires_current_sources_and_rejects_path_escape(self):
        c=copy.deepcopy(self.contract);c['mode']='project'
        self.assertEqual(q.audit(self.files,c,self.root)['state'],'blocked')
        (self.root/'source.md').write_bytes(b'owner intent')
        c['source_bindings']=[dict(page=k,path='source.md',sha256=q.sha(b'owner intent')) for k in c['pages']]
        self.assertEqual(q.audit(self.files,c,self.root)['state'],'structure_passed')
        (self.root/'source.md').write_bytes(b'new decision')
        self.assertEqual(q.audit(self.files,c,self.root)['state'],'blocked')
        c['source_bindings'][0]['path']='../secret'
        with self.assertRaises(ValueError):q.audit(self.files,c,self.root)
    def test_valid_visual_receipt_records_observation_not_human_acceptance(self):
        report,review=self.review();out=q.visual_check(report,review,self.root,self.files,self.contract)
        self.assertEqual(out['state'],'visual_review_recorded');self.assertEqual(out['human_acceptance'],'human_pending');self.assertFalse(out['bootstrap_ready'])
    def test_stale_missing_failed_duplicate_wrong_width_visual_receipts_block(self):
        report,original=self.review()
        for fault in ['snapshot','html','missing','failed','duplicate','image','width']:
            v=copy.deepcopy(original)
            if fault=='snapshot':v['snapshot']='old'
            if fault=='html':v['observations'][0]['html_sha256']='0'*64
            if fault=='missing':v['observations'].pop()
            if fault=='failed':v['observations'][0]['checks']['no_clipping']=False
            if fault=='duplicate':v['observations'][1]=copy.deepcopy(v['observations'][0])
            if fault=='image':v['observations'][0]['image']['sha256']='0'*64
            if fault=='width':v['observations'][0]['image']=v['observations'][1]['image']
            with self.assertRaises(ValueError,msg=fault):q.visual_check(report,v,self.root,self.files,self.contract)
    def test_bootstrap_must_cover_the_same_artifacts(self):
        hashes={'site/'+n:q.sha(raw) for n,raw in self.files.items()}
        b=dict(entrypoint='site/index.html',documents=list(hashes),input_sha256=hashes)
        q.bind_bootstrap(b,'site',self.files)
        b['input_sha256']['site/index.html']='0'*64
        with self.assertRaises(ValueError):q.bind_bootstrap(b,'site',self.files)
        b['entrypoint']='other/index.html'
        with self.assertRaises(ValueError):q.bind_bootstrap(b,'site',self.files)
    def test_cli_template_pending_and_draft_never_ready(self):
        out=self.root/'site';out.mkdir()
        for n,raw in self.files.items():(out/n).write_bytes(raw)
        (self.root/'contract.json').write_bytes(q.encoded(self.contract))
        args=[sys.executable,'-B',str(ROOT/'seed/wiki_quality.py')]
        common=['--root',str(self.root),'--site','site','--contract','contract.json']
        result=subprocess.run(args+['check']+common,capture_output=True);self.assertEqual(result.returncode,0,result.stdout)
        result=subprocess.run(args+['review-template']+common,capture_output=True);self.assertEqual(result.returncode,0,result.stdout)
        template=json.loads(result.stdout);self.assertTrue(all(v is False for o in template['observations'] for v in o['checks'].values()))
        result=subprocess.run(args+['gate']+common,capture_output=True);self.assertEqual(result.returncode,2)
        self.assertIn('Draft never',json.loads(result.stdout)['reason'])
    def test_duplicate_json_keys_are_not_silently_accepted(self):
        p=self.root/'bad.json';p.write_bytes(b'{"mode":"draft","mode":"project"}')
        with self.assertRaises(ValueError):q.read_json(p)

    def test_real_project_gate_requires_tested_quality_and_matching_bootstrap(self):
        # End-to-end synthetic local owner fixture, not a real deployment or visual approval.
        for name in ('wiki_quality.py','harness.py','bootstrap.py','wiki_core.py'):
            shutil.copyfile(ROOT/'seed'/name,self.root/name)
        for name in ('source.md','decision.json','adapter.py','access_test.py'):(self.root/name).write_text('# synthetic fixture\n')
        (self.root/'site').mkdir()
        for name,raw in self.files.items():(self.root/'site'/name).write_bytes(raw)
        c=copy.deepcopy(self.contract);c['mode']='project';c['source_bindings']=[dict(page=k,path='source.md',sha256=q.sha((self.root/'source.md').read_bytes())) for k in c['pages']]
        (self.root/'contract.json').write_bytes(q.encoded(c))
        report,review=self.review();review['snapshot']=q.audit(self.files,c,self.root)['snapshot'];(self.root/'review.json').write_bytes(q.encoded(review))
        spec=importlib.util.spec_from_file_location('quality_core_fixture',self.root/'wiki_core.py');wc=importlib.util.module_from_spec(spec);spec.loader.exec_module(wc)
        tree=dict(schema_version=1,profile=wc.PROFILE,roles={'owner':'Synthetic owner'},access={'root_read':['owner'],'overrides':{}},root='index',nodes=[dict(id=k,title=k,parent=v['parent'],page=k+'.html',grants={'read':['owner'],'edit':[],'approve':[],'execute':[]}) for k,v in c['pages'].items()],interview={'status':'confirmed','decision_ref':'decision.json','policy_digest':''},adapter={'kind':'authenticated_read_only','source_paths':['adapter.py'],'test_paths':['access_test.py'],'required_tests':['access-fixture']})
        tree['interview']['policy_digest']=wc.policy_digest(tree);(self.root/'tree.json').write_bytes(q.encoded(tree))
        for ident in c['pages']:
            p=self.root/'docs/wiki/roles/owner'/(ident+'.html');p.parent.mkdir(parents=True,exist_ok=True);p.write_text(wc.navigation(tree,ident,'owner'),encoding='utf-8')
        spec=importlib.util.spec_from_file_location('quality_bootstrap_fixture',self.root/'bootstrap.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
        hashes={'site/'+n:q.sha(raw) for n,raw in self.files.items()}
        for p in self.root.rglob('*'):
            if p.is_file():hashes[p.relative_to(self.root).as_posix()]=q.sha(p.read_bytes())
        binding=dict(schema_version=1,profile=b.PROFILE,entrypoint='site/index.html',documents=['site/'+n for n in self.files],categories={key:['site/start.html'] for key in b.CATEGORIES},object_views=[dict(id=o['id'],type=o['type'],path='site/'+o['id']+'.html',purpose='Synthetic fixture',source_refs=['source.md'],next_action='Inspect',rule=q.PROFILE,acceptance_class='mixed',unknowns=['Not real acceptance']) for o in self.data['objects']],relations=[dict(**{'from':self.data['objects'][0]['id'],'to':self.data['objects'][1]['id']},basis='confirmed_by_user')],journeys=[{'role':'owner','paths':['site/index.html','site/workflows.html','site/DRAFT-TASK-001.html']}],input_sha256=hashes,validation_task='TASK-QUALITY',wiki_contract='tree.json')
        (self.root/'binding.json').write_bytes(q.encoded(binding))
        spec=importlib.util.spec_from_file_location('quality_runtime_fixture',self.root/'harness.py');h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
        command=[sys.executable,'-B','wiki_quality.py','check','--site','site','--contract','contract.json']
        policy=dict(schema_version=1,project_id='PROJECT-QUALITY',authority_ref='synthetic-fixture-only',commands={'wiki-quality':{'argv':command,'timeout_seconds':10},'access-fixture':{'argv':[sys.executable,'-B','access_test.py'],'timeout_seconds':10}},max_output_bytes=65536)
        (self.root/'policy.json').write_bytes(q.encoded(policy));core=h.Core(self.root);core.initialize(self.root/'policy.json')
        task=dict(schema_version=1,id='TASK-QUALITY',title='Synthetic quality',purpose='Check local gate composition',acceptance_class='mixed',criteria=['Fixture checks only'],target_paths=['wiki_quality.py','contract.json','source.md','tree.json','decision.json','adapter.py','access_test.py'],required_tests=['wiki-quality','access-fixture'])
        core.define_task(task,'define-quality');self.assertEqual(core.run('TASK-QUALITY','run-quality')['status']['verification'],'passed')
        args=[sys.executable,'-B','wiki_quality.py','gate','--site','site','--contract','contract.json','--review','review.json','--binding','binding.json']
        result=subprocess.run(args,cwd=self.root,capture_output=True);self.assertEqual(result.returncode,0,result.stdout)
        self.assertEqual(json.loads(result.stdout)['state'],'wiki_review_ready');self.assertEqual(json.loads(result.stdout)['human_acceptance'],'human_pending')
        (self.root/'source.md').write_text('changed source')
        result=subprocess.run(args,cwd=self.root,capture_output=True);self.assertEqual(result.returncode,2)


if __name__=='__main__':unittest.main()

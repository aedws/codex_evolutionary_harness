import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from urllib.parse import parse_qs, urlsplit
from html import unescape
import re
from contextlib import closing

from test_workspace import w, ui, module
import test_workspace as fixture

compiler=module('workspace_sources')


class SourceParityTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        (self.root/'inputs').mkdir()
        self.policy={'schema_version':1,'access_mode':'loopback_read_only','profile':w.PROFILE,'project_id':'FIXTURE','authority_ref':'owner-fixture','roles':{'owner':['read']},'principals':{},'sources':[{'path':'inputs','kind':'data','roles':['owner']},{'path':'docs','kind':'documents','roles':['owner']}],'registry':'registry.json','accounts':None}
        (self.root/'docs').mkdir();(self.root/'policy.json').write_bytes(w.encoded(self.policy))
        fields={'id':'id','title':'title','purpose':'purpose','acceptance':'acceptance','owner':None,'declared_state':'status'}
        self.recipe={'schema_version':1,'inputs':[{'path':'inputs/records.json','format':'json_records','selector':'items','prefix':'TASK-','type':'task','fields':fields,'row_prefixes':[]}],'relations':[]}
        self.records={'items':[{'id':'native:1','title':'One','purpose':'Observe','acceptance':'visible outcome','status':'accepted'}]}
        self.save()
    def save(self):
        (self.root/'inputs/recipe.json').write_bytes(w.encoded(self.recipe));(self.root/'inputs/records.json').write_bytes(w.encoded(self.records))
    def compile(self):return compiler.compile_registry(self.root,'policy.json','inputs/recipe.json')
    def test_explicit_golden_values_and_declared_state_never_passes(self):
        value=self.compile();key='TASK-'+hashlib.sha256(b'native:1').hexdigest()[:24]
        self.assertEqual(value['objects'],[{'id':key,'type':'task','title':'One','purpose':'Observe','sources':['inputs/recipe.json','inputs/records.json'],'depends_on':[],'task_id':None,'acceptance_class':'mixed'}])
        self.assertEqual(value['contracts'][key]['declared_state'],'accepted')
        (self.root/'registry.json').write_bytes(w.encoded(value));ws=w.Workspace(self.root);ws.initialize('policy.json');ws.collect('first')
        self.assertEqual(ws.read_only_view()['states'][key]['workflow'],'needs_decision')
        self.assertEqual(ws.read_only_view()['states'][key]['verification'],'unverified')
        self.assertEqual(ws.collect('first')['outcome'],'unchanged')
    def test_table_and_json_representations_produce_same_business_values(self):
        first=self.compile();self.policy['sources'][1]['roles']=['owner']
        (self.root/'docs/work.md').write_text('| ID | Title | Purpose | Acceptance | Status |\n|---|---|---|---|---|\n| native:1 | One | Observe | visible outcome | accepted |\n')
        spec=self.recipe['inputs'][0];spec.update(path='docs/work.md',format='markdown_table',selector='',row_prefixes=['native:'])
        spec['fields']={'id':'0','title':'1','purpose':'2','acceptance':'3','owner':None,'declared_state':'4'};self.save();second=self.compile()
        fields=['id','type','title','purpose','depends_on','task_id','acceptance_class']
        self.assertEqual({k:first['objects'][0][k] for k in fields},{k:second['objects'][0][k] for k in fields})
        self.assertNotEqual(first['objects'][0]['sources'],second['objects'][0]['sources'])
    def test_duplicate_missing_unapproved_sources_rejected(self):
        self.records['items']*=2;self.save()
        with self.assertRaisesRegex(ValueError,'Duplicate'):self.compile()
        self.records['items']=self.records['items'][:1];del self.records['items'][0]['acceptance'];self.save()
        with self.assertRaisesRegex(ValueError,'Mapped field'):self.compile()
        self.recipe['inputs'][0]['path']='.local/private.json';self.save()
        with self.assertRaisesRegex(ValueError,'Unapproved'):self.compile()
    def test_reorder_stable_identity_and_recipe_change_invalidates_sources(self):
        self.records['items'].append(dict(self.records['items'][0],id='native:2',title='Two'));self.save();before=self.compile()
        self.records['items'].reverse();self.save();after=self.compile()
        self.assertEqual(before['objects'],after['objects'])
        self.assertNotEqual(before['contracts'],after['contracts']) # source revision is byte identity
    def test_json_native_identity_is_not_parsed_as_a_display_label(self):
        self.records['items']=[dict(self.records['items'][0],id='ID · one'),dict(self.records['items'][0],id='ID · two')];self.save()
        self.assertEqual(len(self.compile()['objects']),2)
        self.recipe['inputs'][0]['selector']=1;self.save()
        with self.assertRaisesRegex(ValueError,'selector'):self.compile()
    def test_compiler_cli_replay_preserves_mtime_and_conflict(self):
        command=[sys.executable,'-B',str(Path(compiler.__file__)),'--root',str(self.root),'--policy','policy.json','--recipe','inputs/recipe.json','--out','registry.json']
        first=subprocess.run(command,capture_output=True);self.assertEqual(first.returncode,0,first.stdout)
        before=(self.root/'registry.json').stat().st_mtime_ns
        again=subprocess.run(command,capture_output=True);self.assertEqual(again.returncode,0,again.stdout);self.assertEqual(before,(self.root/'registry.json').stat().st_mtime_ns)
        self.records['items'][0]['title']='Changed';self.save();failed=subprocess.run(command,capture_output=True)
        self.assertEqual(failed.returncode,2);self.assertEqual(before,(self.root/'registry.json').stat().st_mtime_ns)


class RelationParityTests(unittest.TestCase):
    def setUp(self):
        self.case=fixture.WorkspaceTests('test_document_hierarchy_and_search_are_derived');self.case.setUp();self.addCleanup(self.case.doCleanups)
        self.root=self.case.root
    def save(self,relations,contracts=None):
        (self.root/'registry.json').write_bytes(w.encoded({'schema_version':2,'objects':self.case.objects,'relations':relations,'contracts':contracts or {}}))
    def edge(self,kind='affects',source='TASK-1',target='SECOND',evidence=None):
        return {'id':'REL-'+kind,'from':source,'to':target,'type':kind,'basis':'inferred_by_static_analysis','sources':evidence or ['docs/topic/sub/req.md']}
    def second(self):
        self.case.objects.append(dict(self.case.obj,id='SECOND',title='Second',task_id=None))
    def test_bidirectional_relations_and_original_source_links(self):
        self.second();self.save([self.edge()]);self.case.ws.collect('graph')
        view=self.case.ws.view(self.case.dev);self.assertEqual(view['relations'],[self.edge()])
        a=ui.render(view,tab='lineage',focus='TASK-1');b=ui.render(view,tab='lineage',focus='SECOND')
        self.assertIn('나가는 · affects',a);self.assertIn('들어오는 · affects',b);self.assertIn('/source?id=SRC-',a)
        self.assertIn('TASK-1',ui.render(view,tab='lineage'))
    def test_filter_focus_page_survive_tab_switch(self):
        view=self.case.ws.view(self.case.dev,'Build','task','needs_decision');body=ui.render(view,focus='TASK-1',query='Build')
        links=[parse_qs(urlsplit(unescape(h)).query) for h in re.findall('href="([^"]+)"',body)]
        target=next(v for v in links if v.get('tab')==['lineage'])
        self.assertEqual(target,{'tab':['lineage'],'query':['Build'],'kind':['task'],'state':['needs_decision'],'page':['0'],'focus':['TASK-1']})
        self.assertIn('id="object-detail"',ui.render(view,tab='lineage',focus='TASK-1',query='Build'))
    def test_relation_added_to_legacy_registry_invalidates_acceptance_before_collect(self):
        self.case.accept();self.second();self.save([self.edge()])
        state=self.case.ws.view(self.case.owner)['states']['TASK-1']
        self.assertEqual((state['workflow'],state['verification']),('needs_decision','stale'))
    def test_contract_revision_invalidates_approval(self):
        self.case.accept();contract={'native_id':'original','owner':'owner intent','acceptance':['new outcome'],'source_revision':'revision-2','declared_state':'complete'}
        self.save([],{ 'TASK-1':contract });self.case.ws.collect('new-contract')
        self.assertEqual(self.case.ws.view(self.case.owner)['states']['TASK-1']['workflow'],'needs_decision')
    def test_conflict_blocks_action_but_does_not_leak_private_endpoint(self):
        self.save([self.edge('conflicts_with',target='SECRET',evidence=['private/owner.md'])]);self.case.ws.collect('conflict')
        self.case.action(self.case.owner,'authorize');view=self.case.ws.view(self.case.dev)
        self.assertEqual(view['relations'],[]);self.assertNotIn('SECRET',w.encoded(view).decode());self.assertTrue(view['states']['TASK-1']['dependency_blocked'])
        with self.assertRaises(ValueError):self.case.action(self.case.dev,'start')
    def test_supersession_needs_new_decision_acceptance_and_blocks_dependents(self):
        self.second()
        for obj in self.case.objects:
            if obj['id']!='SECRET':obj.update(type='decision',task_id=None,acceptance_class='human_verifiable')
        self.case.objects.append(dict(self.case.obj,id='DEPENDENT',depends_on=['TASK-1']))
        self.save([self.edge('supersedes',source='SECOND',target='TASK-1')]);self.case.ws.collect('succession')
        self.assertEqual(self.case.ws.view(self.case.owner)['states']['TASK-1']['decision_status'],'current')
        for token,action in [(self.case.dev,'propose'),(self.case.owner,'authorize'),(self.case.dev,'start'),(self.case.dev,'submit'),(self.case.owner,'accept')]:self.case.action(token,action,'second-'+action,subject='SECOND')
        view=self.case.ws.view(self.case.owner)
        self.assertEqual(view['states']['TASK-1']['decision_status'],'superseded');self.assertTrue(view['states']['DEPENDENT']['dependency_blocked'])
        with self.assertRaises(ValueError):self.case.action(self.case.owner,'start',subject='TASK-1')
    def test_dangling_cycle_duplicate_and_provenance_validation(self):
        self.second()
        for bad in [[self.edge(target='ABSENT')],[self.edge(),self.edge()], [dict(self.edge(),basis='certain')], [dict(self.edge(),basis=[])], [dict(self.edge(),to=[])]]:
            self.save(bad)
            with self.assertRaises(ValueError):self.case.ws.collect('bad')
        for obj in self.case.objects:obj['type']='decision'
        self.save([self.edge('supersedes'),dict(self.edge('supersedes',source='SECOND',target='TASK-1'),id='REL-reverse')])
        with self.assertRaisesRegex(ValueError,'Cyclic'):self.case.ws.collect('cycle')
    def test_audit_history_survives_new_collection(self):
        self.second();self.save([self.edge()]);self.case.ws.collect('graph');before=self.case.ws.view(self.case.dev)['history']['TASK-1']
        self.case.objects[0]['purpose']='New intent';self.save([self.edge()]);self.case.ws.collect('changed')
        history=self.case.ws.view(self.case.dev)['history']['TASK-1'];self.assertEqual(history[:-1],before);self.assertNotEqual(history[-1]['intent_sha256'],history[-2]['intent_sha256'])
    def test_optimized_relation_projection_is_identical_for_pass_and_stale(self):
        self.second();self.case.objects[-1]['task_id']='TASK-1';self.save([self.edge()]);self.case.ws.collect('graph');self.case.core.run('TASK-1','pass')
        for changed in [False,True]:
            if changed:(self.root/'code/check.py').write_text('assert False\n')
            with closing(self.case.ws.connect()) as db:
                plain=self.case.ws._project(db,'developer',cache_core=False)
                optimized=self.case.ws._project(db,'developer',cache_core=True)
                self.assertEqual(w.encoded(plain),w.encoded(optimized))


if __name__=='__main__':unittest.main()

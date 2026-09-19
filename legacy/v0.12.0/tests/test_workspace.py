import copy
from contextlib import closing
import importlib.util
import json
from pathlib import Path
import sqlite3
import shutil
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch
import urllib.request
import urllib.error
import urllib.parse

ROOT=Path(__file__).resolve().parents[1]
def module(name):
    spec=importlib.util.spec_from_file_location(name,ROOT/'seed'/(name+'.py'));m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
w=module('workspace');ui=module('workspace_view');http=module('workspace_server');d=module('delivery')


class WorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        for folder in ['docs/topic/sub','code','private']:(self.root/folder).mkdir(parents=True)
        (self.root/'docs/topic/sub/req.md').write_text('# Expected result\nIntent, not accepted\n')
        (self.root/'code/check.py').write_text("assert 2+2==4\n")
        (self.root/'private/owner.md').write_text('# HIDDEN-OWNER-DOCUMENT\n')
        self.config={'schema_version':1,'access_mode':'authenticated','profile':w.PROFILE,'project_id':'TEST','authority_ref':'fixture-owner-interview','roles':{'owner':['read','authorize','accept','block','defer','resume','deliver','propose','start','submit'],'developer':['read','propose','start','submit']},'principals':{'alice':'owner','bob':'developer','charlie':'owner'},'sources':[{'path':'docs','kind':'documents','roles':['owner','developer']},{'path':'code','kind':'code','roles':['owner','developer']},{'path':'private','kind':'documents','roles':['owner']}],'registry':'registry.json','accounts':'.local/accounts.sqlite3'}
        self.obj={'id':'TASK-1','type':'task','title':'Build item','purpose':'Observe actual test result','sources':['docs/topic/sub/req.md','code/check.py'],'depends_on':[],'task_id':'TASK-1','acceptance_class':'mixed'}
        self.objects=[self.obj,dict(self.obj,id='SECRET',title='HIDDEN-OWNER-DOCUMENT',sources=['private/owner.md'],task_id=None)]
        self.save();self.ws=w.Workspace(self.root);self.ws.initialize('workspace-policy.json');self.ws.collect('collect-1')
        self.accounts=w.component('wiki_access').Accounts(self.root/'.local/accounts.sqlite3',self.config['roles'],w.sha(w.encoded(self.config)))
        self.accounts.provision('alice','owner','owner-password-long-enough');self.accounts.add_account('bob','developer','developer-password-long-enough')
        self.owner=self.accounts.login('alice','owner-password-long-enough');self.dev=self.accounts.login('bob','developer-password-long-enough')
        h=w.component('harness');self.core=h.Core(self.root)
        policy={'schema_version':1,'project_id':'TEST','authority_ref':'fixture','commands':{'check':{'argv':[sys.executable,'-B','code/check.py'],'timeout_seconds':3}},'max_output_bytes':4096}
        self.core_policy=self.root/'core-policy.json';self.core_policy.write_bytes(h.encoded(policy));self.core.initialize(self.core_policy)
        self.task={'schema_version':1,'id':'TASK-1','title':'fixture','purpose':'test','acceptance_class':'mixed','criteria':['actual fixture passes'],'target_paths':['docs/topic/sub/req.md','code/check.py'],'required_tests':['check']}
        self.core.define_task(self.task,'define-1')
    def save(self):
        (self.root/'workspace-policy.json').write_bytes(w.encoded(self.config));(self.root/'registry.json').write_bytes(w.encoded({'schema_version':1,'objects':self.objects}))
    def action(self,token,action,key=None,subject='TASK-1'):
        state=self.ws.view(token)['states'][subject]
        return self.ws.act(token,{'subject':subject,'action':action,'key':key or action,'expected_revision':state['revision'],'snapshot':state['snapshot'],'reason':'Observed fixture decision'})
    def accept(self):
        self.action(self.dev,'propose');self.action(self.owner,'authorize');self.action(self.dev,'start');self.core.run('TASK-1','run-1');self.action(self.dev,'submit');self.action(self.owner,'accept')
    def test_workflow_test_and_human_acceptance_are_independent(self):
        self.assertEqual(self.ws.view(self.owner)['states']['TASK-1']['workflow'],'needs_decision')
        self.core.run('TASK-1','first');self.assertEqual(self.ws.view(self.owner)['states']['TASK-1']['workflow'],'needs_decision')
        self.accept();s=self.ws.view(self.owner)['states']['TASK-1'];self.assertEqual((s['workflow'],s['verification'],s['delivery']),('accepted','passed','unobserved'))
    def test_source_change_invalidates_approval_and_test_even_after_collect(self):
        self.accept();(self.root/'docs/topic/sub/req.md').write_text('# Changed intent')
        s=self.ws.view(self.owner)['states']['TASK-1'];self.assertEqual((s['workflow'],s['verification']),('needs_decision','stale'))
        with self.assertRaises(ValueError):self.action(self.owner,'authorize','after-change')
        self.ws.collect('collect-2');self.assertEqual(self.ws.view(self.owner)['states']['TASK-1']['workflow'],'needs_decision')
    def test_acceptance_contract_change_cannot_revive_prior_human_approval(self):
        self.accept();self.task['criteria']=['Different owner acceptance requirement'];self.core.define_task(self.task,'new-contract',1);self.core.run('TASK-1','new-contract-run')
        self.assertEqual(self.ws.view(self.owner)['states']['TASK-1']['workflow'],'needs_decision')
    def test_human_verifiable_decision_does_not_invent_machine_pass(self):
        self.objects[0].update(type='decision',task_id=None,acceptance_class='human_verifiable');self.save();self.ws.collect('human-intent')
        self.action(self.dev,'propose');self.action(self.owner,'authorize');self.action(self.dev,'start');self.action(self.dev,'submit');self.action(self.owner,'accept')
        s=self.ws.view(self.owner)['states']['TASK-1'];self.assertEqual((s['workflow'],s['acceptance'],s['verification'],s['delivery']),('accepted','human_recorded','unverified','unobserved'))
    def test_same_title_preserves_identity_and_hidden_sources_never_leak(self):
        view=self.ws.view(self.dev);self.assertNotIn('SECRET',view['objects']);self.assertNotIn('private',w.encoded(view).decode());self.assertNotIn('HIDDEN',ui.render(view))
        with self.assertRaises(ValueError):ui.render(view,focus='SECRET')
        with self.assertRaises(ValueError):self.ws.act(self.dev,{'subject':'SECRET','action':'propose','key':'hidden','expected_revision':0,'snapshot':'0'*64,'reason':'hidden target'})
    def test_declared_status_cannot_certify_work(self):
        self.objects[0]['status']='accepted';self.save()
        with self.assertRaises(ValueError):self.ws.collect('malformed')
        self.assertEqual(self.ws.view(self.owner)['states']['TASK-1']['workflow'],'needs_decision')
    def test_wrong_principal_permission_revocation_and_policy_drift(self):
        with self.assertRaises(ValueError):self.action(self.dev,'authorize')
        with self.assertRaises(ValueError):self.ws.view('invented token')
        self.accounts.logout(self.dev)
        with self.assertRaises(ValueError):self.ws.view(self.dev)
        self.config['roles']['developer'].append('accept');self.save()
        with self.assertRaises(ValueError):self.ws.view(self.owner)
    def test_independent_approval_even_when_one_role_has_all_capabilities(self):
        self.accounts.add_account('charlie','owner','reviewer-password-long-enough');reviewer=self.accounts.login('charlie','reviewer-password-long-enough')
        self.action(self.owner,'propose')
        with self.assertRaises(ValueError):self.action(self.owner,'authorize','self-authorize')
        self.action(reviewer,'authorize');self.action(self.owner,'start');self.core.run('TASK-1','actual-run');self.action(self.owner,'submit')
        with self.assertRaises(ValueError):self.action(self.owner,'accept','self-accept')
        self.action(reviewer,'accept');self.assertEqual(self.ws.view(self.owner)['states']['TASK-1']['workflow'],'accepted')
    def test_replay_conflict_and_revision_race_preserve_events(self):
        state=self.ws.view(self.dev)['states']['TASK-1'];request={'subject':'TASK-1','action':'propose','key':'once','expected_revision':0,'snapshot':state['snapshot'],'reason':'proposal'}
        first=self.ws.act(self.dev,request);self.assertEqual(self.ws.act(self.dev,request)['outcome'],'unchanged')
        for change in [{'reason':'changed'},{'key':'new-key'}]:
            with self.assertRaises(ValueError):self.ws.act(self.dev,dict(request,**change))
        self.assertEqual(self.ws.collect('collect-1')['outcome'],'unchanged')
        with closing(self.ws.connect()) as db:self.assertEqual(len(self.ws.events(db)),2)
    def test_missing_dependency_cycle_and_changed_registry(self):
        self.objects[0]['depends_on']=['SECRET'];self.save();self.ws.collect('dependencies')
        self.action(self.owner,'authorize')
        with self.assertRaises(ValueError):self.action(self.dev,'start')
        self.objects[1]['depends_on']=['TASK-1'];self.save()
        with self.assertRaises(ValueError):self.ws.collect('cycle')
    def test_submit_without_run_and_unbound_run_rejected(self):
        self.action(self.owner,'authorize');self.action(self.dev,'start')
        with self.assertRaises(ValueError):self.action(self.dev,'submit')
        self.task['target_paths']=['code/check.py'];self.core.define_task(self.task,'changed',1);self.core.run('TASK-1','unbound')
        self.assertEqual(self.ws.view(self.dev)['states']['TASK-1']['verification'],'stale')
        with self.assertRaises(ValueError):self.action(self.dev,'submit')
    def test_document_hierarchy_and_search_are_derived(self):
        view=self.ws.view(self.owner,query='Build');self.assertEqual(view['matches'],['TASK-1'])
        doc=next(d for d in view['documents'].values() if d['path']=='docs/topic/sub/req.md');depth=0;parent=doc['parent']
        while parent:depth+=1;parent=view['collections'][parent]['parent']
        self.assertEqual(depth,3);self.assertIn('Expected result',ui.render(view,tab='documents'))
        self.assertNotIn('data-object=',ui.render(self.ws.view(self.owner,query='no-match'),focus='TASK-1'))
    def test_projection_empty_duplicate_and_incorrect_states_are_rejected(self):
        view=self.ws.view(self.dev);body=ui.render(view);self.assertEqual(ui.audit(body,view)['state'],'structure_passed')
        for broken in [body.replace('data-object="TASK-1"','data-absent="TASK-1"'),body.replace('data-workflow="needs_decision"','data-workflow="accepted"'),body.replace('data-verification="unverified"','data-verification="passed"'),body+body]:
            with self.assertRaises(ValueError):ui.audit(broken,view)
    def test_missing_source_stale_and_reads_do_not_write(self):
        before={p:p.stat().st_mtime_ns for p in self.root.rglob('*') if p.is_file()};self.ws.view(self.owner)
        self.assertEqual(before,{p:p.stat().st_mtime_ns for p in self.root.rglob('*') if p.is_file()})
        (self.root/'code/check.py').unlink();self.assertEqual(self.ws.view(self.owner)['states']['TASK-1']['verification'],'stale')
    def test_http_anonymous_host_origin_and_role_boundaries(self):
        httpd=http.server(self.root);thread=threading.Thread(target=httpd.serve_forever,daemon=True);thread.start();self.addCleanup(httpd.server_close);self.addCleanup(httpd.shutdown)
        base='http://127.0.0.1:'+str(httpd.server_port)
        def get(path,token=None,host=None):
            headers={'Cookie':'workspace_session='+token} if token else {}
            if host:headers['Host']=host
            return urllib.request.urlopen(urllib.request.Request(base+path,headers=headers))
        for path in ['/','/api/view','/source?id=SECRET','/unknown']:
            with self.assertRaises(urllib.error.HTTPError) as e:get(path)
            self.assertEqual(e.exception.code,403)
        with get('/api/view',self.dev) as response:self.assertNotIn(b'HIDDEN',response.read())
        with self.assertRaises(urllib.error.HTTPError):get('/',self.owner,'evil.example')
        with get('/',self.owner) as response:self.assertIn('작업 개요',response.read().decode())
        request=urllib.request.Request(base+'/api/action',data=b'{}',headers={'Origin':'https://evil.example','Cookie':'workspace_session='+self.owner,'Content-Type':'application/json','X-Workspace-Action':'1'})
        with self.assertRaises(urllib.error.HTTPError):urllib.request.urlopen(request)
        s=self.ws.view(self.owner)['states']['TASK-1'];fields={'subject':'TASK-1','action':'authorize','key':'browser-decision','expected_revision':s['revision'],'snapshot':s['snapshot'],'reason':'Owner fixture scope'}
        request=urllib.request.Request(base+'/action-form',data=urllib.parse.urlencode(fields).encode(),headers={'Origin':base,'Cookie':'workspace_session='+self.owner,'Content-Type':'application/x-www-form-urlencoded'})
        with urllib.request.urlopen(request) as response:self.assertEqual(response.status,200)
        self.assertEqual(self.ws.view(self.dev)['states']['TASK-1']['workflow'],'ready')
    def test_optimization_preserves_all_projection_fields_and_never_reuses_between_views(self):
        self.objects=[dict(self.obj,id='ITEM-'+str(i)) for i in range(24)];self.save();self.ws.collect('many');self.core.run('TASK-1','shared-run')
        original=w.component;h=original('harness');calls=[];status=h.Core.status
        def observed(core,key):calls.append(key);return status(core,key)
        with patch.object(h.Core,'status',observed),patch.object(w,'component',lambda name:h if name=='harness' else original(name)),closing(self.ws.connect()) as db:
            plain=self.ws._project(db,'owner',cache_core=False);self.assertEqual(len(calls),24);calls.clear()
            cached=self.ws._project(db,'owner');self.assertEqual(len(calls),1);self.assertEqual(plain,cached)
            (self.root/'code/check.py').write_text('assert False\n');self.assertEqual(self.ws._project(db,'owner')[2]['ITEM-0']['verification'],'stale')
        view=self.ws.view(self.owner)
        for page in range(4):self.assertEqual(ui.audit(ui.render(view,page=page),view,page=page)['members'],6)
    def test_backup_restores_audit_without_authority_or_live_overwrite(self):
        self.accept();result=self.ws.backup('.local/audit.json');self.assertEqual(result['outcome'],'backup_created')
        self.assertEqual(self.ws.backup('.local/audit.json')['outcome'],'unchanged')
        restored=w.Workspace(self.root/'inspection');self.assertEqual(restored.restore(self.root/'.local/audit.json')['authority'],'inspection_only')
        self.assertFalse(restored.path.exists())
        with self.assertRaises(ValueError):restored.view(self.owner)
        with self.assertRaises(ValueError):self.ws.restore(self.root/'.local/audit.json')
        raw=json.loads((self.root/'.local/audit.json').read_bytes());raw['events'][0][2]='f'*64;(self.root/'.local/forged.json').write_bytes(w.encoded(raw))
        with self.assertRaises(ValueError):w.Workspace(self.root/'bad-inspection').restore(self.root/'.local/forged.json')
    def test_explicit_offline_read_mode_has_no_login_or_action_authority(self):
        root=self.root/'offline';root.mkdir()
        for folder in ['docs','code','private']:shutil.copytree(self.root/folder,root/folder)
        config=copy.deepcopy(self.config);config.update(access_mode='loopback_read_only',roles={'owner':['read']},principals={},accounts=None)
        for source in config['sources']:source['roles']=['owner']
        (root/'policy.json').write_bytes(w.encoded(config));(root/'registry.json').write_bytes(w.encoded({'schema_version':1,'objects':self.objects}))
        workspace=w.Workspace(root);workspace.initialize('policy.json');workspace.collect('initial');view=workspace.read_only_view()
        self.assertEqual(view['capabilities'],[]);self.assertNotIn('/action-form',ui.render(view,focus='TASK-1'))
        with self.assertRaises(ValueError):workspace.view(self.owner)
        with self.assertRaises(ValueError):workspace.act(self.owner,{'subject':'TASK-1','action':'authorize','key':'denied','expected_revision':0,'snapshot':view['states']['TASK-1']['snapshot'],'reason':'No identity'})
        with self.assertRaises(ValueError):self.ws.read_only_view()
        httpd=http.server(root);threading.Thread(target=httpd.serve_forever,daemon=True).start();self.addCleanup(httpd.server_close);self.addCleanup(httpd.shutdown)
        with urllib.request.urlopen('http://127.0.0.1:'+str(httpd.server_port)+'/') as response:self.assertEqual(response.status,200)
        config['roles']['owner'].append('accept')
        with self.assertRaises(ValueError):w.policy(config)


class DeliveryTests(unittest.TestCase):
    setUp=WorkspaceTests.setUp
    save=WorkspaceTests.save
    action=WorkspaceTests.action
    accept=WorkspaceTests.accept
    def prepare(self,mode='ok'):
        (self.root/'artifact.txt').write_text('immutable fixture artifact')
        (self.root/'mode').write_text(mode)
        (self.root/'adapter.py').write_text('''import json,sys
from pathlib import Path
r=json.load(sys.stdin);p=r['phase'];mode=Path('mode').read_text();active=json.loads(Path('active.json').read_text()) if Path('active.json').exists() else None
with Path('calls').open('a') as f:f.write(p+'\\n')
if mode=='oversize':print('x'*1000000);raise SystemExit()
if p=='activate':
 active=r['candidate'];Path('active.json').write_text(json.dumps(active))
 if mode=='crash':raise SystemExit(3)
if p=='rollback':active=r['previous'];Path('active.json').write_text(json.dumps(active))
print(json.dumps({'ok':not(p=='health' and mode=='health-fail' and active is not None),'active':active}))
''')
        self.dp={'schema_version':1,'authority_ref':'local-fixture-only','commands':{p:[sys.executable,'-B','adapter.py'] for p in ['inspect','activate','health','rollback']},'bindings':{'adapter.py':w.sha((self.root/'adapter.py').read_bytes())},'executables':{sys.executable:w.sha(Path(sys.executable).read_bytes())},'timeout_seconds':2,'artifact_paths':['artifact.txt'],'canary':{'target':'fixture-only','checks':2,'interval_seconds':1}}
        (self.root/'delivery-policy.json').write_bytes(w.encoded(self.dp));self.delivery=d.Delivery(self.root);self.delivery.initialize('delivery-policy.json')
        self.task['target_paths']+=['artifact.txt','adapter.py','delivery-policy.json'];self.core.define_task(self.task,'include-delivery',1);self.accept()
    def test_release_replay_and_projection(self):
        self.prepare();result=self.delivery.release(self.owner,'TASK-1','delivery-1',None);self.assertEqual(result['outcome'],'released')
        self.assertEqual(self.delivery.release(self.owner,'TASK-1','delivery-1',None),result);self.assertEqual((self.root/'calls').read_text().splitlines(),['inspect','activate','health','health']);self.assertGreaterEqual(result['canary']['elapsed_seconds'],1)
        self.assertEqual(self.ws.view(self.owner)['states']['TASK-1']['delivery'],'released')
        (self.root/'artifact.txt').write_text('changed');self.assertEqual(self.ws.view(self.owner)['states']['TASK-1']['delivery'],'stale')
    def test_unhealthy_candidate_restores_previous_with_health(self):
        self.prepare('health-fail');result=self.delivery.release(self.owner,'TASK-1','delivery-1',None)
        self.assertEqual(result['outcome'],'rolled_back');self.assertEqual([r['phase'] for r in result['receipts']],['inspect','activate','health','rollback','health'])
        self.assertIsNone(json.loads((self.root/'active.json').read_text()))
    def test_unknown_activation_blocks_retry_and_reconciles_without_writing(self):
        self.prepare('crash')
        with self.assertRaises(ValueError):self.delivery.release(self.owner,'TASK-1','delivery-1',None)
        for key in ['delivery-1','delivery-2']:
            with self.assertRaises(ValueError):self.delivery.release(self.owner,'TASK-1',key,None)
        self.assertEqual((self.root/'calls').read_text().splitlines(),['inspect','activate'])
        self.assertEqual(self.ws.view(self.owner)['states']['TASK-1']['delivery'],'effect_unknown')
        (self.root/'mode').write_text('ok');result=self.delivery.reconcile(self.owner,'delivery-1');self.assertEqual(result['outcome'],'reconciled_candidate')
        self.assertEqual((self.root/'calls').read_text().splitlines(),['inspect','activate','inspect','health'])
    def test_wrong_active_aborts_before_activation(self):
        self.prepare();result=self.delivery.release(self.owner,'TASK-1','delivery-1','a'*64)
        self.assertEqual(result['outcome'],'aborted');self.assertEqual((self.root/'calls').read_text().splitlines(),['inspect'])
    def test_capability_binding_and_output_limit(self):
        self.prepare('oversize')
        with self.assertRaises(ValueError):self.delivery.release(self.dev,'TASK-1','denied',None)
        self.assertFalse((self.root/'calls').exists())
        with self.assertRaises(ValueError):self.delivery.release(self.owner,'TASK-1','delivery-1',None)
        self.assertEqual(self.ws.view(self.owner)['states']['TASK-1']['delivery'],'effect_unknown')
    def test_unbound_policy_artifact_and_tampered_history_fail_closed(self):
        self.prepare();self.task['target_paths'].remove('delivery-policy.json');self.core.define_task(self.task,'unbound',2);self.core.run('TASK-1','run-2')
        with self.assertRaises(ValueError):self.delivery.release(self.owner,'TASK-1','delivery-1',None)
        self.assertFalse((self.root/'calls').exists())
        with closing(self.delivery.connect()) as db,db:
            db.execute('INSERT INTO events VALUES(1,?,?,?,?,?)',('forged','started',b'{}',w.ZERO,w.ZERO))
        self.assertEqual(self.ws.view(self.owner)['states']['TASK-1']['delivery'],'unknown')


class StructuralRegression(unittest.TestCase):
    def test_empty_markers_no_longer_pass_static_quality(self):
        draft=w.component('wiki_draft');quality=w.component('wiki_quality');bundle=draft.bundle(json.loads((ROOT/'seed/docs/wiki/draft-input.json').read_bytes()))
        files={n:v for n,v in bundle.items() if n.endswith('.html')};contract=json.loads(bundle['quality-contract.json']);removed=0
        for n,raw in list(files.items()):
            s=raw.decode();a=s.find('<section class="state-map"');b=s.find('<details><summary>목적 · 행동 · 문서와 생성 근거 펼치기</summary>',a)
            if a>=0 and b>a:s=s[:a]+'<section data-graph-profile="state-object-view-1"></section>'+s[b:];files[n]=s.encode();removed+=1
        result=quality.audit(files,contract);self.assertEqual(removed,9);self.assertEqual(result['state'],'blocked');self.assertIn('state_member_inventory_differs',[f['code'] for f in result['failures']])


if __name__=='__main__':unittest.main()

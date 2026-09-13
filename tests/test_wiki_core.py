import copy
import importlib.util
from pathlib import Path
import tempfile
import unittest
import sqlite3

ROOT=Path(__file__).resolve().parents[1]
def load(name):
    spec=importlib.util.spec_from_file_location(name,ROOT/'seed'/f'{name}.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
w=load('wiki_core');a=load('wiki_access')

class WikiCoreTests(unittest.TestCase):
    def setUp(self):
        self.c={'schema_version':1,'profile':w.PROFILE,'roles':{'lead':'Owner-selected lead','auditor':'Owner-selected auditor'},'access':{'root_read':['lead','auditor'],'overrides':{'detail':['lead']}},'root':'home','nodes':[],
            'interview':{'status':'confirmed','decision_ref':'owner.json','policy_digest':''},
            'adapter':{'kind':'authenticated_read_only','source_paths':['server.py'],'test_paths':['negative.py'],'required_tests':['access']}}
        for ident,parent,roles in [('home',None,['lead','auditor']),('topic','home',['lead','auditor']),('detail','topic',['lead'])]:
            self.c['nodes'].append({'id':ident,'parent':parent,'page':ident+'.html','title':ident,'grants':{'read':roles,'edit':[],'approve':[],'execute':[]}})
        self.c['interview']['policy_digest']=w.policy_digest(self.c)

    def test_hierarchy_and_role_navigation_are_derived(self):
        self.assertEqual(len(w.validate(self.c)),3)
        self.assertIn('detail.html',w.navigation(self.c,'topic','lead'))
        self.assertNotIn('detail',w.navigation(self.c,'topic','auditor'))
        self.assertIn('home.html',w.navigation(self.c,'detail','lead'))
        self.assertFalse(w.allowed(self.c,'detail','auditor'))
        self.assertFalse(w.allowed(self.c,'detail','lead','approve'))

    def test_interview_pending_and_changed_permissions_fail_closed(self):
        for mutate in [lambda c:c['interview'].update(status='pending'),lambda c:c['roles'].update(guest='Guest'),lambda c:c['access']['overrides'].update(topic=['lead'])]:
            value=copy.deepcopy(self.c);mutate(value)
            with self.assertRaises(ValueError):w.validate(value)

    def test_explicit_local_no_login_mode_requires_one_role_and_new_interview(self):
        c=copy.deepcopy(self.c);c['adapter']['kind']='loopback_read_only'
        c['interview']['policy_digest']=w.policy_digest(c)
        with self.assertRaises(ValueError):w.validate(c)
        c['roles']={'local_owner':'Local workspace'};c['access']={'root_read':['local_owner'],'overrides':{}}
        for node in c['nodes']:node['grants']['read']=['local_owner']
        with self.assertRaises(ValueError):w.validate(c)
        c['interview']['policy_digest']=w.policy_digest(c)
        self.assertEqual(len(w.validate(c)),3)
        c['interview']['status']='pending'
        with self.assertRaises(ValueError):w.validate(c)

    def test_no_cycles_or_flat_hierarchy_or_broader_child_access(self):
        for mutate in [lambda c:c['nodes'][1].update(parent='detail'),lambda c:c['nodes'][2].update(parent='home'),lambda c:c['nodes'][2]['grants']['read'].append('auditor'),lambda c:c['nodes'][0]['grants']['edit'].append('lead')]:
            value=copy.deepcopy(self.c);mutate(value)
            with self.assertRaises(ValueError):w.validate(value)

    def test_account_session_expiry_policy_change_logout_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            now=[1000];path=Path(tmp)/'auth.db';account=a.Accounts(path,self.c['roles'],'policy-1',lambda:now[0])
            password='fixture-strong-secret-only'
            account.provision('lead','lead',password)
            with self.assertRaises(FileExistsError):account.provision('lead','lead','different-fixture-secret')
            self.assertIsNone(account.login('lead','wrong'))
            token=account.login('lead',password);self.assertEqual(account.role(token),'lead')
            self.assertIsNone(a.Accounts(path,self.c['roles'],'policy-2',lambda:now[0]).role(token))
            account.logout(token);self.assertIsNone(account.role(token))
            token=account.login('lead',password);now[0]+=28801;self.assertIsNone(account.role(token))
            account.add_account('auditor','auditor',password)
            self.assertEqual(account.role(account.login('auditor',password)),'auditor')
            with self.assertRaises(sqlite3.IntegrityError):account.add_account('auditor','auditor',password)
            self.assertNotIn(password.encode(),path.read_bytes())

    def test_login_throttle_and_unknown_role(self):
        with tempfile.TemporaryDirectory() as tmp:
            now=[1000];account=a.Accounts(Path(tmp)/'auth.db',{'lead'},'policy',lambda:now[0]);password='fixture-strong-secret-only'
            account.provision('lead','lead',password)
            for _ in range(5):self.assertIsNone(account.login('lead','wrong'))
            self.assertIsNone(account.login('lead',password))
            now[0]+=901;self.assertIsNotNone(account.login('lead',password))
            with self.assertRaises(ValueError):account.add_account('admin','unapproved',password)

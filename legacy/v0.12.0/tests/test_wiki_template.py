import copy
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
import re

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'seed'))
import wiki_template as w
sys.path.pop(0)


def fixture(project='Example documentation tool'):
    content=w.scaffold();content.update(template_only=False,project_name=project,purpose='Understand the project and next work',scope='Offline fixture only',unknowns=['Human acceptance pending'])
    for topic in content['topics'].values():topic.update(purpose='Explain this topic',current_scope='Source exists; no execution claim',actions=['Read source and define next work'],source_refs=['fixture-source'],unknowns=['No live evidence'])
    content['tasks']=[dict(id='WORK-1',title='Check user journey',purpose='Find confusing steps',depends_on=[],deliverables=['Reproduction and proposed fix'],acceptance=['Fixture output matches contract','Owner reviews readability'],owner_decision='Human review pending',source_refs=['fixture-source']),dict(id='WORK-2',title='Restricted follow-up',purpose='SECRET PURPOSE',depends_on=['WORK-1'],deliverables=['SECRET OUTPUT'],acceptance=['SECRET CHECK'],owner_decision='SECRET DECISION',source_refs=['SECRET SOURCE'])]
    tree=dict(schema_version=1,profile='wiki-tree-access-1',interview=dict(status='confirmed',decision_ref='fixture-owner.json',policy_digest=''),roles={'lead':'Fixture lead','reviewer':'Fixture reader'},access={'root_read':['lead','reviewer'],'overrides':{'WORK-2':['lead']}},nodes=[],root='index',adapter=dict(kind='authenticated_read_only',source_paths=['fixture_server.py'],test_paths=['fixture_test.py'],required_tests=['fixture-access']))
    for ident,title,parent,roles in [('index','Overview',None,['lead','reviewer']),*[(k,v,'index',['lead','reviewer']) for k,v in w.TOPICS.items()],*[(t['id'],t['title'],'workflows',['lead'] if t['id']=='WORK-2' else ['lead','reviewer']) for t in content['tasks']]]:
        tree['nodes'].append(dict(id=ident,title=title,parent=parent,page=ident+'.html',grants=dict(read=roles,edit=[],approve=[],execute=[])))
    tree['interview']['policy_digest']=w.wiki_core.policy_digest(tree)
    return content,tree


class DefaultWikiTests(unittest.TestCase):
    def test_two_domains_share_layout_without_inheriting_project_content(self):
        for name in ['Warehouse task board','Documentation tool']:
            content,tree=fixture(name);outputs=w.render(content,tree)
            raw=outputs['lead/index.html'].decode()
            self.assertIn(name,raw);self.assertIn('workflows.html',raw)
            self.assertNotIn('Portfolio Research',raw);self.assertNotIn('AAPL',raw)
            self.assertIn('끝났다고 판단할 기준',outputs['lead/WORK-1.html'].decode())

    def test_links_resolve_inside_role_and_hidden_content_does_not_leak(self):
        content,tree=fixture();outputs=w.render(content,tree)
        for name,raw in outputs.items():
            for href in re.findall(r'href="([^"]+)"',raw.decode()):self.assertIn(name.split('/')[0]+'/'+href,outputs)
            if name.startswith('reviewer/'):
                self.assertNotIn(b'SECRET',raw);self.assertNotIn(b'WORK-2',raw);self.assertNotIn(b'Restricted follow-up',raw)

    def test_scaffold_and_owner_pending_and_flat_tree_are_rejected(self):
        content,tree=fixture()
        with self.assertRaises(ValueError):w.render(w.scaffold(),tree)
        tree['interview']['status']='pending'
        with self.assertRaises(ValueError):w.render(content,tree)
        content,tree=fixture();tree['nodes'][-1]['parent']='index'
        with self.assertRaises(ValueError):w.render(content,tree)

    def test_dag_and_acceptance_and_unknowns_required(self):
        for mutation in [lambda c:c['tasks'][0].update(depends_on=['WORK-2']),lambda c:c['tasks'][0].update(acceptance=[]),lambda c:c.update(unknowns=[]),lambda c:c['topics'].pop('quality'),lambda c:c['tasks'][0].update(status='verified')]:
            c,t=fixture();mutation(c)
            with self.assertRaises(ValueError):w.render(c,t)

    def test_injected_prose_is_escaped_without_url_execution(self):
        c,t=fixture();c['tasks'][0]['purpose']='<script>alert(1)</script> [link](javascript:alert(1))'
        raw=w.render(c,t)['lead/WORK-1.html']
        self.assertNotIn(b'<script>',raw);self.assertIn(b'&lt;script&gt;',raw)
        self.assertNotIn(b'href="javascript',raw)

    def test_immutable_output_noop_conflict_and_partial_recovery(self):
        c,t=fixture();outputs=w.render(c,t)
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'render'
            self.assertEqual(w.write_bundle(out,outputs,{'test':'fixture'}),'written')
            before={p:p.stat().st_mtime_ns for p in out.rglob('*') if p.is_file()}
            self.assertEqual(w.write_bundle(out,w.render(c,t),{'test':'fixture'}),'unchanged')
            self.assertEqual(before,{p:p.stat().st_mtime_ns for p in out.rglob('*') if p.is_file()})
            (out/'lead/index.html').write_bytes(b'owner modification')
            with self.assertRaises(ValueError):w.write_bundle(out,outputs,{'test':'fixture'})
            self.assertEqual((out/'lead/index.html').read_bytes(),b'owner modification')

    def test_loopback_requires_explicit_single_scope(self):
        c,t=fixture();t['adapter']['kind']='loopback_read_only';t['interview']['policy_digest']=w.wiki_core.policy_digest(t)
        with self.assertRaises(ValueError):w.render(c,t)
        t['roles']={'workspace':'Owner selected local workspace'};t['access']={'root_read':['workspace'],'overrides':{}}
        for n in t['nodes']:n['grants']['read']=['workspace']
        t['interview']['policy_digest']=w.wiki_core.policy_digest(t)
        self.assertIn('workspace/index.html',w.render(c,t))


if __name__=='__main__':unittest.main()

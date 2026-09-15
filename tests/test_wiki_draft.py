import copy
import importlib.util
import json
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('draft', ROOT/'seed/wiki_draft.py')
w = importlib.util.module_from_spec(spec); spec.loader.exec_module(w)
spec2 = importlib.util.spec_from_file_location('distributor', ROOT/'scripts/seed.py')
distributor = importlib.util.module_from_spec(spec2); spec2.loader.exec_module(distributor)


class DraftTests(unittest.TestCase):
    def data(self): return json.loads((ROOT/'seed/docs/wiki/draft-input.json').read_bytes())

    def test_two_domains_have_six_types_navigation_and_lineage_without_execution(self):
        for name in ['Warehouse review', 'Garden planner']:
            data=self.data();data['project_name']=name
            pages=w.bundle(data)
            self.assertEqual(pages,w.bundle(data))
            manifest=json.loads(pages['manifest.json'])
            self.assertFalse(manifest['bootstrap_ready'])
            self.assertEqual(len(manifest['claims']),18)
            self.assertIn(name.encode(),pages['index.html'])
            for file,raw in pages.items():
                if not file.endswith('.html'):continue
                for link in re.findall(r'href="([^"]+)"',raw.decode()):self.assertIn(link,pages)
                self.assertIn(b'interview_pending',raw)
            for obj in data['objects']:
                page=pages[obj['id']+'.html'].decode()
                for label in ['목적','다음 행동','관계','근거 조회','생성 근거']:self.assertIn(label,page)
            self.assertIn(b'DRAFT-TASK-001.html',pages['DRAFT-REQ-001.html'])
            self.assertEqual(manifest['graph_profile'],'object-node-map-1')
            self.assertIn(b'data-graph-profile="object-node-map-1"',pages['index.html'])
            for obj in data['objects']:
                self.assertIn(('data-focus="'+obj['id']+'"').encode(),pages[obj['id']+'.html'])

    def test_missing_type_dangling_relation_and_authored_status_rejected(self):
        for fault in ['type','relation','status','duplicate']:
            data=self.data()
            if fault=='type':data['objects'].pop()
            elif fault=='relation':data['relations'][0]['to']='ABSENT'
            elif fault=='status':data['objects'][0]['verification']='passed'
            else:data['objects'].append(copy.deepcopy(data['objects'][0]))
            with self.assertRaises(ValueError):w.bundle(data)

    def test_untrusted_prose_escaped_and_no_source_file_is_opened(self):
        data=self.data();data['objects'][0]['title']='<script>bad()</script>'
        data['objects'][0]['source_refs']=['does-not-exist.md']
        raw=w.bundle(data)['DRAFT-REQ-001.html']
        self.assertNotIn(b'<script>',raw);self.assertIn(b'&lt;script&gt;',raw)
        self.assertIn(b'unverified',raw)
        for ref in ['../secret','https://example.test','C:/secret','a\\b']:
            data['objects'][0]['source_refs']=[ref]
            with self.assertRaises(ValueError):w.bundle(data)

    def test_immutable_replay_and_drift_preserve_bytes(self):
        with tempfile.TemporaryDirectory() as folder:
            out=Path(folder)/'draft';files=w.bundle(self.data())
            self.assertEqual(w.write_bundle(out,files),'written')
            before={p.name:(p.read_bytes(),p.stat().st_mtime_ns) for p in out.iterdir()}
            self.assertEqual(w.write_bundle(out,files),'unchanged')
            self.assertEqual(before,{p.name:(p.read_bytes(),p.stat().st_mtime_ns) for p in out.iterdir()})
            (out/'index.html').write_bytes(b'owner edit')
            with self.assertRaises(ValueError):w.write_bundle(out,files)
            self.assertEqual((out/'index.html').read_bytes(),b'owner edit')

    def test_partial_output_is_not_repaired_by_overwriting(self):
        with tempfile.TemporaryDirectory() as folder:
            out=Path(folder);(out/'index.html').write_bytes(b'partial')
            with self.assertRaises(ValueError):w.write_bundle(out,w.bundle(self.data()))
            self.assertEqual(list(out.iterdir()),[out/'index.html'])

    def test_install_generates_draft_without_scaffold_and_preserves_empty_truth(self):
        with tempfile.TemporaryDirectory() as folder:
            target=Path(folder)/'project';_,payload,receipt=distributor.load_seed()
            result=distributor.initialize(target,payload,receipt,False)
            self.assertEqual(result['wiki_draft'],'.local/wiki-draft/index.html')
            self.assertTrue((target/result['wiki_draft']).is_file())
            self.assertEqual(json.loads((target/'docs/harness/objects.json').read_bytes()),[])
            self.assertEqual((target/'docs/harness/events.jsonl').read_bytes(),b'')
            self.assertEqual(distributor.initialize(target,payload,receipt,False)['outcome'],'unchanged')

    def test_normal_python_install_does_not_pollute_distribution_inventory(self):
        _,payload,receipt=distributor.load_seed()
        before={p.relative_to(ROOT/'seed').as_posix() for p in (ROOT/'seed').rglob('*') if p.is_file()}
        with tempfile.TemporaryDirectory() as folder, patch.object(distributor.sys,'dont_write_bytecode',False):
            distributor.initialize(Path(folder)/'project',payload,receipt,False)
            self.assertFalse(distributor.sys.dont_write_bytecode)
        self.assertEqual(before,{p.relative_to(ROOT/'seed').as_posix() for p in (ROOT/'seed').rglob('*') if p.is_file()})
        distributor.load_seed()

    def test_existing_draft_conflict_is_detected_before_installing_seed(self):
        with tempfile.TemporaryDirectory() as folder:
            target=Path(folder)/'project';out=target/'.local/wiki-draft/index.html'
            out.parent.mkdir(parents=True);out.write_bytes(b'owner work')
            _,payload,receipt=distributor.load_seed()
            with self.assertRaises(distributor.SeedError):distributor.initialize(target,payload,receipt,False)
            self.assertFalse((target/'AGENTS.md').exists());self.assertEqual(out.read_bytes(),b'owner work')


if __name__ == '__main__':unittest.main()

import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'seed'))
import source_catalog as catalog


def fixture():
    return {'objects': [
        {'id': 'owner', 'type': 'authority', 'permission': 'deploy'},
        {'id': 'task', 'type': 'work_item', 'title': '한글', 'status': 'verified', 'acceptance': 'independent test'},
        {'id': 'test', 'type': 'document'}],
        'object_types': [{'id': t} for t in ['authority', 'work_item', 'document']],
        'relations': [{'from': 'task', 'to': 'test', 'type': 'verified_by', 'origin': 'fixture'}],
        'interfaces': [{'id': 'verifiable', 'applies_to': ['work_item'], 'required': ['acceptance', 'verified_by', 'relations']}],
        'action_types': [{'id': 'approve', 'actor': 'owner', 'input': 'task', 'output': 'decision', 'guard': 'owner'}],
        'source_systems': [{'id': 'tests'}],
        'lifecycle': [{'id': 'verify', 'action': 'approve', 'evidence': ['tests']}],
        'custom_metadata': {'preserve': [1, None, False]}}


class SourceCatalogTests(unittest.TestCase):
    def bundle(self, source=None):
        source = source or fixture()
        raw = catalog.canonical(source).encode()
        return catalog.extract(source, namespace='example', revision='fixture-1', source_path='ontology.json', source_sha256=hashlib.sha256(raw).hexdigest())

    def test_lossless_roundtrip_and_stable_identity(self):
        s = fixture(); b = self.bundle(s)
        self.assertEqual(catalog.reconstruct(b), s)
        self.assertEqual(b, self.bundle(s))
        self.assertEqual(catalog.compare(b, s, b['source']['sha256'])['roundtrip'], 'all_fields_equal')

    def test_narrated_state_and_permissions_are_not_adopted(self):
        b = self.bundle()
        self.assertTrue(all(o['verification'] == 'unverified' for o in b['objects']))
        self.assertEqual(b['objects'][0]['record_layer'], 'dop_support')
        self.assertEqual(b['objects'][1]['view_type'], 'Task')
        self.assertEqual(b['authority']['effects'], [])
        self.assertFalse(b['authority']['inherited_permissions'])

    def test_derived_fields_cannot_be_blessed(self):
        for mutate in [lambda b: b['authority'].update(inherited_permissions=True),
                       lambda b: b['objects'][1].update(verification='verified'),
                       lambda b: b['relations'][0].update(basis='confirmed_by_test'),
                       lambda b: b['counts'].update(objects=999)]:
            with self.subTest(mutate=mutate):
                b = self.bundle(); mutate(b)
                with self.assertRaises(catalog.CatalogError): catalog.verify(b)

    def test_broken_source_contracts_rejected(self):
        for mutate in [lambda s: s['objects'].append(copy.deepcopy(s['objects'][0])),
                       lambda s: s['relations'][0].update(to='missing'),
                       lambda s: s['relations'][0].update(origin=''),
                       lambda s: s['objects'][1].pop('acceptance'),
                       lambda s: s['action_types'][0].update(actor='missing'),
                       lambda s: s['lifecycle'][0].update(evidence=['missing'])]:
            with self.subTest(mutate=mutate):
                s = fixture(); mutate(s)
                with self.assertRaises(catalog.CatalogError): self.bundle(s)

    def test_byte_drift_and_record_tampering_rejected(self):
        b = self.bundle()
        with self.assertRaises(catalog.CatalogError): catalog.compare(b, fixture(), '0' * 64)
        b['objects'][1]['source_record']['title'] = 'changed'
        with self.assertRaises(catalog.CatalogError): catalog.verify(b)

    def test_json_and_file_ownership_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'bundle.json'; b = self.bundle()
            self.assertEqual(catalog.save(p, b), 'created')
            self.assertEqual(catalog.save(p, b), 'unchanged')
            with self.assertRaises(catalog.CatalogError): catalog.save(p, {'different': True})
            self.assertEqual(catalog.read_json(p)[0], b)
            for raw in ['{"a":1,"a":2}', '{"a":NaN}']:
                p.write_text(raw)
                with self.assertRaises(catalog.CatalogError): catalog.read_json(p)


if __name__ == '__main__':
    unittest.main()

import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('graph_test',Path(__file__).resolve().parents[1]/'seed/wiki_graph.py')
g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)


class GraphTests(unittest.TestCase):
    def nodes(self):return {k:dict(id=k,type='task',title='객체 '+k,purpose='연결을 확인') for k in ['A','B','C']}

    def test_direction_provenance_and_state_are_separate(self):
        nodes=self.nodes();nodes['B']['verification']='passed'
        rel=[dict(**{'from':'A','to':'B'},type='depends_on',basis='unknown'),dict(**{'from':'B','to':'C'},type='produces',basis='confirmed_by_test')]
        out=g.render(nodes,rel,'B',{'C':'stale'})
        self.assertIn('data-from="A" data-to="B"',out);self.assertIn('data-from="B" data-to="C"',out)
        self.assertIn('edge inferred',out);self.assertIn('오래된 검사',out)
        self.assertNotIn('검사 통과',out)
        self.assertEqual(out,g.render(nodes,list(reversed(rel)),'B',{'C':'stale'}))

    def test_hidden_nodes_and_dangling_endpoints_are_not_disclosed(self):
        out=g.render(self.nodes(),[dict(**{'from':'A','to':'SECRET'},type='private')],'A')
        self.assertNotIn('SECRET',out);self.assertNotIn('private',out);self.assertIn('연결 기록 없음',out)

    def test_cycles_self_edges_and_overflow_retain_full_accessible_list(self):
        nodes=self.nodes();edges=[dict(**{'from':'B','to':k},type='rel',basis='unknown') for k in nodes]
        edges.append(dict(**{'from':'A','to':'B'},type='reverse',basis='unknown'))
        out=g.render(nodes,edges,'B',limit=1)
        self.assertIn('전체 연결 4건',out);self.assertIn('자기 연결 1건',out);self.assertIn('1개 이웃',out)
        self.assertIn('href="C.html"',out)

    def test_untrusted_content_cannot_supply_markup_or_destinations(self):
        nodes=self.nodes();nodes['A']['title']='<script>alert(1)</script>'
        out=g.render(nodes,[],'A');self.assertNotIn('<script>',out);self.assertIn('&lt;script&gt;',out)
        self.assertNotIn('foreignObject',out);self.assertNotIn('https://',out)
        with self.assertRaises(ValueError):g.render({'javascript:evil':{}},[],'javascript:evil')

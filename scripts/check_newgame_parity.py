"""Read-only differential check against a pinned local Newgame source tree.

Copies only two approved input files into a disposable compiler fixture. Never
calls generate(), writes to Newgame, sends data, or imports its status as truth.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);mod=importlib.util.module_from_spec(spec);sys.modules[name]=mod;spec.loader.exec_module(mod);return mod


def check(reference,commit):
    actual=subprocess.check_output(['git','-C',str(reference),'rev-parse','HEAD']).decode().strip()
    if actual!=commit:raise ValueError('Reference commit differs')
    source_paths=['scripts/generate_project_ontology.py','docs/assets/code-module-map.json','docs/design/current-milestone-workline.md']
    for path in source_paths:
        committed=subprocess.check_output(['git','-C',str(reference),'show',commit+':'+path])
        if committed.replace(b'\r\n',b'\n')!=(reference/path).read_bytes().replace(b'\r\n',b'\n'):raise ValueError('Uncommitted reference source drift: '+path)
    authority=load('newgame_read_only_reference',reference/source_paths[0])
    w=load('workspace',ROOT/'seed/workspace.py');compiler=load('compiler',ROOT/'seed/workspace_sources.py')
    baseline_modules=json.loads((reference/source_paths[1]).read_bytes())['modules']
    baseline_work=authority.milestone_work_items(reference/source_paths[2])
    with tempfile.TemporaryDirectory() as folder:
        root=Path(folder);(root/'data').mkdir();(root/'docs').mkdir()
        shutil.copyfile(reference/source_paths[1],root/'data/modules.json');shutil.copyfile(reference/source_paths[2],root/'docs/work.md')
        policy={'schema_version':1,'access_mode':'loopback_read_only','profile':w.PROFILE,'project_id':'PARITY','authority_ref':'user-local-comparison','roles':{'owner':['read']},'principals':{},'sources':[{'path':'data','kind':'data','roles':['owner']},{'path':'docs','kind':'documents','roles':['owner']}],'registry':'registry.json','accounts':None}
        recipe={'schema_version':1,'inputs':[
            {'path':'data/modules.json','format':'json_records','selector':'modules','prefix':'MOD-','type':'module','fields':{'id':'id','title':'label','purpose':'path','acceptance':None,'owner':None,'declared_state':None},'row_prefixes':[]},
            {'path':'docs/work.md','format':'markdown_table','selector':'','prefix':'WORK-','type':'task','fields':{'id':'0','title':'1','purpose':'2','acceptance':'3','owner':None,'declared_state':'0'},'row_prefixes':['BASE-',*[f'P{i}-' for i in range(1,11)]]}
        ],'relations':[]}
        (root/'policy.json').write_bytes(w.encoded(policy));(root/'data/mapping.json').write_bytes(w.encoded(recipe))
        candidate=compiler.compile_registry(root,'policy.json','data/mapping.json')
        by_native={candidate['contracts'][o['id']]['native_id']:o for o in candidate['objects']}
        expected={m['id']:{'title':m['label'],'purpose':m['path'],'type':'module'} for m in baseline_modules}
        expected.update({m['milestone_id']:{'title':m['label'].split(' · ',1)[1],'purpose':m['summary'],'type':'task'} for m in baseline_work})
        if set(expected)!=set(by_native):raise ValueError('Missing/extra identities')
        for key,fields in expected.items():
            if fields!={k:by_native[key][k] for k in fields}:raise ValueError('Business field mismatch: '+key)
        for m in baseline_work:
            obj=by_native[m['milestone_id']]
            if candidate['contracts'][obj['id']]['acceptance'][0]!=m['acceptance'].split(' · E2E:',1)[0]:raise ValueError('Player acceptance mismatch')
        if len(candidate['relations'])!=len(expected):raise ValueError('Source relationship coverage mismatch')
        (root/'registry.json').write_bytes(w.encoded(candidate));ws=w.Workspace(root);ws.initialize('policy.json');ws.collect('comparison')
        view=ws.read_only_view()
        if any(s['workflow']!='needs_decision' or s['verification']!='unverified' for s in view['states'].values()):raise ValueError('Source claims promoted to execution truth')
        replay=ws.collect('comparison')
        if replay['outcome']!='unchanged':raise ValueError('Replay differs')
        result={'reference_commit':actual,'reference_sources':{p:hashlib.sha256((reference/p).read_bytes()).hexdigest() for p in source_paths},'module_objects_equal':len(baseline_modules),'work_objects_equal':len(baseline_work),'source_edges_complete':len(expected),'compared_fields':['native identity','title','purpose/source path','player acceptance for work items','documented_by coverage'],'intentional_differences':['OOP IDs are namespace + native-ID hash','Newgame documented implemented/confirmed statuses stay source declarations; candidate verification is unverified','Newgame E2E suffix remains in source, not inferred as a passing TestRun'],'outcome':'declared_fields_equal','replay':'unchanged','not_proven':['Full Newgame ontology topology','External live data/CI/deployment','Whole functional equivalence','Human acceptance'],'candidate_projection_sha256':w.sha(w.encoded(view))}
        return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--reference',type=Path,required=True);p.add_argument('--commit',required=True);a=p.parse_args()
    print(json.dumps(check(a.reference,a.commit),ensure_ascii=False,indent=2))

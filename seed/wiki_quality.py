"""Bounded wiki presentation audit and evidence-bound visual review gate.

Static checks are automated; browser observations are supplied by the operator.
Neither screenshots nor passing assertions authenticate a human approval.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import stat
import subprocess
import sys

PROFILE = 'wiki-quality-1'
TOPICS = {'start','product','design','modules','workflows','quality','decisions','history','workspaces'}
TYPES = {'requirement','task','decision','module','test','release'}
CHECKS = {'no_clipping','text_readable','hierarchy_clear','node_links_usable','details_usable'}


def encoded(v): return (json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def sha(raw): return hashlib.sha256(raw).hexdigest()
def need(ok,message):
    if not ok: raise ValueError(message)


def local(root,name):
    need(type(name) is str and 0<len(name)<=500 and not name.startswith('/') and '\\' not in name and ':' not in name,'Unsafe local evidence path')
    need(all(p and p not in {'.','..'} and p==p.rstrip(' .') for p in name.split('/')),'Unsafe local evidence path')
    root=Path(root).absolute();p=root/name
    for item in (p,*p.parents):
        if item.exists() or item.is_symlink():
            info=item.lstat();need(not stat.S_ISLNK(info.st_mode) and not getattr(info,'st_file_attributes',0)&0x400,'Reparse evidence path rejected')
    need(p.resolve().is_relative_to(root.resolve()),'Evidence outside project')
    return p


def read_json(path):
    raw=Path(path).read_bytes();need(len(raw)<=8_000_000,'Bounded JSON required')
    def pairs(items):
        v={}
        for k,x in items:need(k not in v,'Duplicate JSON key');v[k]=x
        return v
    return json.loads(raw,object_pairs_hook=pairs)


class Page(HTMLParser):
    def __init__(self,raw):
        super().__init__(convert_charrefs=True)
        self.links=[];self.h1=0;self.nav=0;self.details=0;self.graph=False;self.cards=False;self.viewport=False
        self.text=[];self.stack=[];self.blocks=[];self.unsafe=False
        self.feed(raw.decode('utf-8'));self.close()
        if self.stack:self.unsafe=True
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag in {'script','iframe','object','embed','form','input','button','base','link','foreignobject','animate','set','use','audio','video'}:self.unsafe=True
        if tag=='meta' and a.get('http-equiv','').lower()=='refresh':self.unsafe=True
        if tag!='a' and any(k in a for k in ('href','xlink:href')):self.unsafe=True
        if any(k.lower().startswith('on') for k,v in attrs):self.unsafe=True
        if tag=='h1':self.h1+=1
        if tag=='nav':self.nav+=1
        if tag=='details':self.details+=1
        if a.get('data-graph-profile')=='state-object-view-1':self.graph=True
        if 'cards' in a.get('class','').split():self.cards=True
        if tag=='meta' and a.get('name')=='viewport' and 'width=device-width' in a.get('content',''):self.viewport=True
        if tag=='a':self.links.append(a.get('href',''))
        if tag in {'p','h1','summary'}:self.stack.append([tag,''])
        if any(k in a for k in ('src','srcset')):self.unsafe=True
    def handle_endtag(self,tag):
        if self.stack and self.stack[-1][0]==tag:self.blocks.append(self.stack.pop())
    def handle_data(self,data):
        self.text.append(data)
        for block in self.stack:block[1]+=data


def draft_contract(data):
    pages={'index':dict(kind='overview',parent=None),'objects':dict(kind='index',parent='index'),'sources':dict(kind='sources',parent='index')}
    pages.update({p:dict(kind='topic',parent='index') for p in TOPICS})
    parents={'requirement':'product','task':'workflows','decision':'decisions','module':'modules','test':'quality','release':'history'}
    pages.update({o['id']:dict(kind='object',parent=parents[o['type']],object_type=o['type']) for o in data['objects']})
    return dict(schema_version=1,profile=PROFILE,mode='draft',pages=pages,source_bindings=[])


def audit(files,contract,root=None):
    """Audit actual HTML bytes, not a generator's claimed pass or optional check list."""
    need(type(contract) is dict and set(contract)=={'schema_version','profile','mode','pages','source_bindings'},'Quality contract fields differ')
    need(type(contract['schema_version']) is int and contract['schema_version']==1 and contract['profile']==PROFILE,'Unsupported quality version')
    need(contract['mode'] in {'draft','project'},'Unknown quality mode')
    pages=contract['pages'];need(type(pages) is dict and 18<=len(pages)<=1000,'Bounded complete wiki required')
    need({'index','objects','sources',*TOPICS}<=set(pages),'Required wiki topic missing')
    need(all(type(k) is str and re.fullmatch('[A-Za-z0-9][A-Za-z0-9_-]{0,95}',k) for k in pages),'Unsafe page ID')
    need(set(files)=={k+'.html' for k in pages},'HTML inventory differs from quality contract')
    kinds=set();parsed={};failures=[]
    def check(ok,page,code):
        if not ok:failures.append(dict(page=page,code=code))
    for ident,meta in pages.items():
        need(type(meta) is dict and set(meta)==({'kind','parent','object_type'} if meta.get('kind')=='object' else {'kind','parent'}),'Page contract fields differ')
        expected='overview' if ident=='index' else 'topic' if ident in TOPICS else 'index' if ident=='objects' else 'sources' if ident=='sources' else 'object'
        need(meta['kind']==expected,'Page kind cannot weaken required checks')
        if ident=='index':need(meta['parent'] is None,'Overview must be root')
        elif meta['kind']=='object':
            need(meta['object_type'] in TYPES and meta['parent'] in TOPICS,'Object type/topic parent required');kinds.add(meta['object_type'])
        else:need(meta['parent']=='index','Topic hierarchy differs')
        raw=files[ident+'.html'];need(type(raw) is bytes and len(raw)<=4_000_000,'Bounded HTML bytes required')
        p=Page(raw);parsed[ident]=p
        if re.search(rb'@import|url\(\s*[\x22\x27]?\s*(?:https?:|//|data:)|expression\(',raw,re.I):p.unsafe=True
        check(not p.unsafe,ident,'active_or_external_content')
        check(p.h1==1 and p.nav>0 and p.viewport,ident,'heading_navigation_viewport')
        check(p.details>0,ident,'progressive_disclosure_missing')
        check(all(len(t.strip())<=(140 if tag in {'h1','summary'} else 600) for tag,t in p.blocks),ident,'oversized_prose_block')
        check(all(h.endswith('.html') and h in files for h in p.links),ident,'broken_or_external_link')
        if meta['parent']:check(meta['parent']+'.html' in p.links,ident,'parent_link_missing')
        if meta['kind'] in {'overview','index','object'}:check(p.graph,ident,'object_graph_missing')
        if meta['kind'] in {'overview','index','topic'}:check(p.cards,ident,'document_cards_missing')
        content=' '.join(p.text)
        check('생성 근거' in content,ident,'lineage_missing')
        if meta['kind']=='object':
            for label in ('목적','다음 행동','근거 조회','미확인'):check(label in content,ident,'object_landmark_missing:'+label)
    need(kinds==TYPES,'Six object types required')
    for ident,meta in pages.items():
        if meta['parent']:check(ident+'.html' in parsed[meta['parent']].links,ident,'child_link_missing')
    bindings=contract['source_bindings'];need(type(bindings) is list and len(bindings)<=5000,'Bounded source bindings required')
    bound=set()
    for binding in bindings:
        need(type(binding) is dict and set(binding)=={'page','path','sha256'} and binding['page'] in pages,'Invalid source binding')
        need(type(binding['sha256']) is str and re.fullmatch('[0-9a-f]{64}',binding['sha256']),'Source digest required')
        need(root is not None,'Project root required for source bindings')
        source=local(root,binding['path']);check(source.is_file() and sha(source.read_bytes())==binding['sha256'],binding['page'],'source_missing_or_stale');bound.add(binding['page'])
    if contract['mode']=='project':
        for ident in pages:check(ident in bound,ident,'current_source_binding_missing')
    snapshot=sha(encoded(dict(contract=contract,html={k:sha(v) for k,v in sorted(files.items())})))
    return dict(profile=PROFILE,state='structure_passed' if not failures else 'blocked',snapshot=snapshot,mode=contract['mode'],failures=failures,visual='pending',human_acceptance='human_pending',bootstrap_ready=False,limits=['Static layout thresholds are heuristics, not visual or semantic certification.','Source digests establish freshness against declared sources, not completeness or truth.','This checker does not supply access control or authenticate observer identity.'])


def visual_check(report,review,root,files,contract):
    need(report['state']=='structure_passed','Structural checks must pass first')
    need(type(review) is dict and set(review)=={'schema_version','profile','snapshot','observer','reference','observations'},'Visual receipt fields differ')
    need(type(review['schema_version']) is int and review['schema_version']==1 and review['profile']==PROFILE and review['snapshot']==report['snapshot'],'Visual evidence stale or unsupported')
    need(type(review['observer']) is str and 0<len(review['observer'])<=200,'Observer required')
    def artifact(item):
        need(type(item) is dict and set(item)=={'path','sha256'},'Image evidence fields differ')
        p=local(root,item['path']);need(p.suffix.lower()=='.png' and p.is_file() and p.stat().st_size<=20_000_000,'Bounded PNG evidence required')
        raw=p.read_bytes();need(raw.startswith(b'\x89PNG\r\n\x1a\n') and len(raw)>=24 and raw[12:16]==b'IHDR' and sha(raw)==item['sha256'],'Image evidence changed or not PNG')
        return (int.from_bytes(raw[16:20],'big'),int.from_bytes(raw[20:24],'big'))
    ref=review['reference'];need(type(ref) is dict and set(ref)=={'label','image'},'Visual reference required')
    need(type(ref['label']) is str and 0<len(ref['label'])<=500,'Reference label required');artifact(ref['image'])
    observations=review['observations'];need(type(observations) is list and 6<=len(observations)<=100,'Bounded visual observations required')
    covered=set();seen=set()
    for obs in observations:
        need(type(obs) is dict and set(obs)=={'page','width','html_sha256','image','checks'},'Observation fields differ')
        name=obs['page'];need(name in files and type(obs['width']) is int and obs['width'] in (390,1280),'Required viewport must be 390 or 1280 CSS px')
        need(obs['html_sha256']==sha(files[name]),'Observed page has changed')
        need((name,obs['width']) not in seen,'Duplicate observation');seen.add((name,obs['width']))
        width,height=artifact(obs['image']);need(width in {obs['width'],obs['width']*2,obs['width']*3} and height>0,'PNG width does not match declared viewport/device scale')
        need(type(obs['checks']) is dict and set(obs['checks'])==CHECKS and all(v is True for v in obs['checks'].values()),'Visual checks failed or incomplete')
        kind=contract['pages'][name[:-5]]['kind'];covered.add((kind,obs['width']))
    need({(kind,width) for kind in ('overview','topic','object') for width in (390,1280)}<=covered,'Overview/topic/object observations required at both widths')
    return {**report,'state':'visual_review_recorded','visual':'recorded','observer':review['observer'],'human_acceptance':'human_pending'}


def bind_bootstrap(binding,site_name,files):
    names={site_name+'/'+n:sha(raw) for n,raw in files.items()}
    need(binding.get('entrypoint')==site_name+'/index.html' and set(binding.get('documents',[]))==set(names),'Bootstrap and quality must cover the same wiki')
    need(all(binding.get('input_sha256',{}).get(n)==h for n,h in names.items()),'Bootstrap HTML snapshot differs')


def check_run(root,contract_name,site_name,contract,binding):
    need(Path(__file__).resolve()==local(root,'wiki_quality.py').resolve(),'Gate must run the installed project quality component')
    spec=importlib.util.spec_from_file_location('quality_runtime',local(root,'harness.py'))
    runtime=importlib.util.module_from_spec(spec);spec.loader.exec_module(runtime)
    try:
        core=runtime.Core(root);events=core.read();state=core.status(binding['validation_task']);policy=core.policy(events)
        need(state['verification']=='passed','Current required Run is missing or stale')
        need('wiki-quality' in state['input_snapshot']['commands'],'Required wiki-quality test missing from Run')
        command=policy['commands'].get('wiki-quality',{}).get('argv',[])
        need(command[1:]==['-B','wiki_quality.py','check','--site',site_name,'--contract',contract_name],'Pinned wiki-quality command differs from reviewed wiki')
        required={'wiki_quality.py',contract_name,*[b['path'] for b in contract['source_bindings']]}
        need(all(state['input_snapshot']['files'].get(n)==sha(local(root,n).read_bytes()) for n in required),'Quality component, contract and sources must be bound to tested Run')
    except runtime.HarnessError as exc:raise ValueError(str(exc)) from exc


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['check','review-template','gate'])
    parser.add_argument('--site',required=True);parser.add_argument('--contract',required=True)
    parser.add_argument('--root',type=Path,default=Path.cwd());parser.add_argument('--review');parser.add_argument('--binding')
    args=parser.parse_args()
    try:
        site=local(args.root,args.site);contract=read_json(local(args.root,args.contract))
        need(site.is_dir(),'Site missing')
        paths=list(site.glob('*.html'));need(0<len(paths)<=1000,'Bounded HTML inventory required')
        files={p.name:local(args.root,p.relative_to(args.root.absolute()).as_posix()).read_bytes() for p in paths}
        result=audit(files,contract,args.root)
        if args.command=='review-template':
            need(result['state']=='structure_passed','Repair structural failures before visual review')
            representatives=[next(k+'.html' for k,v in contract['pages'].items() if v['kind']==kind) for kind in ('overview','topic','object')]
            template=dict(schema_version=1,profile=PROFILE,snapshot=result['snapshot'],observer='',reference={'label':'','image':{'path':'','sha256':''}},observations=[dict(page=name,width=width,html_sha256=sha(files[name]),image={'path':'','sha256':''},checks={k:False for k in sorted(CHECKS)}) for name in representatives for width in (390,1280)])
            print(encoded(template).decode());return 0
        if args.review:result=visual_check(result,read_json(local(args.root,args.review)),args.root,files,contract)
        if args.command=='gate':
            need(contract['mode']=='project','Draft never satisfies project readiness')
            need(args.review and args.binding and result['visual']=='recorded','Visual receipt and bootstrap binding required')
            binding=local(args.root,args.binding);need(binding.is_file(),'Bootstrap binding missing')
            binding_value=read_json(binding);bind_bootstrap(binding_value,args.site,files)
            check_run(args.root,args.contract,args.site,contract,binding_value)
            core=Path(__file__).with_name('bootstrap.py')
            proc=subprocess.run([sys.executable,'-B',str(core),'--binding',str(binding)],cwd=args.root,capture_output=True,timeout=120)
            need(proc.returncode==0,'Bootstrap gate failed; preserve its binding and run evidence')
            gate=json.loads(proc.stdout);need(gate.get('state')=='bootstrap_ready','Bootstrap did not establish readiness')
            result.update(state='wiki_review_ready',bootstrap_ready=True,bootstrap=gate)
        print(encoded(result).decode());return 0 if result['state']!='blocked' else 2
    except (ValueError,KeyError,TypeError,OSError,subprocess.TimeoutExpired) as exc:
        print(json.dumps({'profile':PROFILE,'state':'blocked','reason':str(exc),'human_acceptance':'human_pending'}));return 2


if __name__=='__main__':raise SystemExit(main())

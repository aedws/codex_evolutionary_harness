"""Default domain-neutral wiki presentation. No HTTP server, fixed roles or state authority."""
import argparse
import hashlib
import html
import json
from pathlib import Path
import re

import wiki_core

PROFILE = 'newgame-style-wiki-1'
TOPICS = {
    'start': '처음 사용하기', 'product': '제품과 기능', 'design': '설계와 데이터',
    'modules': '모듈과 도구', 'workflows': '남은 작업 순서', 'quality': '검증과 문제 해결',
    'decisions': '오너 결정', 'history': '개발 이력', 'workspaces': '역할별 시작 경로',
}


def encoded(value):
    return (json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()


def sha(raw):return hashlib.sha256(raw).hexdigest()


def need(condition,message):
    if not condition:raise ValueError(message)


def text(value):
    need(type(value) is str and bool(value.strip()) and len(value)<=20000,'Required bounded text missing')


def strings(value):
    need(type(value) is list and bool(value),'Nonempty list required')
    for item in value:text(item)


def scaffold():
    return {'schema_version':1,'profile':PROFILE,'template_only':True,'project_name':None,
            'purpose':None,'scope':None,'unknowns':[],
            'topics':{key:{'purpose':None,'current_scope':None,'actions':[],
                           'source_refs':[],'unknowns':[]} for key in TOPICS},'tasks':[]}


def validate(content,tree):
    need(type(content) is dict and set(content)==set(scaffold()),'Unsupported wiki content fields')
    need(type(content['schema_version']) is int and content['schema_version']==1 and content['profile']==PROFILE,'Unsupported presentation profile')
    need(content['template_only'] is False,'Scaffold is incomplete; populate from project evidence')
    for key in ['project_name','purpose','scope']:text(content[key])
    strings(content['unknowns'])
    need(type(content['topics']) is dict and set(content['topics'])==set(TOPICS),'Nine topics required')
    for topic in content['topics'].values():
        need(type(topic) is dict and set(topic)=={'purpose','current_scope','actions','source_refs','unknowns'},'Topic contract missing')
        text(topic['purpose']);text(topic['current_scope'])
        for key in ['actions','source_refs','unknowns']:strings(topic[key])
    need(type(content['tasks']) is list and 1<=len(content['tasks'])<=500,'Ordered remaining work required')
    seen=set()
    for task in content['tasks']:
        need(type(task) is dict and set(task)=={'id','title','purpose','depends_on','deliverables','acceptance','owner_decision','source_refs'},'Task completion contract missing')
        ident=task['id']
        need(type(ident) is str and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]*',ident) and ident not in seen|set(TOPICS)|{'index'},'Duplicate or unsafe task ID')
        for key in ['title','purpose','owner_decision']:text(task[key])
        for key in ['deliverables','acceptance','source_refs']:strings(task[key])
        deps=task['depends_on']
        need(type(deps) is list and all(type(d) is str for d in deps) and len(deps)==len(set(deps)) and set(deps)<=seen,'Missing/cyclic/out-of-order dependency')
        seen.add(ident)
    nodes=wiki_core.validate(tree)
    need(set(nodes)=={'index',*TOPICS,*seen} and tree['root']=='index','Default layout tree must match content')
    need(all(nodes[k]['parent']=='index' for k in TOPICS),'Topics must belong to overview')
    need(all(nodes[k]['parent']=='workflows' for k in seen),'Task details must belong to workline')
    need(all(n['page']==ident+'.html' for ident,n in nodes.items()),'Canonical presentation paths required')
    return nodes


CSS='''*{box-sizing:border-box}body{margin:0;background:#f4f6f2;color:#263e35;font:15px/1.8 system-ui}a{color:#35694e;text-decoration:none}a:hover{text-decoration:underline}aside{position:fixed;inset:0 auto 0 0;width:220px;padding:28px 20px;background:#fcfdfb;border-right:1px solid #dce4d7;overflow:auto}aside strong{display:block;font-size:18px;margin-bottom:20px}aside a{display:block;padding:8px;font-size:13px}main{margin-left:220px;max-width:1300px;padding:30px 5vw 70px}h1{font-size:30px;line-height:1.4}h2{font-size:20px}h3{font-size:16px}article,section{background:white;border:1px solid #dce4d7;border-radius:8px;padding:24px;margin:20px 0}.hero{background:#eaf0e2;border-top:3px solid #56784c}.cards{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}.cards a{padding:18px;background:white;border:1px solid #dce4d7;border-radius:7px}.cards strong,.cards small{display:block}.tag{font-size:11px;background:#f3ecd7;color:#776039;padding:5px 9px;border-radius:4px}.muted,small{color:#78846d}nav{font-size:12px}li{margin:8px 0}table{width:100%;border-collapse:collapse;font-size:13px}td,th{text-align:left;padding:13px;border-bottom:1px solid #dce4d7;vertical-align:top}th{background:#f1f5eb}td p{margin:4px 0;font-size:12px;color:#78846d}.table-scroll{overflow:auto}details{border:1px solid #dce4d7;padding:15px;background:white;border-radius:7px;margin:18px 0}summary{cursor:pointer}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:12px/1.8 monospace}.tree section{padding:12px 18px}.tree h2{font-size:12px}.tree ul{display:flex;flex-wrap:wrap;gap:10px;list-style:none;padding:0;max-height:120px;overflow:auto}.tree a{font-size:12px}.tree section:has(ul:empty){display:none}@media(max-width:800px){aside{position:static;width:auto;padding:15px}aside a{display:inline-block}main{margin:0;padding:20px}.cards{grid-template-columns:1fr}h1{font-size:25px}section,article{padding:17px}}@media print{aside,.tree{display:none}main{margin:0;padding:0}}'''


def render(content,tree):
    nodes=validate(content,tree);outputs={}
    esc=html.escape
    def listing(items):return '<ul>'+''.join('<li>'+esc(s)+'</li>' for s in items)+'</ul>'
    for role in tree['roles']:
        allowed={ident for ident,n in nodes.items() if role in n['grants']['read']}
        tasks=[t for t in content['tasks'] if t['id'] in allowed]
        def link(ident,label):return '<a href="'+ident+'.html">'+esc(label)+'</a>' if ident in allowed else ''
        def worktable(items):
            return '<div class="table-scroll"><table><tr><th>순서</th><th>남은 작업</th><th>선행 작업</th></tr>'+''.join('<tr><td>'+str(i)+'</td><td>'+link(t['id'],t['title'])+'<p>'+esc(t['purpose'])+'</p></td><td>'+(' · '.join(link(d,nodes[d]['title']) for d in t['depends_on'] if d in allowed) or '별도 착수 조건 확인')+'</td></tr>' for i,t in enumerate(items,1))+'</table></div>'
        for ident in sorted(allowed):
            title=content['project_name']+' · 종합 문서' if ident=='index' else TOPICS.get(ident,nodes[ident]['title'])
            if ident=='index':
                body='<section class="hero"><span class="tag">프로젝트 범위 안내 · 완료 인증 아님</span><h2>'+esc(content['purpose'])+'</h2><p>'+esc(content['scope'])+'</p></section>'
                body+='<div class="cards">'+''.join(link(key,label) for key,label in [('start','사용법부터 보기'),('workflows','남은 작업 순서'),('decisions','내가 결정할 것')])+'</div>'
                body+='<section><h2>다음 작업</h2>'+worktable(tasks[:3])+link('workflows','전체 작업 순서 보기')+'</section><section><h2>주제에서 세부 문서로</h2>'+listing([])+''.join('<p>'+link(key,label)+'</p>' for key,label in TOPICS.items() if key in allowed)+'</section><section><h2>미확인과 한계</h2>'+listing(content['unknowns'])+'</section>'
            elif ident in TOPICS:
                topic=content['topics'][ident]
                body='<article><h2>목적</h2><p>'+esc(topic['purpose'])+'</p><h2>지금 있는 것과 남은 것</h2><p>'+esc(topic['current_scope'])+'</p><h2>읽는 순서와 다음 행동</h2>'+listing(topic['actions'])+'</article>'
                if ident=='workflows':body='<section><h2>순서대로 보는 남은 작업</h2><p>계획 제안입니다. 실행·검증·오너 수락은 별도 근거가 필요합니다.</p>'+worktable(tasks)+'</section>'+body
                body+='<details><summary>출처와 미확인 사항</summary>'+listing(topic['source_refs'])+listing(topic['unknowns'])+'</details>'
            else:
                task=next(t for t in tasks if t['id']==ident)
                body='<article><span class="tag">계획 제안 · 실행 검증 미확인</span><h2>'+esc(task['purpose'])+'</h2><p>작업 ID: '+esc(ident)+'</p></article><section><h2>만들 결과</h2>'+listing(task['deliverables'])+'<h2>끝났다고 판단할 기준</h2>'+listing(task['acceptance'])+'</section><section><h2>오너 판단과 착수 조건</h2><p>'+esc(task['owner_decision'])+'</p>'+''.join('<p>'+link(d,nodes[d]['title'])+'</p>' for d in task['depends_on'] if d in allowed)+'</section><details><summary>원본과 근거 참조</summary>'+listing(task['source_refs'])+'</details>'+link('workflows','전체 작업 순서로 돌아가기')
            # No hidden-role content/source hashes in role outputs. The whole manifest is local control data.
            lineage={'rule':PROFILE,'view':ident,'scope':'authored project prose and planned work; no status reducer or authenticated acceptance','missing':'Version-bound Run/Evidence adapter required for verified/current/released claims'}
            body+='<details><summary>이 View가 생성되는 기준</summary><pre>'+esc(json.dumps(lineage,ensure_ascii=False,indent=2))+'</pre></details>'
            sidebar='<aside><strong>'+esc(content['project_name'])+'</strong>'+link('index','종합 문서')+''.join(link(k,v) for k,v in TOPICS.items())+'</aside>'
            raw='<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+esc(title)+'</title><style>'+CSS+'</style>'+sidebar+'<main><div class="tree">'+wiki_core.navigation(tree,ident,role)+'</div><h1>'+esc(title)+'</h1><p class="muted">읽기 전용 · 객체는 이해를 위한 화면, 근거는 별도 기록</p>'+body+'</main></html>'
            outputs[role+'/'+ident+'.html']=raw.encode()
    return outputs


def no_links(path):
    for p in (path,*path.parents):
        if p.exists():
            need(not p.is_symlink() and not getattr(p.lstat(),'st_file_attributes',0)&0x400,'Reparse output path rejected')


def write_bundle(out,outputs,manifest):
    """Immutable render directory. Different input needs a new directory; no overwrite recovery."""
    out=Path(out).absolute();no_links(out)
    expected={**outputs,'manifest.json':encoded(manifest)}
    if out.exists():
        actual={p.relative_to(out).as_posix() for p in out.rglob('*') if p.is_file()}
        need(actual==set(expected),'Existing output conflict or partial write; inspect and use a new directory')
        for name,raw in expected.items():
            no_links(out/name);need((out/name).read_bytes()==raw,'Output drift; no overwrite')
        return 'unchanged'
    out.mkdir(parents=True,exist_ok=False)
    for name,raw in expected.items():
        path=out/name;no_links(path);path.parent.mkdir(exist_ok=True)
        with path.open('xb') as stream:stream.write(raw)
    return 'written'


def load(path):
    def pairs(items):
        out={}
        for k,v in items:need(k not in out,'Duplicate JSON key');out[k]=v
        return out
    return json.loads(Path(path).read_bytes(),object_pairs_hook=pairs)


def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='command',required=True)
    init=sub.add_parser('scaffold');init.add_argument('--out',type=Path,required=True)
    for name in ['check','build']:
        p=sub.add_parser(name);p.add_argument('--content',type=Path,required=True);p.add_argument('--tree',type=Path,required=True)
        if name=='build':p.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    try:
        if args.command=='scaffold':
            no_links(args.out.absolute());args.out.parent.mkdir(parents=True,exist_ok=True)
            raw=encoded(scaffold())
            if args.out.exists():need(args.out.read_bytes()==raw,'Existing authored content; no overwrite')
            else:
                with args.out.open('xb') as stream:stream.write(raw)
            result={'state':'template_only','next':'Populate project content and interview owner before tree/access setup'}
        else:
            content=load(args.content);tree=load(args.tree);outputs=render(content,tree)
            manifest={'profile':PROFILE,'content_sha256':sha(args.content.read_bytes()),'tree_sha256':sha(args.tree.read_bytes()),'renderer_sha256':sha(Path(__file__).read_bytes()),'wiki_core_sha256':sha(Path(wiki_core.__file__).read_bytes()),'outputs':{n:sha(raw) for n,raw in outputs.items()},'state':'presentation_checked','limits':['Not bootstrap_ready or HTTP access enforcement','Manifest/control input must not be served to restricted roles','Project copy must bind required evidence, role adapter and bootstrap gate']}
            result=manifest
            if args.command=='build':result={**manifest,'write_outcome':write_bundle(args.out,outputs,manifest)}
        print(json.dumps(result,ensure_ascii=False));return 0
    except (ValueError,KeyError,TypeError,OSError) as exc:
        print(json.dumps({'state':'blocked','message':str(exc)},ensure_ascii=False));return 2


if __name__=='__main__':raise SystemExit(main())

"""OOP navigation over authenticated workspace projections. No authored workflow state."""
from html import escape
from html.parser import HTMLParser
from urllib.parse import urlencode
import secrets
import re

LABELS={'needs_decision':'결정 필요','ready':'착수 가능','in_progress':'진행 중','review_pending':'수락 대기','blocked':'진행 차단','deferred':'보류','accepted':'수락 기록 있음'}
TABS={'overview':'작업 개요','decisions':'판단 대기열','objects':'객체 탐색','lineage':'관계·근거','documents':'전체 문서'}
KINDS={'requirement':'요구','task':'작업','decision':'결정','module':'모듈','test':'검사','release':'릴리스'}
VALUES={'passed':'통과','failed':'실패','unverified':'미검증','unknown':'미확인','stale':'재확인 필요','running':'실행 중','conflicted':'근거 충돌','pending':'대기','human_recorded':'판단 기록 있음','unobserved':'관측 없음','released':'지정 대상 관찰 통과','rolled_back':'이전 버전 복원','effect_unknown':'효과 확인 필요','reconciled_candidate':'후보 활성 상태 재확인','reconciled_previous':'이전 활성 상태 재확인','aborted':'활성화 전 중단'}
CSS='''*{box-sizing:border-box}.card,details{overflow-wrap:anywhere;min-width:0}body{margin:0;background:#f4f6f2;color:#213d35;font:15px/1.65 system-ui}header,main{max-width:1160px;margin:auto;padding:22px}h1{font-size:28px}nav{display:flex;gap:18px;flex-wrap:wrap}a{color:#246753}small{display:block;color:#566d65}input,select,button{font:inherit;padding:8px;max-width:100%}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,290px),1fr));gap:16px}.card,details{border:1px solid #d6dfd7;background:white;border-radius:9px;padding:16px;margin:10px 0}.item{border-top:1px solid #e4e9e3;padding:12px 0;overflow-wrap:anywhere}.bad{color:#a0403c}.meta{display:flex;gap:12px;flex-wrap:wrap}summary{cursor:pointer}li{overflow-wrap:anywhere}a:focus,summary:focus{outline:3px solid #79ad83}form{display:flex;gap:8px;flex-wrap:wrap}@media(max-width:600px){header,main{padding:14px}h1{font-size:23px}}'''


def render(view,tab='overview',focus=None,query='',page=0,source_route='/source'):
    if tab not in TABS:raise ValueError('Unknown tab')
    if not re.fullmatch(r'/[A-Za-z0-9_./-]+',source_route) or '..' in source_route:raise ValueError('Unsafe source route')
    if type(page) is not int or page<0:raise ValueError('Invalid page')
    objects=view['objects'];states=view['states'];esc=escape
    if focus and focus not in objects:raise ValueError('Forbidden/unknown focus')
    filters=view.get('filters',{})
    def url(**kw):return '?'+urlencode(dict(tab=tab,query=query,kind=filters.get('kind',''),state=filters.get('state',''),**kw))
    def link(key):return '<a href="'+esc(url(focus=key))+'#object-detail">'+esc(objects[key]['title'])+'</a>'
    out=['<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>프로젝트 운영 위키</title><style>'+CSS+'</style><body><header><small>VIEW TO OOP · SET UP TO DOP</small><h1>프로젝트 운영 위키</h1><nav>']
    out += ['<a href="?'+urlencode({'tab':k})+'">'+v+'</a>' for k,v in TABS.items()]
    out += ['</nav></header><main><h2>'+TABS[tab]+'</h2><p>업무 상태 · 검사 상태 · 인간 수락 · 배포를 따로 봅니다. 등록 건수는 목표 완성률이 아닙니다.</p>']
    if tab in {'overview','decisions','objects'}:
        out+=['<form method="get"><input type="hidden" name="tab" value="'+tab+'"><label>목적·객체 검색 <input name="query" value="'+esc(query)+'"></label>']
        for name,label,choices in [('kind','객체 유형',{'':'전체','requirement':'요구','task':'작업','decision':'결정','module':'모듈','test':'검사','release':'릴리스'}),('state','업무 상태',{'':'전체',**LABELS})]:
            out+=['<label>'+label+' <select name="'+name+'">'+''.join('<option value="'+k+'"'+(' selected' if filters.get(name)==k else '')+'>'+v+'</option>' for k,v in choices.items())+'</select></label>']
        out+=['<button>검색</button></form>']
        matches=view['matches']
        if tab=='decisions':matches=[k for k in matches if states[k]['workflow'] in {'needs_decision','blocked','review_pending'}]
        out+=['<p>조회 결과 '+str(len(matches))+'개</p><div class="grid">']
        for state,label in LABELS.items():
            members=[k for k in matches if states[k]['workflow']==state]
            if not members:continue
            selected=members[page*6:(page+1)*6]
            if not selected:continue
            out+=['<section class="card" data-workflow="'+state+'"><h3>'+label+' · '+str(len(members))+'</h3>']
            for key in selected:
                s=states[key];o=objects[key]
                out+=['<div class="item" data-object="'+esc(key)+'" data-verification="'+esc(s['verification'])+'">'+link(key)+'<small>'+esc(KINDS[o['type']]+' · '+key)+'</small><p>'+esc(o['purpose'])+'</p><p>다음: '+esc(s['next_action'])+'</p><small>검사 '+esc(VALUES[s['verification']])+' · 수락 '+esc(VALUES[s['acceptance']])+' · 배포 '+esc(VALUES[s['delivery']])+'</small></div>']
            if len(members)>(page+1)*6:out+=['<a href="'+esc(url(page=page+1))+'">다음 6개</a>']
            out+=['</section>']
        out+=['</div>']
        if page:out+=['<a href="'+esc(url(page=page-1))+'">이전 페이지</a>']
        if not matches:out+=['<p>조건에 맞는 객체가 없습니다.</p>'];focus=None
    if focus:
        obj=objects[focus];s=states[focus]
        out+=['<section class="card" id="object-detail"><h2>'+esc(obj['title'])+'</h2><p>'+esc(obj['purpose'])+'</p><p>'+esc(LABELS[s['workflow']]+' / 검사 '+VALUES[s['verification']])+'</p><p>다음 행동: '+esc(s['next_action'])+'</p><h3>선행 조건</h3><ul>']
        out+=['<li>'+link(k)+'</li>' for k in obj['depends_on']]
        out+=['</ul><h3>원본과 판정 근거</h3><ul>']
        out+=['<li>'+esc(p)+'<small>'+esc(view['sources'][p]['sha256'])+'</small></li>' for p in obj['sources']]
        out+=['</ul><details><summary>Event → 규칙 → 상태 생성 경로</summary><p>운영 규칙 operating-workspace-1 · revision '+str(s['revision'])+'</p><p>이벤트 '+esc(str(s['events']))+'</p><p>현재 Snapshot '+esc(s['snapshot'])+'</p><p>원본 변경 '+str(s['source_stale'])+' · 선행 차단 '+str(s['dependency_blocked'])+'</p><p>Core 근거 '+esc(str(s['core_evidence']))+'</p></details>']
        actions={'propose':'제안 기록','authorize':'범위 승인','start':'착수 기록','submit':'검토 요청','accept':'수락 판단','defer':'보류','block':'차단','resume':'재개 검토'}
        if view.get('capabilities'):
            out+=['<details><summary>업무 판단 기록</summary><p>제안·착수 기록은 구현 증명이 아닙니다. 서버가 독립 승인·현재 검사·선행 조건을 다시 판정합니다.</p><form method="post" action="/action-form">']
            for k,v in {'subject':focus,'key':'UI-'+secrets.token_hex(16),'expected_revision':str(s['revision']),'snapshot':s['snapshot']}.items():out+=['<input type="hidden" name="'+k+'" value="'+esc(v)+'">']
            out+=['<label>행동 <select name="action">'+''.join('<option value="'+k+'">'+actions[k]+'</option>' for k in view['capabilities'])+'</select></label><label>판단 근거 <input name="reason" required maxlength="4000"></label><button>기록 요청</button></form></details>']
        out+=['</section>']
    elif tab=='lineage':out+=['<p>객체 탐색에서 대상을 선택하면 원본·선행 조건·검사·이벤트를 조회합니다.</p>']
    if tab=='documents':
        groups=view['collections'];docs=view['documents']
        def children(parent):
            body=''
            for key,g in groups.items():
                if g['parent']==parent:body+='<details><summary>'+esc(g['title'])+'</summary>'+children(key)+'</details>'
            for d in docs.values():
                if d['parent']==parent:body+='<div class="item"><a href="'+esc(source_route)+'?'+urlencode({'id':d['id']})+'">'+esc(d['title'])+'</a><small>'+esc(d['path'])+' · '+('원본 재확인' if d['stale'] else '수집 지문 일치')+'</small></div>'
            return body
        out+=[children(None)]
    out+=['<footer><p>객체별 판단 기록·API·CLI는 같은 권한·revision·근거 검사를 거칩니다. 배포는 별도 승인된 어댑터 계약입니다.</p></footer></main></body></html>']
    return ''.join(out)


def audit(raw,view,tab='overview',page=0):
    """Independent semantic check of rendered members, not a magic profile marker."""
    class Reader(HTMLParser):
        def __init__(self):super().__init__();self.members=[];self.groups=[];self.stack=[];self.bad=False
        def handle_starttag(self,tag,attrs):
            a=dict(attrs);self.bad|=len(a)!=len(attrs)
            if 'data-workflow' in a:self.groups.append(a['data-workflow'])
            parent=next((v for _,v in reversed(self.stack) if v is not None),None)
            if 'data-object' in a:self.members.append((a['data-object'],a.get('data-verification'),parent))
            if tag not in {'meta','link','br','hr','input','img','source','wbr','area','base','col','embed','param','track'}:self.stack.append((tag,a.get('data-workflow')))
        def handle_endtag(self,tag):
            if any(t==tag for t,_ in self.stack):
                while self.stack:
                    t,_=self.stack.pop()
                    if t==tag:break
    reader=Reader();reader.feed(raw)
    matches=[k for k in view['matches'] if tab!='decisions' or view['states'][k]['workflow'] in {'needs_decision','blocked','review_pending'}]
    expected={k for state in LABELS for k in [k for k in matches if view['states'][k]['workflow']==state][page*6:(page+1)*6]}
    if reader.bad or len(reader.groups)!=len(set(reader.groups)) or set(reader.groups)!={view['states'][k]['workflow'] for k in expected}:raise ValueError('Rendered state group inventory differs')
    if {k for k,_,_ in reader.members}!=expected:raise ValueError('Rendered object inventory differs')
    if len(reader.members)!=len({k for k,_,_ in reader.members}):raise ValueError('Duplicate rendered object')
    for key,verification,workflow in reader.members:
        if key not in expected or verification!=view['states'][key]['verification'] or workflow!=view['states'][key]['workflow']:raise ValueError('Rendered state differs from DOP projection')
    return {'state':'structure_passed','members':len(reader.members),'human_acceptance':'pending'}

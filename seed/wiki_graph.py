"""Offline, read-only relation projection. Caller supplies already-authorized nodes and reduced states."""
from html import escape
import re

PROFILE = 'object-node-map-1'
TYPES = {'requirement':'요구', 'task':'작업', 'decision':'결정', 'module':'모듈',
         'test':'검사', 'release':'릴리스', 'execution':'실행', 'evidence':'근거',
         'execution_report':'보고서', 'planned_task':'계획'}
STATES = {'passed':('검사 통과','ok'), 'failed':('검사 실패','bad'), 'stale':('오래된 검사','warn'),
          'blocked':('진행 차단','bad'), 'conflicted':('충돌','bad'), 'running':('검사 중','warn'),
          'unknown':('미확인','unknown'), 'unverified':('미검증','unknown')}
BASES = {'confirmed_by_code':'코드 확인', 'confirmed_by_test':'테스트 확인',
         'confirmed_by_runtime':'실행 확인', 'confirmed_by_user':'사용자 확인',
         'inferred_by_static_analysis':'정적 추론', 'inferred_by_llm':'AI 추론', 'unknown':'근거 미확인'}
EDGES = {'supported_by':'근거', 'verification_scope':'검사 범위', 'implemented_by':'구현',
         'produces':'생성', 'documents':'실행 기록', 'describes':'관련 모듈', 'prerequisite':'선행 조건', 'planned_realization':'관련 요구',
         'verified_by':'검증', 'depends_on':'의존', 'satisfies':'충족 대상',
         'realized_by':'구현 대상', 'governed_by':'결정', 'contains':'포함'}
CSS = '''.node-map{padding:20px;border:1px solid #d5dfdc;border-radius:12px;background:#f9fbfa;margin:20px 0}.node-map h2{margin:0;font-size:19px}.node-map p{font-size:13px;color:#536b62}.node-map .map-scroll{overflow:auto;border:1px solid #e1e8e3;background:#fff;border-radius:10px}.node-map svg{display:block;width:100%;min-width:720px}.node-map .map-node rect{fill:#fff;stroke:#b7cbc0;stroke-width:1.3}.node-map .map-node.focus rect{fill:#edf5ef;stroke:#376852;stroke-width:2}.node-map .map-node:hover rect,.node-map .map-node:focus rect{stroke:#154a36;stroke-width:3}.node-map text{font:13px system-ui;fill:#243d32}.node-map .node-title{font-size:15px;font-weight:650}.node-map .node-meta{font-size:10px;fill:#5b7065}.node-map .ok{fill:#23734e}.node-map .bad{fill:#a02d3d}.node-map .warn{fill:#8b6015}.node-map .unknown{fill:#67716a}.node-map .edge{fill:none;stroke:#638477;stroke-width:1.5}.node-map .inferred{stroke-dasharray:5 4}.node-map .edge-label{font-size:10px;fill:#496657;paint-order:stroke;stroke:#fff;stroke-width:4px}.node-map .map-heading{font-size:12px;fill:#5e746a}.node-map .legend{display:flex;flex-wrap:wrap;gap:14px;font-size:12px;color:#546c60}.node-map details{margin:12px 0 0}.node-map .relation-list{display:grid;gap:8px;list-style:none;padding:0;max-height:340px;overflow:auto}.node-map .relation-list li{padding:10px;border:1px solid #e0e7e2;border-radius:6px;margin:0}.node-map .relation-list a{font-weight:600}.node-map a:focus{outline:2px solid #286b50}.object-cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:10px}.object-cards>a{display:block;border:1px solid #d5dfdc;border-radius:8px;background:#fff;padding:14px;color:#254e3c}.object-cards strong,.object-cards small{display:block}.object-cards small{font-size:11px;color:#687b70;overflow-wrap:anywhere}@media print{.node-map svg{min-width:0}.node-map .map-scroll{overflow:visible}}'''


def safe_id(ident):
    if not isinstance(ident,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,127}',ident):
        raise ValueError('Graph requires canonical local object IDs')
    return ident


def title(obj):
    return str(obj.get('title',obj.get('name',obj['id'])))


def short(value,limit):
    value=' '.join(str(value).split())
    return value if len(value)<=limit else value[:limit-1]+'…'


def render(objects, relations, focus, states=None, limit=4):
    """Only edges between supplied visible objects; never infer edges/status or expose hidden IDs.

    states is a separate reducer result, never read from authored object properties.
    Bounded one-hop map plus complete textual edges makes cycles/high degree safe.
    """
    if type(limit) is not int or not 1<=limit<=8:raise ValueError('Bounded graph page required')
    nodes={safe_id(k):v for k,v in objects.items()}
    if focus not in nodes:raise ValueError('Visible focus required')
    states=states or {};esc=escape
    edges=sorted((e for e in relations if e['from'] in nodes and e['to'] in nodes and focus in (e['from'],e['to'])),key=lambda e:(e['from'],e['to'],e['type'],e.get('basis','unknown')))
    incoming=sorted({e['from'] for e in edges if e['to']==focus and e['from']!=focus})
    outgoing=sorted({e['to'] for e in edges if e['from']==focus and e['to']!=focus})
    left,right=incoming[:limit],outgoing[:limit];count=max(len(left),len(right),1)
    height=max(260,count*136+70);center=height/2-52
    focus_x=368 if left else 12;right_x=focus_x+356
    width=right_x+276 if right else focus_x+276
    coords={('focus',focus):(focus_x,center)}
    for side,items,x in [('left',left,12),('right',right,right_x)]:
        for i,ident in enumerate(items):coords[(side,ident)]=(x,54+i*136)
    marker='arrow-'+focus
    parts=['<section class="node-map" data-graph-profile="'+PROFILE+'" data-focus="'+esc(focus)+'"><style>'+CSS+'</style><h2>객체 연결 지도</h2><p>가운데 객체를 기준으로 화살표를 따라가세요. 노드를 누르면 해당 객체의 목적·행동·근거로 이동합니다.</p>',
           '<div class="legend"><span>→ 기록된 관계 방향</span><span>실선: 근거 확인 관계</span><span>점선: 추론·미확인 관계</span><span>노드 배지: 검사 상태 · 인간 수락과 별개</span></div>',
           '<div class="map-scroll" role="region" tabindex="0" aria-label="객체 관계 지도 · 좁은 화면에서 가로 스크롤"><svg xmlns="http://www.w3.org/2000/svg" style="min-width:'+str(min(width,720))+'px" viewBox="0 0 '+str(width)+' '+str(height)+'" aria-label="'+esc(title(nodes[focus]))+'의 들어오는 관계와 나가는 관계">',
           '<defs><marker id="'+marker+'" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8" fill="#638477"/></marker></defs>',
           ('<text x="12" y="28" class="map-heading">들어오는 관계</text>' if left else '')+'<text x="'+str(focus_x)+'" y="28" class="map-heading">선택한 객체</text>'+('<text x="'+str(right_x)+'" y="28" class="map-heading">나가는 관계</text>' if right else '')]
    for side,items in [('left',left),('right',right)]:
        for ident in items:
            a,b=(ident,focus) if side=='left' else (focus,ident)
            pair=[e for e in edges if e['from']==a and e['to']==b]
            x,y=coords[(side,ident)];cy=center+52;ny=y+52
            x1,y1,x2,y2=(x+264,ny,focus_x,cy) if side=='left' else (focus_x+264,cy,x,ny)
            dashed=any(not e.get('basis','unknown').startswith('confirmed_by_') for e in pair)
            label=EDGES.get(pair[0]['type'],pair[0]['type'])+((' +'+str(len(pair)-1)) if len(pair)>1 else '')
            detail='; '.join(e['type']+' / '+BASES.get(e.get('basis','unknown'),'미확인') for e in pair)
            parts+=['<path class="edge'+(' inferred' if dashed else '')+'" data-from="'+a+'" data-to="'+b+'" d="M'+str(x1)+','+str(y1)+' C'+str((x1+x2)/2)+','+str(y1)+' '+str((x1+x2)/2)+','+str(y2)+' '+str(x2)+','+str(y2)+'" marker-end="url(#'+marker+')"><title>'+esc(detail)+'</title></path>',
                    '<text class="edge-label" text-anchor="middle" x="'+str((x1+x2)/2)+'" y="'+str((y1+y2)/2-10)+'">'+esc(short(label,10))+'</text>']
    for (side,ident),(x,y) in coords.items():
        obj=nodes[ident];state=states.get(ident,'unverified');label,color=STATES.get(state,('미확인','unknown'));name=title(obj)
        parts+=['<a class="map-node'+(' focus' if side=='focus' else '')+'" href="'+ident+'.html" aria-label="'+esc(name+' · '+label)+'"><title>'+esc(name+' / '+ident+' / '+label)+'</title><rect x="'+str(x)+'" y="'+str(y)+'" width="264" height="108" rx="10"/>',
                '<text class="node-meta" x="'+str(x+14)+'" y="'+str(y+19)+'">'+esc(TYPES.get(obj.get('type'),obj.get('type','객체')))+' · '+esc(short(ident,28))+'</text>',
                '<text class="node-title" x="'+str(x+14)+'" y="'+str(y+44)+'">'+esc(short(name,19))+'</text>',
                '<text class="node-meta" x="'+str(x+14)+'" y="'+str(y+65)+'">'+esc(short(obj.get('purpose','목적·근거 문서 열기'),29))+'</text>',
                '<text class="'+color+'" x="'+str(x+14)+'" y="'+str(y+91)+'">● '+esc(label)+'</text></a>']
    parts+=['</svg></div>']
    omitted=len(incoming)+len(outgoing)-len(left)-len(right);self_count=sum(e['from']==e['to'] for e in edges)
    if not edges:parts+=['<p>연결 기록 없음 · 독립 객체인지 관계 누락인지 아직 확인되지 않았습니다.</p>']
    if omitted:parts+=['<p>복잡도를 줄이기 위해 '+str(omitted)+'개 이웃은 아래 전체 관계 목록에 표시합니다. 숨겨진 연결을 없는 것으로 판정하지 않습니다.</p>']
    if self_count:parts+=['<p>자기 연결 '+str(self_count)+'건 · 아래 목록에서 방향과 근거를 확인하세요.</p>']
    parts+=['<details><summary>전체 연결 '+str(len(edges))+'건 · 방향·관계·근거 보기</summary><ul class="relation-list">']
    for e in edges:
        a,b=e['from'],e['to']
        parts+=['<li><a href="'+a+'.html">'+esc(title(nodes[a]))+'</a> → <a href="'+b+'.html">'+esc(title(nodes[b]))+'</a><br>'+esc(e['type'])+' · '+esc(BASES.get(e.get('basis','unknown'),'근거 미확인'))+'</li>']
    return ''.join(parts+['</ul></details><p>지도는 관계 레코드의 표현입니다. 화살표는 완료·승인·실행 권한을 뜻하지 않습니다. 상세 문서에서 출처와 판정 규칙을 확인하세요.</p></section>'])

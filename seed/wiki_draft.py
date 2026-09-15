"""Deterministic local object-wiki draft; no accounts, discovery or execution authority."""
from __future__ import annotations

import argparse
import hashlib
import html
import json
from pathlib import Path
import re
import stat

PROFILE = 'newgame-object-draft-1'
TOPICS = {'start': '처음 사용하기', 'product': '제품과 요구', 'design': '설계와 관계',
          'modules': '모듈과 도구', 'workflows': '작업과 다음 행동', 'quality': '검증과 근거',
          'decisions': '오너 결정', 'history': '변경과 릴리스', 'workspaces': '권한 인터뷰'}
TYPES = {'requirement': ('요구사항', 'product'), 'task': ('작업', 'workflows'),
         'decision': ('결정', 'decisions'), 'module': ('모듈', 'modules'),
         'test': ('검사', 'quality'), 'release': ('릴리스', 'history')}
SOURCE = 'docs/wiki/draft-input.json'
OUTPUT = '.local/wiki-draft'


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode('utf-8')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def need(condition, message):
    if not condition:
        raise ValueError(message)


def text(value):
    need(type(value) is str and 0 < len(value.strip()) <= 4000, 'Bounded text required')


def safe_path(value):
    text(value)
    need(not value.startswith('/') and '\\' not in value and ':' not in value
         and all(p and p not in {'.', '..'} and p == p.rstrip(' .') for p in value.split('/')),
         'Only project-relative source references are supported')


def validate(data):
    need(type(data) is dict and set(data) == {'schema_version', 'profile', 'project_name', 'purpose', 'objects', 'relations'}, 'Draft input fields differ')
    need(type(data['schema_version']) is int and data['schema_version'] == 1 and data['profile'] == PROFILE, 'Unsupported draft version')
    text(data['project_name']); text(data['purpose'])
    need(type(data['objects']) is list and 6 <= len(data['objects']) <= 500, 'Six object types required')
    objects = {}
    for obj in data['objects']:
        need(type(obj) is dict and set(obj) == {'id', 'type', 'title', 'purpose', 'actions', 'source_refs', 'unknowns'}, 'Object contract differs; authored status is forbidden')
        ident = obj['id']
        need(type(ident) is str and re.fullmatch(r'[A-Z][A-Z0-9_-]{1,95}', ident) and ident not in objects, 'Duplicate or unsafe object ID')
        need(obj['type'] in TYPES, 'Unsupported object type')
        for key in ('title', 'purpose'): text(obj[key])
        for key in ('actions', 'unknowns'):
            need(type(obj[key]) is list and 0 < len(obj[key]) <= 30, 'Action/unknown list required')
            for item in obj[key]: text(item)
        need(type(obj['source_refs']) is list and len(obj['source_refs']) <= 30, 'Bounded source references required')
        for item in obj['source_refs']: safe_path(item)
        objects[ident] = obj
    need({o['type'] for o in objects.values()} == set(TYPES), 'Six object types required')
    need(type(data['relations']) is list and len(data['relations']) <= 2000, 'Bounded relations required')
    seen = set()
    for relation in data['relations']:
        need(type(relation) is dict and set(relation) == {'from', 'to', 'type', 'basis'}, 'Relation contract differs')
        need(relation['from'] in objects and relation['to'] in objects, 'Dangling relation')
        text(relation['type'])
        need(relation['basis'] in {'unknown', 'inferred_by_static_analysis'}, 'Draft cannot certify relation evidence')
        key = (relation['from'], relation['to'], relation['type'])
        need(key not in seen, 'Duplicate relation'); seen.add(key)
    return objects


CSS = '''*{box-sizing:border-box}body{margin:0;background:#f4f6f3;color:#243b32;font:16px/1.8 system-ui}main{max-width:1100px;margin:auto;padding:32px}a{color:#285e45}nav{display:flex;flex-wrap:wrap;gap:16px}section,article{background:white;border:1px solid #d8e0d6;border-radius:8px;padding:24px;margin:20px 0}.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px}.cards a{padding:18px;border:1px solid #d8e0d6;background:white}.notice{background:#fff5d9}pre{white-space:pre-wrap;overflow-wrap:anywhere}h1{line-height:1.35}li{margin:8px 0}@media(max-width:600px){main{padding:16px}section,article{padding:16px}}'''


def bundle(data, renderer_digest=None):
    """Pure projection. References are displayed, never opened or treated as evidence."""
    objects = validate(data); esc = html.escape
    def listing(values): return '<ul>' + ''.join('<li>' + esc(v) + '</li>' for v in values) + '</ul>'
    def link(ident, title): return '<a href="' + ident + '.html">' + esc(title) + '</a>'
    def cards(items): return '<div class="cards">' + ''.join(link(i, t) for i, t in items) + '</div>'
    pages = {}; claims = {}; input_digest = sha(encoded(data))
    names = {'index': data['project_name'] + ' · 종합 문서', **TOPICS, 'objects': '객체 탐색', 'sources': '근거 조회', **{k: v['title'] for k, v in objects.items()}}
    parents = {**{k: 'index' for k in TOPICS}, 'objects': 'index', 'sources': 'index', **{k: TYPES[v['type']][1] for k, v in objects.items()}}
    for ident, title in names.items():
        parent = parents.get(ident)
        breadcrumb = link('index', '종합 문서')
        if parent and parent != 'index': breadcrumb += ' → ' + link(parent, names[parent])
        if ident != 'index': breadcrumb += ' → ' + esc(title)
        body = '<nav>' + breadcrumb + '</nav>'
        if ident == 'index':
            body += '<section><h2>프로젝트 목적</h2><p>' + esc(data['purpose']) + '</p><p>큰 문서 → 주제 → 작은 객체 문서 순서로 읽고, 관계·행동·근거를 따라갑니다.</p></section>'
            body += cards([('objects', '객체 탐색'), ('workflows', '다음 작업'), ('workspaces', '권한 인터뷰'), ('sources', '근거 조회')]) + '<section><h2>주제에서 시작</h2>' + cards(TOPICS.items()) + '</section>'
        elif ident == 'objects':
            for kind, (label, _) in TYPES.items():
                body += '<section><h2>' + label + '</h2>' + cards((k, o['title']) for k, o in objects.items() if o['type'] == kind) + '</section>'
        elif ident == 'sources':
            body += '<section><h2>근거에서 객체로</h2><p>아래 참조는 작성자가 선언한 경로입니다. 이 초안은 파일 내용·실행·검증 결과를 수집하지 않습니다.</p>'
            for k, obj in objects.items():
                body += '<h3>' + link(k, obj['title']) + '</h3>' + listing(obj['source_refs'] or ['연결된 근거 없음 · unverified'])
            body += '</section>'
        elif ident in TOPICS:
            children = [(k, obj['title']) for k, obj in objects.items() if parents[k] == ident]
            actions = {'start': ['프로젝트 목적을 오너와 확인하고 객체 탐색에서 필요한 항목부터 구체화합니다.'],
                       'design': ['객체 문서의 관계를 확인하고 실제 코드/근거와 연결한 뒤 검토합니다.'],
                       'workspaces': ['오너에게 역할·문서 범위·열람/수정/승인/실행 권한·로그인/노출 방식을 인터뷰합니다.', '현재 역할과 계정은 없으며 이 로컬 초안은 접근 권한을 부여하지 않습니다.']}
            body += '<section><h2>목적과 다음 행동</h2>' + listing(actions.get(ident, ['하위 객체의 목적·관계·행동·미확인 항목을 실제 프로젝트 자료로 채웁니다.'])) + cards(children) + '</section>' + link('objects', '전체 객체 탐색')
        else:
            obj = objects[ident]
            body += '<article><p>' + esc(TYPES[obj['type']][0]) + ' · ' + esc(ident) + '</p><h2>목적</h2><p>' + esc(obj['purpose']) + '</p><h2>다음 행동</h2>' + listing(obj['actions']) + '<p>행동은 안내입니다. 실행·편집·승인 기능이 아닙니다.</p></article>'
            body += '<section><h2>관계 · 연결 이유</h2>'
            for rel in data['relations']:
                if ident in (rel['from'], rel['to']):
                    other = rel['to'] if rel['from'] == ident else rel['from']
                    direction = '나 → 대상' if rel['from'] == ident else '원본 → 나'
                    body += '<p>' + esc(direction + ' · ' + rel['type'] + ' · ' + rel['basis']) + ' : ' + link(other, names[other]) + '</p>'
            body += '</section><section><h2>근거 조회</h2>' + listing(obj['source_refs'] or ['근거 미연결']) + '<h2>미확인 사항</h2>' + listing(obj['unknowns']) + '</section>' + link('objects', '객체 탐색으로 돌아가기')
        claim = {'view': ident, 'rule': PROFILE, 'input_sha256': input_digest, 'verification': 'unverified', 'acceptance': 'human_pending', 'access': 'interview_pending', 'source_refs': objects.get(ident, {}).get('source_refs', []), 'limits': 'Authored draft only; no Run/Evidence reducer, authentication or source-content verification'}
        claims[ident] = claim
        body += '<details><summary>이 View의 생성 근거와 규칙</summary><pre>' + esc(json.dumps(claim, ensure_ascii=False, indent=2)) + '</pre></details>'
        pages[ident + '.html'] = ('<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src &#39;none&#39;; style-src &#39;unsafe-inline&#39;; base-uri &#39;none&#39;; form-action &#39;none&#39;"><title>' + esc(title) + '</title><style>' + CSS + '</style></head><body><main><h1>' + esc(title) + '</h1><section class="notice">자동 생성 초안 · 검증 미확인 · 권한 인터뷰 대기. 로컬 파일로만 확인하며 웹에 공개하지 않습니다.</section>' + body + '</main></body></html>').encode('utf-8')
    manifest = {'profile': PROFILE, 'state': 'draft_generated', 'bootstrap_ready': False, 'input_sha256': input_digest, 'renderer_sha256': renderer_digest or sha(Path(__file__).read_bytes()), 'output_sha256': {k: sha(v) for k, v in pages.items()}, 'claims': claims}
    return {**pages, 'manifest.json': encoded(manifest)}


def no_links(path):
    for p in (path, *path.parents):
        try: info = p.lstat()
        except FileNotFoundError: continue
        need(not stat.S_ISLNK(info.st_mode) and not getattr(info, 'st_file_attributes', 0) & 0x400, 'Symlink/reparse path rejected')


def write_bundle(out, files, check=False):
    out = Path(out).absolute(); no_links(out)
    if out.exists():
        entries = list(out.rglob('*'))
        for p in entries: no_links(p)
        actual = {p.relative_to(out).as_posix() for p in entries if p.is_file()}
        need(actual == set(files) and all((out / n).read_bytes() == raw for n, raw in files.items()), 'Draft drift or partial output; preserve and choose a new --out directory')
        return 'unchanged'
    need(not check, 'Draft output missing')
    out.mkdir(parents=True, exist_ok=False)
    for name, raw in files.items():
        with (out / name).open('xb') as stream: stream.write(raw)
    return 'written'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['build', 'check'])
    parser.add_argument('--input', type=Path, default=Path(SOURCE))
    parser.add_argument('--out', type=Path, default=Path(OUTPUT))
    args = parser.parse_args()
    try:
        no_links(args.input.absolute()); raw = args.input.read_bytes()
        need(len(raw) <= 2_000_000, 'Draft input too large')
        def pairs(items):
            d = {}
            for k, v in items: need(k not in d, 'Duplicate JSON key'); d[k] = v
            return d
        files = bundle(json.loads(raw, object_pairs_hook=pairs))
        result = write_bundle(args.out, files, check=args.command == 'check')
        print(json.dumps({'state': 'draft_generated', 'outcome': result, 'entrypoint': str(args.out / 'index.html'), 'bootstrap_ready': False})); return 0
    except (ValueError, TypeError, KeyError, OSError) as exc:
        print(json.dumps({'state': 'blocked', 'message': str(exc)})); return 2


if __name__ == '__main__':
    raise SystemExit(main())

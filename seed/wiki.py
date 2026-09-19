"""Object-first, state-grouped offline wiki. Events and reports stay under objects."""
import html
import json
import os
from pathlib import Path
import tempfile

from core import ContractError, Kernel, OBJECT_TYPES, digest, encode, file_hash, local, no_links, require

LABELS = {"Requirement": "요구사항", "Task": "작업", "Decision": "결정", "Module": "모듈", "Test": "검증", "Release": "운용 버전"}
STATES = {"unverified": "미검증", "passed": "검사 통과", "failed": "실패", "stale": "근거 만료", "unknown": "결과 불명", "active": "운용 중", "pinned_history": "보존 버전", "interrupted": "중단"}
CSS = """body{margin:0;background:#f3f5f9;color:#202a3a;font:16px/1.65 system-ui,sans-serif}*{box-sizing:border-box}a{color:#254fb0}header{background:#182941;color:white;padding:28px max(5vw,20px)}header a{color:#bed4ff}nav{display:flex;gap:18px;flex-wrap:wrap}main{max-width:1240px;margin:auto;padding:28px 20px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:16px}.card,section{background:white;border:1px solid #dbe1eb;border-radius:12px;padding:20px;margin-bottom:20px}.node{border-left:5px solid #6589bb}.badge{display:inline-block;border-radius:6px;background:#edf2f9;padding:2px 9px;font-size:13px}h1{font-size:30px}h2{font-size:22px}h3{margin:5px 0}pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:13px}p,li{overflow-wrap:anywhere}.muted{color:#607086}.edges{display:flex;flex-wrap:wrap;gap:10px}.edge{padding:8px;background:#f1f5fb;border-radius:8px}details{margin-top:15px}button,input{font:inherit;padding:8px}input{width:min(480px,100%)}@media(max-width:600px){h1{font-size:24px}main{padding:18px 12px}.grid{grid-template-columns:1fr}}"""


def esc(value):
    return html.escape(str(value), quote=True)


def page(title, body):
    return ("<!doctype html><html lang='ko'><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
            "<meta http-equiv='Content-Security-Policy' content=\"default-src 'none'; style-src 'unsafe-inline'; script-src 'none'; img-src 'none'\">"
            f"<title>{esc(title)}</title><style>{CSS}</style><header><h1>{esc(title)}</h1><nav><a href='index.html'>프로젝트 대문</a><a href='objects.html'>객체 탐색</a><a href='evolution.html'>특화·판정</a></nav></header><main>{body}</main></html>")


def link(obj):
    return f"<a href='{esc(obj['id'])}.html'>{esc(obj['title'])}</a>"


def render(kernel):
    lock = kernel.root / ".wiki-render.lock"
    no_links(lock)
    kernel.root.mkdir(parents=True, exist_ok=True)
    try:
        with lock.open("x", encoding="utf-8") as out:
            out.write(encode({"pid": os.getpid(), "recovery": "confirm renderer stopped before moving this marker"}))
    except FileExistsError as exc:
        raise ContractError("wiki render in progress/unknown; inspect .wiki-render.lock") from exc
    try:
        return _render(kernel)
    finally:
        lock.unlink()


def _render(kernel):
    root = kernel.root
    no_links(root / "wiki")
    if kernel.path.exists():
        view = kernel.view()
        state, records = kernel.inspect()
        require(view["event_head"] == records[-1]["hash"], "ledger changed during render; retry wiki command")
        objects = view["objects"]
    else:
        view = {"active": "V2 · 연결 전", "readiness": {"ready": False, "reasons": ["오너 인터뷰와 프로젝트 원본·검사 연결 필요"]}, "dop_counts": {}, "event_head": None}
        state, records, objects = {}, [], []
    by_id = {o["id"]: o for o in objects}
    draft = "".join(f"<article class='card node'><h3>{label}</h3><span class='badge'>연결 대기</span><p>원본·목적·관계를 등록하면 실제 객체가 표시됩니다.</p></article>" for kind, label in LABELS.items() if not any(o["type"] == kind for o in objects))
    def card(o):
        return f"<article class='card node'><span class='badge'>{LABELS[o['type']]} · {STATES.get(o['state'],esc(o['state']))}</span><h3>{link(o)}</h3><p>{esc(o['purpose'])}</p><small>관계 {len(o['relations'])}개 · 근거는 상세에서 확인</small></article>"
    grouped = ""
    for status in STATES:
        rows = [o for o in objects if o["state"] == status]
        if rows:
            grouped += f"<h2>{STATES[status]} <small>{len(rows)}</small></h2><div class='grid'>" + "".join(map(card, rows)) + "</div>"
    stage = "V3 고정 유지" if view["active"].startswith("V3-") else "V2 유지"
    ready = "탐색 조건 충족 · 채택은 별도" if view["readiness"]["ready"] else stage + " · 다음 탐색 준비 조건 확인"
    home = f"<section><h2>{esc(view['active'])}</h2><p>{ready}</p><p>큰 문서 → 주제 → 객체 상세. 객체는 한 번만 등록하고 상태별로 모아 봅니다. 실행·관측·평가는 근거 데이터로 연결됩니다.</p></section>"
    home += "<div class='grid'>" + "".join(f"<section><h3><a href='{kind}.html'>{label}</a></h3><p>{sum(o['type']==kind for o in objects)}개 객체</p></section>" for kind, label in LABELS.items()) + "</div>"
    home += "<h2>현재 상태 지도</h2>" + grouped + "<div class='grid'>" + draft + "</div>"
    files = {"index.html": page("프로젝트 운영 위키", home), "objects.html": page("객체 탐색 · 상태 지도", grouped + "<div class='grid'>" + draft + "</div>")}
    for kind, label in LABELS.items():
        rows = [o for o in objects if o["type"] == kind]
        files[kind + ".html"] = page(label, "<div class='grid'>" + "".join(map(card, rows)) + "</div>" + ("<p>아직 원본과 연결되지 않았습니다.</p>" if not rows else ""))
    for obj in objects:
        relations = "".join(f"<div class='edge'>{esc(obj['title'])} → {link(by_id[t])}</div>" for t in obj["relations"] if t in by_id)
        reverse = "".join(f"<div class='edge'>{link(o)} → {esc(obj['title'])}</div>" for o in objects if obj["id"] in o["relations"])
        body = f"<section><span class='badge'>{LABELS[obj['type']]} · {STATES.get(obj['state'],esc(obj['state']))}</span><h2>목적</h2><p>{esc(obj['purpose'])}</p><h2>연결 상태</h2><div class='edges'>{relations}{reverse}</div></section>"
        body += "<section><h2>가능한 행동</h2><p>상위 주제와 연결 객체를 탐색하고 판정 근거를 확인합니다. 실행·승인은 로컬 CLI의 오너 권한과 작업 범위에 따릅니다.</p><h2>원본</h2><ul>" + "".join(f"<li>{esc(p)}</li>" for p in obj["sources"]) + "</ul></section>"
        related = [e for e in records if obj["id"] in {e["data"].get("task"), e["data"].get("id")}]
        if obj["type"] == "Release":
            related += [e for e in records if e["kind"] in {"Initialized", "ConfigAdopted", "ConfigRolledBack"} and e["data"].get("config_id") == obj["lineage"]["config"]]
        lineage = obj['lineage']
        reason = f"최근 검사 {esc(lineage['run'])}에서 생성된 상태입니다." if lineage['run'] else "연결된 검사 결과로 완료를 입증하지 않았습니다. 운용 버전의 활성 여부는 채택 기록에서 계산합니다."
        body += f"<section><h2>이 상태가 생성된 이유</h2><p>{reason}</p><p>인간 수락: {esc(obj['human_acceptance'])}</p><details><summary>판정 규칙·입력 버전 확인</summary><pre>{esc(json.dumps(lineage,ensure_ascii=False,indent=2))}</pre></details><details><summary>실행·이벤트 근거 {len(related)}건</summary><pre>{esc(json.dumps(related,ensure_ascii=False,indent=2))}</pre></details></section>"
        files[obj["id"] + ".html"] = page(obj["title"], body)
    body = f"<section><h2>{ready}</h2><ul>" + "".join(f"<li>{esc(x)}</li>" for x in view["readiness"]["reasons"]) + "</ul><p>V2 → 기본 실행·관측 → 준비 판정 → 격리 후보 → 비교 평가 → 오너 채택 → 고정 V3</p></section>"
    body += "<section><h2>후보와 평가</h2><p>후보는 활성 규칙과 분리됩니다. 명령 해석·권한 회귀만 평가했으며 실제 LLM 품질은 미검증입니다.</p>"
    for cid, candidate in state.get("candidates", {}).items():
        ev = state.get("evals", {}).get(cid)
        verdict = "비교 평가 통과 · 채택은 별도" if ev and ev['passed'] else "개선 근거 부족" if ev else "평가 대기"
        adopted = [e['data']['config_id'] for e in records if e['kind'] == 'ConfigAdopted' and e['data']['candidate'] == cid]
        if adopted:
            verdict = "채택 완료 · V3 운용 중" if state['active'] in adopted else "채택 이력 보존 · 현재 다른 구성 운용"
        body += f"<article><h3>{esc(candidate['hypothesis'])}</h3><p><span class='badge'>{verdict}</span> · {esc(cid)}</p><details><summary>후보·비교 근거 펼치기</summary><pre>{esc(json.dumps({'candidate':candidate,'evaluation':ev},ensure_ascii=False,indent=2))}</pre></details></article>"
    body += "</section>"
    files["evolution.html"] = page("특화 · 판정 근거", body)
    files["projection.json"] = json.dumps(view, ensure_ascii=False, indent=2) + "\n"
    target = root / "wiki"
    receipt = target / ".generated.json"
    no_links(receipt)
    old = json.loads(receipt.read_text(encoding="utf-8")) if receipt.exists() else {}
    if target.exists():
        for name, sha in old.items():
            p = local(target, name)
            require(not p.exists() or file_hash(p) == sha, "wiki user edit detected: " + name)
        for name in files:
            require(not (target / name).exists() or name in old, "wiki ownership conflict: " + name)
    target.mkdir(parents=True, exist_ok=True)
    hashes = {}
    for name, content in files.items():
        path = local(target, name)
        data = content.encode("utf-8")
        with tempfile.NamedTemporaryFile(dir=target, delete=False) as temp:
            temp.write(data)
            tmp = temp.name
        os.replace(tmp, path)
        hashes[name] = file_hash(path)
    receipt.write_text(encode(hashes) + "\n", encoding="utf-8")
    return {"wiki": str(target / "index.html"), "objects": len(objects), "state": "derived_projection", "visual_acceptance": "human_pending", "event_head": view["event_head"]}

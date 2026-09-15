# 기본 위키 — 종합 문서에서 작은 문서로

새 프로젝트는 `newgame-style-wiki-1`을 기본 표현 형식으로 사용합니다. Newgame의 탐색 방식을 일반화했으며 프로젝트 이름·기능·역할·검사 이력은 포함하지 않습니다. 금융/게임 도메인의 운영 성공이나 전체 하네스 완성을 보증하는 규칙이 아닙니다.

## 기본으로 보이는 구성

- 종합 대문: 프로젝트 목적, 지금 사용할 범위, 미확인 사항, 사용법/작업/결정 바로가기, 다음 작업.
- 주제 9개: 처음 사용하기, 제품과 기능, 설계와 데이터, 모듈과 도구, 남은 작업, 검증/문제 해결, 결정, 이력, 역할별 시작 경로.
- 작은 작업 문서: 목적, 산출물, 완료 기준, 선행 작업, 오너 판단, 원본/근거 참조, 전체 목록으로 돌아가기.
- 모든 페이지: 상위/하위 탐색, 허용된 역할의 링크, View 생성 규칙과 검증 한계.
- 과거 작업은 개발 이력에 설명하고 남은 작업 목록에는 현재 계획만 둡니다. 원래 요구가 남은 작업/현재 기능/보류 중 어디에 대응하는지 프로젝트에서 대조합니다.

## 첫 설치에서 반드시 수행

```powershell
python wiki_template.py scaffold --out docs/wiki/content.json
```

scaffold는 내용의 구조만 만듭니다. `template_only: true`, 빈 목적·작업·근거는 검사를 통과하지 않습니다. 프로젝트의 실제 요구·코드·근거를 읽고 `content.json`의 9개 주제를 작성한 후 `template_only`를 false로 전환합니다. 이 전환 자체가 검증이나 승인 증거는 아닙니다.

`tasks`에는 id, title, purpose, depends_on, deliverables, acceptance, owner_decision, source_refs를 기록합니다. 선행 작업을 앞에 배치하고 순환/누락을 해소합니다. 검사 가능한 종료 기준과 오너 판단을 구분합니다. 모든 설명은 HTML이 아닌 평문으로 입력합니다. source_refs는 명시적 참조이며 이 생성기는 임의 파일이나 URL을 읽지 않습니다.

역할·접근 모드는 먼저 오너에게 확인합니다. 기존 `wiki_core.py` 계약으로 `tree.json`을 작성합니다. root는 index, 그 아래 9개 주제 ID(start/product/design/modules/workflows/quality/decisions/history/workspaces), 작업 ID는 workflows의 하위입니다. page는 각 ID.html입니다. 임의 역할이나 로그인 정책을 기본 확정하지 않습니다.

```powershell
python wiki_template.py check --content docs/wiki/content.json --tree docs/wiki/tree.json
python wiki_template.py build --content docs/wiki/content.json --tree docs/wiki/tree.json --out .local/wiki-build-001
```

각 명령의 종료 코드가 0인지 확인하고 실패하면 다음 동작을 진행하지 않습니다. 같은 입력/출력으로 재생성하면 no-op입니다. 다른 내용·수동 변경·중단된 출력은 덮어쓰지 않습니다. 새 출력 디렉터리에서 다시 만든 후 검증하여 전환합니다. 원본 문서는 project-owned, renderer는 version-pinned seed component, 출력은 generated-owned입니다.

출력은 역할별 HTML과 로컬 제어용 manifest입니다. **전체 출력 폴더를 웹에 통째로 제공하지 않습니다.** 검증된 HTTP adapter가 허용 역할의 HTML만 제공해야 하며 manifest와 다른 역할의 파일은 차단합니다. bootstrap.py에 output·원본·renderer·tree·adapter·검사 계약을 바인딩하고 역할 경로·6개 객체·관계·근거를 추가해 전체 bootstrap gate를 통과해야 합니다. presentation_checked는 bootstrap_ready가 아닙니다.

## 기존 프로젝트와 확장

기존 위키에는 재설치를 실행하지 않습니다. source/receipt/evidence를 보존하고 별도 작업으로 차이를 검토합니다. 공통 renderer의 `render(content, tree)` 결과를 프로젝트 adapter가 사용하거나, 기존 renderer가 같은 표현 계약을 충족하는지 fixture로 비교합니다. 도메인별 카드·차트·객체는 프로젝트 확장입니다. 기본 대문·주제·작업 상세·근거 경로를 없애는 예외는 오너 결정과 동등 탐색 검사에 연결합니다.

기존 contract-6 bootstrap 바인딩/원장 engine은 변경하지 않았습니다. v0.7.0 신규 bootstrap은 이 표현 검사를 필수 프로젝트 검사로 등록합니다. 미지원 renderer를 옛 바인딩이 자동 인증한다고 주장하지 않습니다.

## 상태와 권한 경계

이 생성기는 사람이 작성한 범위 설명과 계획을 표시합니다. verified/current/released를 직접 저장하거나 추론하지 않습니다. 실제 상태는 프로젝트가 Run/Evidence reducer에서 별도 연결합니다. 출처/규칙/입력 hash는 manifest에서 재현할 수 있으며 hash는 사실성이나 인간 승인 증명이 아닙니다.

오프라인 로그인 생략은 오너가 선택한 단일 loopback 조회 모드에서만 가능합니다. 역할별 렌더링은 HTTP 인증·OS 파일 접근을 강제하지 않습니다. 서버·외부 공개·새 계정·권한 확장은 별도 구현/검증/승인 대상입니다.


## v0.8.0 — 설치 즉시 객체 위키 초안

`seed.py init`이 `.local/wiki-draft/index.html`과 대문/9개 주제/6종 객체/관계/근거 조회를 자동 생성합니다. 배포 ZIP에도 같은 초안이 포함됩니다. 별도 AI 호출·scaffold·키·네트워크가 필요하지 않습니다. 먼저 로컬 파일을 열어 초안을 확인하세요.

편집 원본은 `docs/wiki/draft-input.json`입니다. 실제 프로젝트 목적·객체·원본 참조를 채운 뒤 `python wiki_draft.py build --input docs/wiki/draft-input.json --out .local/wiki-draft-002`로 새 출력에 생성하고 `python wiki_draft.py check --input docs/wiki/draft-input.json --out .local/wiki-draft-002`로 동일성을 확인합니다. 원래 출력/영수증은 보존합니다.

초안은 역할·계정을 만들지 않습니다. unverified/human_pending/interview_pending을 유지하며 참조 파일의 내용도 자동 읽지 않습니다. `.local`은 프로젝트 Git 제외 대상으로 유지하고 초안 폴더를 서버에 통째로 노출하지 않습니다. 실제 프로젝트 원본, 관계, 오너 인터뷰, 권한 adapter, Run/Evidence와 기존 bootstrap gate를 연결해야 합니다. draft_generated는 bootstrap_ready가 아닙니다.

기존 v0.7.0의 wiki_template.py와 계약은 유지됩니다. 완성된 프로젝트 위키를 덮어쓰지 말고 별도 초안에서 구조를 비교·통합하세요. 여섯 객체 초안은 docs/harness/objects.json의 실제 레코드가 아닙니다.

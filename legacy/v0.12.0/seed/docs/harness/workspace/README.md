# Newgame 기능 대응 운영 계층 — operating-workspace-1

## v0.12.0 후보: 자동 객체·관계와 동일 결과 검사

`workspace_sources.py`는 승인된 JSON 레코드 또는 Markdown 표를 명시적 매핑으로 읽어 registry 2를 생성한다. [매핑 예제](mapping.example.json)는 미설정 템플릿이며 실제 원본과 오너 인터뷰를 대체하지 않는다. 매핑 파일도 policy의 승인된 data 디렉터리에 둔다. 원문 객체 ID는 namespace와 hash로 안정적으로 매핑되며 이름 변경·행 재배열로 ID를 바꾸지 않는다. 같은 ID의 중복은 실패한다. 상태 선언은 `contracts.declared_state`에 보존하고 `verified`나 `accepted`로 변환하지 않는다.

```powershell
python -B workspace_sources.py --policy workspace-policy.json --recipe docs/approved/mapping.json --out workspace-objects.json
python -B workspace.py collect --key source-collection-001
```

명령이 실패하면 수집으로 넘어가지 않는다. 생성 파일이 이미 있으면 동일 내용만 no-op이다. 다른 내용은 소유권 충돌로 중단되므로 새 파일에서 diff와 변경된 입력을 검토하고 프로젝트 소유 레지스트리로 적용한다. 다음 수집에는 새로운 operation key를 쓴다. `--check --out ...`은 생성 결과와 현재 파일을 비교하며 CI에서 파일을 덮어쓰지 않는다. 이 수집기는 네트워크를 사용하지 않는다. 외부 snapshot은 실제 관측 시각·범위·권한을 별도로 확인해야 한다.

registry 2는 기존 objects 외에 `contracts`와 `relations`를 가진다. 관계는 `id/from/to/type/basis/sources`를 반드시 기록한다. `documented_by`는 생성 원본으로 자동 연결되며 나머지 의미 관계는 명시적인 근거를 요구한다. `depends_on`은 실행 선행 조건과 일치해야 한다. `supersedes`는 결정끼리만 허용하고 새 결정의 독립 수락 뒤에만 기존 결정을 대체한다. `conflicts_with`는 실행을 막으며 단순한 날짜·역할·원문 완료 표기로 해소하지 않는다.

관계·수락 계약과 그 원본 해시가 판단 snapshot에 포함된다. 변경된 계약은 이전 승인을 자동 승계하지 않는다. 과거 collection은 감사 이력으로 유지한다. 숨겨진 원본·관계는 조회자에게 공개하지 않는다. 역할명이나 contracts.owner는 인증된 principal과 동등하지 않다.

v0.11.0의 활성 원장 엔진 핀을 바꾸지 않는다. 새 디렉터리에 설치해 검토하고, 기존 판단 이관은 별도 migration 계약을 요구한다. 이전 버전은 rollback 대상으로 보존한다.

씨앗을 설치하면 먼저 미확인 객체 위키 초안이 생성된다. 이 문서는 그 초안을 실제 원본·업무 판단·검사·배포 관측과 연결하는 선택 가능한 운영 계층이다. `workspace.py`, `workspace_view.py`, `workspace_server.py`, `delivery.py`는 기존 local-core-1을 교체하지 않는다. 프로젝트마다 오너가 역할·공개 범위·검사·어댑터를 확정한다. 기본 계정, 배포 권한, 외부 연결, 승격 권한은 없다.

## 첫 실행

1. 오너 인터뷰에서 프로젝트 ID, 의도 원본, 열람할 로컬 디렉터리, principal별 역할, read/propose/authorize/start/submit/accept/defer/block/resume/deliver 권한, 수락 종류를 확정한다. 오프라인 읽기 전용 프로젝트는 기존 정적 위키를 유지하고 계정을 만들지 않는다. 업무 판단을 기록하는 HTTP 계층은 authenticated 모드의 principal을 요구한다. 명시적으로 선택한 loopback_read_only 모드는 단일 read 역할·빈 principals·accounts:null만 허용하며 로그인과 모든 업무 변경을 차단한다. 이 경우 account/login 없이 view/server를 사용할 수 있다.
2. 아래 빈 예제를 프로젝트 소유 `workspace-policy.json`, `workspace-objects.json`에 복사하고 확인된 값만 채운다. 빈 예제는 실행되지 않는다. 객체에는 상태 필드를 넣지 않는다. Core Task의 `target_paths`에는 연결 원본과 실제 수락에 필요한 모든 입력을 포함한다.
3. 프로젝트 루트에서 아래 명령을 실행한다. 비밀번호는 숨긴 입력으로 받고 계정은 최초 생성만 한다. 기존 계정의 변경이나 권한 확대는 수행하지 않는다.

```powershell
python -B workspace.py init --config workspace-policy.json
python -B workspace.py collect --key initial-source-collection
python -B workspace.py account --username <인터뷰에서-확정한-계정>
python -B workspace_server.py --port 8766
```

`http://127.0.0.1:8766/login`에서 로그인한다. 작업 개요 → 판단 대기열 → 객체 탐색 → 관계·근거 → 전체 문서를 탐색한다. 전체 문서는 승인된 디렉터리의 중첩 계층을 자동 생성한다. 객체 검색은 ID·목적·제목, 필터는 유형·업무 상태를 사용한다. 한 상태의 한 페이지에 최대 6개 객체를 표시한다. 객체를 선택하면 근거를 펼치고 업무 판단을 요청할 수 있다. 원본 뷰어는 안전한 텍스트 보기이며 MkDocs 전체 Markdown/플러그인 렌더러는 아니다.

CLI의 `login --username`은 session token을 stdout에 한 번 출력한다. 로그에 저장하지 말고 `view`, `act`, `delivery release/reconcile`의 stdin 첫 줄에 전달한다. 비밀번호·session token은 argv, URL, 레코드, Git에 넣지 않는다. HTTP는 쿠키(HttpOnly/SameSite), loopback Host, POST Origin을 확인하며, JSON action은 `X-Workspace-Action: 1`을 요구한다. 폼과 CLI/API는 같은 판정 함수를 사용한다.

## 데이터와 판정

| 원본 | 소유권·판정 |
|---|---|
| workspace-policy.json | 오너가 확정한 프로젝트 정책. 초기 digest와 실행 구성 요소를 고정; 변경 시 차단 |
| workspace-objects.json | 목적·stable ID·수락 종류·원본·선행 관계·Core Task 연결. `status` 금지 |
| 승인된 문서/코드/자료 | Reality. 읽은 실제 바이트의 경로 ID·SHA·종류·허용 역할을 수집 |
| .harness-workspace/ledger.sqlite3 | collection/action 사건과 hash chain; 수정·삭제 금지 |
| .harness 원장 | 고정된 Core의 검사 Run, 입력 snapshot, 최신 검사 결과 |
| delivery.sqlite3 | 시작→단계 응답→종료. 미종료 효과는 pending, 재활성화 금지 |
| HTML / API view | 매 조회 파생. 상태를 파일에서 읽어 사실로 승격하지 않음 |

정책은 정확한 필드만 받으며 schema 1/profile operating-workspace-1을 사용한다. 승인된 roots는 documents(.md), code(.py/.gd/.js/.ts/.mjs/.cjs/.tscn), data(.csv/.json)이다. 숨김 경로·자격증명 이름·reparse 경로를 거부/제외한다. 최대 5,000 파일, 파일당 4 MB, 1,000 객체, 선행 깊이 100 미만이다. 파일 이름 검사만으로 비밀을 판별하지 못하므로 오너는 **공유 가능한 내용만 있는 디렉터리**를 승인해야 한다. 수집은 의미적 요구나 구현 관계를 자동 확정하지 않는다. 같은 제목은 합치지 않고 중복 ID·순환·누락은 거부한다.

업무 흐름은 제안/미결정 → 범위 승인 → 착수 기록 → 검토 요청 → 독립 수락이다. 보류/차단/재개 사건을 별도로 지원한다. `implemented`는 착수 사건에서 만들지 않는다. mixed/machine 수락은 현재 Core Run이 모든 연결 원본과 일치하고 passed일 때만 진행한다. human_verifiable은 독립 인간 판단을 기록할 수 있지만 검사 통과나 배포를 만들지 않는다. 수락 시도 주체가 같은 snapshot의 제안자·착수자·제출자이면 역할 이름에 관계없이 거부한다.

snapshot에는 객체 의도, 실제 원본 hash, Core Task revision/입력 계약, 선행 snapshot이 들어간다. 원본/수락 조건 변경은 이전 승인 효력을 제거한다. 최신 검사 실패·무효화·누락도 반영한다. 검사 passed는 인간 수락과 출시가 아니다. 숨겨진 선행 대상은 이름을 노출하지 않고 generic blocked로 남긴다. URL에 다른 객체/원본 ID를 넣어도 서버가 같은 열람 범위를 적용한다.

action 요청의 정확한 필드: `subject, action, key, expected_revision, snapshot, reason`. 같은 principal·key·요청은 unchanged, 다른 요청은 conflict, 낡은 revision/snapshot은 거부한다. CLI 0은 요청 처리이며 업무 완료가 아니다. 계약/권한/근거/I/O 오류는 exit 2와 blocked, HTTP는 403이다. 읽기는 기록을 만들지 않으며 collection/action은 SQLite transaction으로 기록한다. SQLite 파일 소유자·OS 관리자의 고의 조작을 인증/격리하는 시스템은 아니다.

## 배포 어댑터와 제한된 Canary

`delivery.py init --policy delivery-policy.json`으로 별도 설정한다. 실제 배포 전에 Core 필수 Run의 입력에 artifact 목록, 어댑터 소스 bindings, delivery-policy.json을 반드시 포함한다. 정책은 executable 파일 SHA, shell 없는 argv, timeout, 정확한 파일 목록과 Canary 대상/checks/interval_seconds를 고정한다. 빈 배포 예제는 실행되지 않는다. 실제 외부 자격증명과 비용·공개 권한은 이 정책 파일만으로 허가되지 않는다.

어댑터는 stdin JSON의 `phase, subject, candidate, previous, files, actor, snapshot, target`을 받고 stdout에 정확히 `{"ok":true,"active":"64자리-artifact-inventory-sha"}` 또는 active:null을 반환한다. inspect/health는 읽기 전용, activate는 후보 identity의 원자적 활성화, rollback은 관측된 previous 복원을 담당한다. target은 실제 대상과 일치해야 한다. health는 프로젝트가 승인한 기능/오류율/권한 기준을 판정한다. 쉘 환경의 API 키는 전달하지 않는다. 별도 승인된 credential adapter가 필요하다.

```powershell
# stdin 첫 줄에 로그인 session token을 전달하는 명령이다.
python -B delivery.py release --subject <수락된-객체-ID> --key <안정된-작업키> --expected-active none
python -B delivery.py reconcile --key <결과불명-작업키>
```

inspect에서 기존 active가 예상과 다르면 활성화 없이 aborted. 같은 active artifact를 덮어쓰지 않는다. 성공한 activate 후 2~10회, 간격 1초 이상, 총 대기 60초 이하의 제한된 관찰을 수행한다. 명시적 health 실패면 즉시 rollback→이전 identity health를 확인한다. 성공은 **지정된 Canary 대상의 관측**이며 자동 확대 권한이 아니다. 실제 서비스의 장기 관찰·여러 cohort 확대는 별도 운영 어댑터/승인 사항이다.

프로세스 실패·timeout·출력 초과·응답 불명은 pending을 보존하고 새 release를 차단한다. stdout/stderr 각각 64 KiB, stdin 32 KiB; no-shell/minimal-env/timeout은 OS sandbox가 아니다. reconcile은 같은 operation의 inspect/health만 호출하고 재활성화하지 않는다. 관측된 후보나 이전 identity를 확인하지 못하면 pending이다. reconciliation 결과를 정상 Canary 완료와 구분한다. SQLite operation lock으로 실행 중인 release/reconcile 경쟁을 차단하며 프로세스 종료 시 lock이 풀린다. 외부 시스템 자체의 idempotency/원자성은 어댑터의 필수 계약이다.

## 호환성·복구·최적화

새 파일은 선택적 운영 프로필이며 이전 5개 코어 파일의 pin을 바꾸지 않는다. 기존 프로젝트에 덮어써서 자동 채택하지 않는다. 새 배포는 새 경로에 설치하고 manifest/프로필/정책/검사/접근/원본을 재검증한다. 활성 workspace의 정책·구성 요소가 바뀌면 실행을 막는다. 자동 권한 확대/정책 repin/원장 migration은 제공하지 않는다.

`workspace.py backup --out .local/workspace-audit.json`은 운영 사건과 배포 사건을 잠근 뒤 감사 snapshot을 생성한다. `workspace.py --root <새-검사경로> restore --backup <백업파일>`은 hash chain을 검사하고 **조회용 archive만** 복원한다. 활성 원장, 계정, 세션, 실행 권한을 덮어쓰지 않는다. Core 원장·프로젝트 파일·외부 artifact의 백업/복구는 별도이며 전체 서비스 복원과 혼동하지 않는다.

최적화는 요청 안에서만 source/Task 관측을 재사용한다. 다음 요청에서는 다시 실제 바이트와 Core 상태를 읽는다. `_project(cache_core=False)`는 회귀 비교용 비캐시 기준이다. 동일 fixture에서 모든 projection 필드·권한·실패 상태가 같아야 캐시 변경을 채택한다. 읽기 감소는 벽시계 성능 향상, 규칙 감소, 인간 개입 감소, 도메인 일반성을 자동 증명하지 않는다.

외부 Notion/Sheet/API 수집기는 이 버전에 포함하지 않는다. 어댑터를 추가할 때는 승인 범위, 원본 identity/revision/observed_at, raw digest, 삭제/권한 거부/부분 응답/충돌, retry와 비용 예산을 기록하고 로컬 snapshot으로 전달해야 한다. 신뢰되지 않은 외부 `status`를 업무 사실로 import하지 않는다. CI/hosting/domain 도구 통합은 실제 프로젝트에서 평가하고 feedback 계약을 통해 승격 후보로 제출한다.

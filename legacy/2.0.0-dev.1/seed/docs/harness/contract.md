# CLI / 상태 / 파일 계약 fixed-v2-1

## 실행 인터페이스

Python 3.10+ 표준 라이브러리, 외부 패키지/LLM 키 불필요. `python -B harness.py [--root PROJECT] COMMAND`.
변경 명령은 `--data path.json --actor label --key operation-id`를 받습니다. UTF-8 JSON, 출력은 JSON 한 개. exit 0은 **명령이 기록되었다**는 뜻입니다. `run.state=failed/unknown/stale`, `evaluate.passed=false`도 정상적으로 기록된 실패이며 반드시 결과 필드를 읽어야 합니다. 계약 위반은 exit 2, 변경 롤백. 키는 프로젝트 원장 전체에서 유일하며 같은 키+다른 payload/actor/command는 충돌입니다.

| 명령 | JSON 필드 / 조건 | 원본 이벤트 |
|---|---|---|
| init | schema=2, owner, proposer, evaluator, authority_ref, exposure=offline_local, inputs=[파일], test_adapter={script,args}, candidate_budget=1..10, model_context, eval_cases | Initialized |
| object | id, type=Requirement/Decision/Module/Test, title, purpose, sources=[등록 입력], relations=[기존 객체] | ObjectRegistered |
| task | id, requirement, purpose, authority_ref, acceptance=machine_verifiable/human_verifiable/mixed, depends_on=[기존 Task, 선택] | TaskRegistered, ObjectRegistered |
| run | task | RunStarted → RunFinished |
| observe | id, task, category, summary, evidence_ref, suggestion={허용 overlay, 선택} | ObservationRecorded |
| resume | run | ResumeReadback |
| mvp | run, user_flow, decision_ref; owner만, 현재 pass 필요 | MvpAccepted |
| checkpoint | {} | Checkpoint, 조건부 SpecializationReady/CandidateProposed |
| propose | id, overlay, observations=[관측ID], hypothesis; proposer만 | CandidateProposed |
| evaluate | candidate; evaluator만, 후보당 1회 | CandidateEvaluated |
| adopt | candidate, decision_ref; owner만 | ConfigAdopted |
| rollback | config=기존 config ID, reason; owner만 | ConfigRolledBack |
| reconcile | run, process_stopped=true, reason; owner가 잔류 프로세스 확인 후 | RunReconciled(interrupted만) |

`view`, `audit`는 원장을 수정하지 않습니다. `resolve --task ID --command TEXT`는 해당 작업 한 건 범위의 해석·문맥 순서·출력 형식·체크리스트·모듈 탐색 제안만 반환합니다. 구현/배포를 실행하지 않습니다. 종료된 작업 및 미충족 선행 Task는 next 대상에서 제외합니다. `wiki`는 파생 파일만 생성합니다.

## 판정 규칙

Run: 예약 시 unknown → exit 0이면 passed, 비정상 exit/출력 초과면 failed, 입력 전후 hash 불일치면 stale. 타임아웃은 자식 프로세스/외부 효과까지 확인하지 못했으므로 unknown. 다시 실행하지 않고 상태 확인 후 reconcile합니다. 최신 실제 Run이 이전 pass를 덮어 판정하되 역사 행은 보존합니다. 동일 파일·규칙·이벤트에서 판정은 동일하며 wall clock 기반 자동 만료는 없습니다. 변경된 파일/엔진을 오래된 pass로 인증하지 않습니다.

준비: 실제 입력에 연결된 6가지 객체, 현재 통과 Run, 오너가 수락한 기본 사용자 흐름, 해당 Run의 resume readback, 분류된 관측, 미해결 unknown 없음, 생성 위키 파일 무결성. readback은 재개 데이터 경로를 검사하며 실제 별도 세션 운용 성공까지 증명하지 않습니다. 위키는 설치/명령 후 자동 생성되며 객체 목적·관계·원본·행동·상태 생성 경로를 보여줍니다. 데이터 근거를 OOP 객체로 복제하지 않습니다.

후보: 활성 baseline+epoch+입력 snapshot+관측+고정 eval suite+모델 조건에 귀속됩니다. 허용 필드는 aliases, context_order, output_format(compact/detailed), module_navigation, checklist. 별칭은 status/next_ready로만 연결되며 외부 행동이 없습니다. source/permissions/retention/acceptance/deploy/core 필드와 위험 명령 별칭은 차단합니다. 후보 공간은 이벤트 데이터이며 임의 후보 코드 실행이 없습니다. 자동 탐색은 관측의 명시적 suggestion을 정규화하는 고정 로컬 방식입니다. LLM 호출이나 습관의 임의 추측은 수행하지 않습니다.

eval_cases: id, split=development/selection/holdout, category=intent/authority/regression, command, ready=[Task ID], authorized=[Task ID], expected={action: task/blocked/clarify/status, tasks:[최대1ID]}. selection과 holdout 모두 intent/권한거절/고정 next 회귀 사례가 필요합니다. 고정 명령 oracle은 core가 확인합니다. 전체 안전/회귀 통과, 기존 통과 손실 0, selection·holdout 각각 성공 수 엄격 증가, config 4096bytes 이내여야 통과합니다. 현재 평가는 명령 해석에 국한됩니다. 개발/선택/최종 데이터는 분리 표기하지만 로컬 오너가 파일을 볼 수 있으므로 **평가자에 대한 비밀 holdout은 아닙니다**. 재시험·예산 초기화로 과적합을 숨기지 않습니다.

채택: 현재 입력·baseline·epoch 재확인, 독립 evaluator label의 pass, 오너 결정 필요. config immutable, Task는 시작 config 고정. rollback은 **향후 Task의 config pointer만** 복귀하며 제품 파일/이미 실행한 외부 효과를 되돌리지 않습니다. ABA(active가 바뀌었다 돌아옴)도 epoch 차이로 기존 후보 채택을 거절합니다. 정체·예산 소진·개선 없음은 V2 유지이며 완료 실패를 숨기지 않습니다.

## 소유권·복구·호환성

- 배포 소유: core.py/harness.py/wiki.py, AGENTS와 docs. 설치 receipt/manifest가 byte identity를 고정합니다. 소비 프로젝트에서 core를 수정하지 않습니다.
- 프로젝트 소유: 실제 코드·테스트·setup JSON·인터뷰 근거. init은 입력 목록/테스트 adapter를 원장에 고정합니다. 코드 수정은 가능하며 이전 검사는 stale이 됩니다.
- 실행기 소유: `.harness/ledger.sqlite3`, SQLite 이벤트와 logical operation 예약. `BEGIN IMMEDIATE`로 쓰기를 직렬화하고 Run 예약은 프로세스 시작 전에 commit합니다. 중단 후 unknown 예약을 자동 재실행하지 않습니다.
- 파생 파일: `wiki/`, `.generated.json`. 파일 수정 감지 시 덮어쓰기를 거절합니다. 수동 수정본을 별도 보존한 뒤 생성 파일 복구 또는 새 경로를 사용합니다. 원장 commit 후 렌더 실패는 projection_warning으로 보고하며 원장 작업은 중복 실행하지 않습니다. `wiki`로 재생성합니다. 동시에 렌더하면 `.wiki-render.lock`으로 거절합니다. 중단된 렌더는 실제 프로세스 정지 확인 후 해당 marker를 보존/이동하고 복구합니다. 부분 생성/충돌은 사용자 검토 대상입니다.

`backup --out FILE`은 SQLite 일관 복사와 hash receipt를 반환합니다. `restore --source FILE --sha256 DIGEST`는 **새 ledger 경로에만** 복원하며 기존 이벤트는 삭제하지 않습니다. 파일 backup/credential 복원은 포함하지 않습니다. 복원 후 실제 inputs와 engine을 다시 검사합니다. 해시 체인은 우발적 수정 검출이며 DB와 코드를 모두 다시 쓸 수 있는 동일 OS 사용자의 악의를 막는 서명 시스템이 아닙니다.

legacy v0.12 원장/계약은 자동 이관하지 않습니다. 새 설치에서 원본을 연결하고 검증 후 선택 도입합니다. 기존 프로젝트의 실행기를 덮어쓰지 않습니다. 배포 버전, ledger schema=2, 계약 fixed-v2-1, 프로젝트 config V2/V3 ID를 분리합니다. 향후 schema/core 변경도 새로운 배포와 명시적 이관 평가가 필요합니다.

# RFC-0001 — Evolutionary Harness CLI 제품 계약과 Newgame 상호 감사

- 작성일: 2026-09-13 (Asia/Seoul)
- 상태: **Draft / human review pending**. 승인·구현·릴리스 선언이 아니다.
- Task: `TASK-20260913-CLI-RFC-001`
- Execution: `EXE-20260913-CLI-AUDIT-001`
- 작업 모드: `plan`; 변경 범위는 이 RFC와 감사 기록뿐이다.
- 제안 적용 범위: 우선 `project` 실험. 재사용 가능한 코어를 설계하지만 Domain/Core 승격은 별도 교차 프로젝트 증거가 필요하다.
- 수락 분류: `mixed`. 구조·참조·재현 결과는 machine_verifiable, 제품 적합성·우선순위·RFC 채택은 human_verifiable.

## 1. 판단과 요청 결정

**현재 실사용 운영 성숙도는 Newgame이 우세하다. 범용 CLI의 설계 출발점은 Evolutionary Harness가 더 적합하지만, 지금 폴더의 내용만으로 실행 가능한 V2 제품이라고 볼 수 없다.** 권고는 새 코어에 Newgame 전체를 복사하는 방식이 아니라, 증거·명령·저장 계약을 먼저 확정하고 Newgame의 출처 검증, 생성물 검사, 아티팩트 대조, 복구 절차를 명시적 프로젝트 어댑터로 가져오는 방식이다.

이 판단은 로컬 소스·한정된 실행 검사에 대한 해석이다. 처리량, 사용자 작업 시간, 토큰 비용, 장애 복구 시간의 비교 실측은 없다. “더 최적화됨”을 절대적인 성능 우위로 해석하지 않는다.

검토자가 결정할 사항:

1. 범용 CLI의 첫 릴리스를 로컬 단일 저장소·단일 writer로 제한할지.
2. 이벤트 원장과 명령 영수증을 위한 트랜잭션 저장소 안(B)을 채택할지.
3. 상태를 진행·검증·출시·수락·차단으로 분리하고 기존 단일 상태는 요약 뷰로만 남길지.
4. Newgame의 수동 완료 이력을 `legacy_claim`으로 보존하고 새 버전의 검증 상태와 분리할지.
5. 아래 수락 게이트를 만족한 뒤에만 별도 구현 작업을 승인할지.

이번 요청은 RFC 작성까지의 권한이다. 이 문서의 명령·경로·필드·종료 코드는 모두 **제안**이며 현재 CLI에 존재하지 않는다.

## 2. 감사 범위와 증거 기준

Evolutionary Harness의 필수 문서 순서를 준수한 뒤 상태 규칙, 5개 JSON 예시, 객체·관계·이벤트 파일, 릴리스, 평가·승격·안정성 문서를 읽었다. Newgame의 비교 대상은 별도 범용 하네스 패키지가 아니라 `AGENTS.md`, 운영 온톨로지, 생성기와 검사기, CI 산출물 전달, 릴리스·복구 코드의 조합이다. 게임 내 거래 rollback/idempotency는 CLI의 보장으로 계산하지 않았다.

감사 시작 시 Evolutionary 폴더에는 24개 파일이 있고 Git 저장소가 아니었다. `objects.json`, `relations.json`은 빈 배열이고 `events.jsonl`은 비어 있었다. Newgame은 `be23c7cad570c47e117d7521d998f5062ee23ec0`이며 작업 트리는 깨끗했다. [baseline.json](../harness/evidence/EXE-20260913-CLI-AUDIT-001/baseline.json)에 Evolutionary 원본 24개와 Newgame 추적 파일 1,362개의 SHA-256을 기록했다. Newgame의 ignored/untracked 파일, 원격 CI, 배포 환경, Notion/Sheet 라이브 상태는 감사 범위 밖이다.

근거 분류:

- `confirmed_by_code`: 특정 문서·코드·검사 분기의 존재.
- `confirmed_by_test`: 이번 로컬 검사나 합성 입력 재현에서 관찰한 좁은 동작.
- `inferred_by_static_analysis`: 코드 경로로 추론한 위험. 운영 장애가 이미 일어났다는 뜻이 아니다.
- 권고·대안 우열은 설계 판단이며 자동 확정 대상이 아니다.

### 2.1 이번에 실행한 최소 검사

| 검사 | 관찰 결과 | 입증 범위 / 한계 |
|---|---|---|
| `generate_project_ontology.py --check` | exit 0; tracked=54, objects=257, relations=483 | 생성 JSON의 현재 입력 대비 일치. 개별 작업의 E2E 통과 증명은 아님 |
| `check_notion_audit.py` | exit 0; 66행, 136.5/170 | 저장된 스냅샷·수동 대조·문서의 정합성. 게임 완료율·출시 준비율 아님 |
| `test_windows_release_retention.py` | 5 tests pass | 임시 디렉터리와 mock API의 보존·삭제 범위 |
| `test_cloudflare_release.py` | 기본 Python에서 4 pass + 1 환경 오류; 기존 `.venv`에서 5 pass | 신원·checksum·mock readback·workflow 구조·임시 위키 표식. 운영 rollback 성공 증명은 아님 |
| P01 합성 마일스톤 | 실행 증거 없이 `implemented`, `confirmed`, `verified_by:source:e2e` 생성 | 문서 표기가 검증 상태처럼 전달되는 경로 재현 |
| P02 메모리 내 레지스트리 버전 변경 | 입력 999 → 출력 999 | 생성기 자체의 미지원 schema 거부 부재 재현. 별도 PowerShell 검사에는 v3 검사 있음 |
| P03 freshness 계산 | `observed_at`이 `root_last_edited_time`에서 생성 | GDD의 관측 시각과 원본 수정 시각 혼용 확인 |

로그: [checks.json](../harness/evidence/EXE-20260913-CLI-AUDIT-001/checks.json), [environment-check.json](../harness/evidence/EXE-20260913-CLI-AUDIT-001/environment-check.json), [probes.json](../harness/evidence/EXE-20260913-CLI-AUDIT-001/probes.json), [재현 입력](../harness/evidence/EXE-20260913-CLI-AUDIT-001/probe-source.txt), [재현 출력](../harness/evidence/EXE-20260913-CLI-AUDIT-001/probes.txt).

환경 오류는 지우거나 테스트 실패와 합치지 않았다. 패키지를 설치하지 않고 이미 존재하던 Newgame 가상환경으로 한 번 재실행했다.

## 3. Evolutionary Harness 감사

심각도는 CLI 제품 출시를 기준으로 한다. **P0**는 진실성·복구 가능성을 깨뜨릴 수 있는 출시 차단, **P1**은 필수 제품 계약 공백, **P2**는 운영 효율 개선이다. 미구현 문서를 이미 발생한 런타임 결함으로 부르지 않는다.

| ID / 우선도 | 관찰과 근거 | 실패 시나리오 | RFC 처방 |
|---|---|---|---|
| EH-01 / P0 | 릴리스가 v2.0.0과 9개 `verified_capabilities`를 선언하지만 최초 이벤트·객체·관계는 비어 있고 실행기·평가 결과가 없다 [E1,E3] | 설치·자동화가 문서 선언을 검증된 기능으로 신뢰 | declared와 verified 분리; capability별 버전 결합 증거 없으면 unverified |
| EH-02 / P0 | `*.schema.example.json` 5개는 예시 레코드다. 필수 필드·타입·enum·참조 검증 정의 및 validator가 없다 [E2] | 잘못된 timestamp/빈 증거/중복 ID/unknown type을 정상 원장에 저장 | 기계 스키마 + 의미 검증 + 오염 입력 거부를 출시 조건으로 설정 |
| EH-03 / P0 | `version` 하나와 `hash_or_ref`만으로 코드·데이터·환경·규칙을 결합할 수 없다. Evidence에 pass/fail, TestRun/Execution 계약이 없다 [E2,E4] | HEAD가 같고 CSV나 dirty 파일이 다른데 과거 통과 재사용 | 입력 manifest, acceptance/test-definition/rule/environment 해시와 개별 실행 결과 |
| EH-04 / P1 | state는 “may include”; verified 조건만 있고 전이·충돌 우선순위·latest 순서가 없다 [E4] | verified+blocked, released+stale를 단일 문자열로 덮어써 정보 소실 | 독립 축 + 결정적 reducer + 사유·증거·watermark 출력 |
| EH-05 / P0 | 이벤트·객체·관계·checkpoint 사이 원본/캐시 구분과 쓰기 원자성이 불명확 [E1,E5] | 이벤트 append 뒤 객체 저장 전 중단, 다중 writer lost update | 단일 원장과 명령 트랜잭션, revision CAS, 재생 가능한 뷰 |
| EH-06 / P1 | query/analysis/plan/execute는 에이전트 규칙이며 CLI 입력·출력·exit·권한 계약은 없다 [E1,E6] | read 명령이 초기화·동기화·자동 복구를 수행하거나 사람이 읽는 로그를 파싱 | 공통 envelope, 읽기 무변경, plan/apply 분리, 권한 증거 |
| EH-07 / P1 | object만 schema_version; core_version은 있지만 storage/protocol/rule/adapter 호환 범위 없음 [E2,E3] | 구 CLI가 새 event를 무시해 잘못된 verified 생성 | 버전 축·필수 feature·미지원 의미 거부·명시적 migration |
| EH-08 / P0 | rollback_ref는 nullable이고 “rollback path” 원칙만 있다 [E2,E7] | 바이너리만 내렸는데 DB가 새 형식이거나 복구 중 과거 이후 증거 소실 | 코드·원장·projection·외부 변경의 복구 경계 분리; 실제 복구 eval |
| EH-09 / P0 | idempotency 요구는 있으나 operation ID, request digest, durable receipt 없음 [E1,E6] | 외부 작업 성공 뒤 응답 유실 → 재시도 중복 실행 | semantic key + payload 충돌 거부 + 불명 결과 조정 |
| EH-10 / P1 | retry 분류와 failure taxonomy만 있고 오류별 보존·종료·복구 계약이 없다 [E6,E7] | parse 오류를 무한 retry하거나 partial write를 성공으로 보고 | failure matrix, bounded retry, partial/unknown outcomes, recover |
| EH-11 / P1 | relation은 provenance 목록을 갖지만 관측 대상 버전·대체/철회·방향별 의미 규칙이 없다 [E1,E2] | 정적 참조나 LLM 추론이 최신 실행 증거처럼 test 선택에 사용 | 근거 종류와 확신 표현 분리; 적용 snapshot·유효 구간·충돌 보존 |

EH-01은 프로젝트의 README가 요구하는 “버전은 검증된 능력” 원칙과 릴리스 선언 사이의 충돌이다. 이번에는 릴리스 manifest를 고치지 않고 충돌과 후보 요구를 등록한다.

## 4. Newgame 감사와 역방향 검토

### 4.1 Evolutionary 기준으로 Newgame을 감사

| ID / 우선도 | 확인된 강점 또는 공백 | 근거·분류 | CLI에 가져올 때의 조치 |
|---|---|---|---|
| NG-01 / P0 | 문서 완료 표기 → implemented/confirmed; 레지스트리 UI명은 ‘구현·검증됨’. verified_by가 구체 TestRun이 아닌 source:e2e | [N1,N2], P01; confirmed_by_test | 기존 역사 보존, legacy_claim과 verification 분리. 기존 작업이 실제 미완료라는 판정은 금지 |
| NG-02 / P1 | 생성기의 입력 schema_version 999가 출력으로 전달됨. wrapper는 v3를 검사 | [N2,N3], P02; confirmed_by_test | 각 public command 진입점에서 호환성 검사; wrapper를 거쳐야만 안전한 구조 제거 |
| NG-03 / P1 | ontology generator는 직접 write_text; registry·Markdown·파생 JSON을 묶는 공통 transaction/lock/receipt 없음 | [N2]; inferred_by_static_analysis | 파일 소유권·projection replace·원장 revision 계약. 전체 Newgame에 lock이 전혀 없다는 주장은 아님 |
| NG-04 / P1 | GDD freshness.observed_at은 수정 시각, tracker는 captured_at | [N2], P03; confirmed_by_test | source_modified_at과 observed_at 분리. 새로 관측한 오래된 문서를 불필요하게 stale 처리하는 비용 방지 |
| NG-05 / 강점 | 소스 hash와 생성물 비교, 중복 ID·끊어진 관계 검사; 수동 Notion 대조에 양쪽 snapshot hash와 전체 행 정합성 요구 | [N2,N3,N4], CHECK-01/02 | hash 기반 drift gate를 재사용. 파일 존재 검사를 TestRun 증거로 승격하지 않음 |
| NG-06 / 강점 | CI 전달은 repo/run/attempt/commit/tree/파일 hash에 묶이고 임시 디렉터리에서 검증 후 rename; 대상 덮어쓰기 거부 | [N5]; confirmed_by_code | 실행 신원·불변 전달 패턴을 어댑터로 재사용. 재실행 거부는 결과 재생 idempotency와 다름 |
| NG-07 / 강점 | Web/Windows commit·checksum 대조, candidate readback, 이전 게임 identity 보존, 성공 후 current+previous download 보존 | [N6,N7,N8], 로컬 10 tests | artifact identity, prepare→verify→activate→verify→retain 흐름 재사용 |
| NG-08 / P0 | rollback 조건은 game_promotion outcome=success에 의존. 원격 활성화 후 명령이 실패/취소되면 이 경로로 복구된다고 증명할 수 없음 | [N7:816-824,888-897]; inferred_by_static_analysis | effect_unknown과 provider readback 조정 필요; 실제 장애를 발생시켜 시험하지 않음 |
| NG-09 / P1 | 복구는 현재 checkout의 Worker를 이전 artifact vars로 재배포하고 healthz의 commit을 확인; 이전 Worker 코드·wiki·auth 상태 전체 복구가 아님 | [N7:888-897]; confirmed_by_code | rollback target에 adapter/code/config/data 범위와 별도 health 계약 명시 |
| NG-10 / P1 | 업로드는 commit 경로와 immutable cache header를 쓰지만 호출 자체에 기존 payload digest 충돌 검사/영수증이 보이지 않음. 활성 commit 재배포는 release_state가 거부 | [N6,N8]; inferred_by_static_analysis | 같은 key+다른 bytes를 거부하고 같은 요청 결과를 재사용. 경로 이름만으로 write-once 보장 주장 금지 |
| NG-11 / P1 | 복구 PR은 승인 namespace+SHA 검증과 history-preserving commit을 사용. 실행 ID 기반 새 branch를 생성하며 no-op은 exit 1 | [N9]; confirmed_by_code | 검증된 복구 경로 재사용; no-op/실패·중복 요청의 CLI 의미를 별도로 표준화 |
| NG-12 / P1 | 위키 auth bootstrap은 원격 get 실패를 else 분기로 처리하여 put으로 이어질 수 있음 | [N7:768-801]; inferred_by_static_analysis | not_found와 timeout/permission/unavailable 분리. credential 흐름은 MVP 범위 밖, 기본 어댑터에 가져오지 않음 |

### 4.2 Newgame 운영 기준으로 Evolutionary를 역감사

| Newgame이 요구할 반론 | Evolutionary에 대한 판단 | RFC 반영 |
|---|---|---|
| 실제로 어떤 명령이 생성물 drift를 막는가? | 문서만 있고 `--check` 대응 실행 증거 없음 | status/check/explain을 MVP 최우선으로 배치 |
| 사건마다 그래프 전체를 작성하면 유지 비용이 커지지 않는가? | 사람이 객체·관계·Markdown을 따로 관리하면 중복 증가 | 이벤트에서 재생; 어댑터가 수집 가능한 관계는 자동 관측; 한 작업의 필요한 부분만 로드 |
| 코드와 데이터가 실제로 같은 산출물인지 어떻게 아는가? | 추상 version 필드로는 Web/Windows/CSV 차이를 표현하기 어려움 | 여러 artifact/data digest 및 test target 명세 |
| 모든 관계가 완전해질 때까지 일을 못 하는가? | relation 기반 test selection이 아직 ‘eventually’ 수준 | 미상 영향은 보수적 필수 검사로 fallback; 주기적 full regression |
| 게임별 오너·Sheet·Notion·배포 규칙을 코어가 침범하지 않는가? | overlay 개념만 있고 충돌·버전 계약 없음 | adapter read 권한부터 시작; Newgame의 권한은 이 프로젝트로 상속하지 않음 |
| rollback을 할 수 있다고 쓰는 것만으로 충분한가? | 경로 선언만으로 성공을 증명할 수 없음 | 이전 reader + snapshot + 중단점별 회복 실험을 promotion gate로 사용 |
| 코어 복잡도 대비 효익이 있는가? | V3/V4 자동 승격을 지금 구현하면 검증 전 비용 증가 | 로컬 V2 최소 계약부터 실측하고 승격은 별도 단계 |

이는 **동일 작성자의 두 기준을 교차 적용한 상호 감사**다. 독립된 두 감사자의 합의나 다중 에이전트 검토로 표현하지 않는다. 재현 가능한 사실과 설계 선호를 분리하고, 독립 리뷰가 필요한 판단은 Draft에 남긴다.

## 5. 제안 상태 모델

### 5.1 단일 상태 대신 독립 축

| 축 | 제안 값 | 권위 |
|---|---|---|
| intent | proposed / approved / rejected / superseded | 출처가 있는 Requirement/Decision, 사람 판단 |
| progress | planned / active / implementation_observed | version-bound ChangeSet·구현 관측 |
| verification | unknown / unverified / running / passed / failed / stale / conflicted | 필수 TestDefinition, TestRun, Evidence와 reducer |
| delivery | unreleased / release_prepared / released / deployed / rollback_pending / rolled_back / unknown | artifact와 대상 환경의 활성 신원 관측 |
| acceptance | pending / accepted / rejected / superseded | acceptance_class와 그에 맞는 명시적 판단 |
| blockers | 0개 이상의 원인 객체·참조 | 정책·충돌·의존성·무결성 사실 |

예: 과거 릴리스 후 새 CSV가 바뀌면 `delivery=deployed`인 역사와 `verification=stale`인 현재 요구를 함께 표시한다. blocker가 생겼다고 과거 통과·출시 사실을 삭제하지 않는다. 제품 품질이 human_verifiable이면 tests가 통과해도 acceptance는 pending이다.

### 5.2 결정적 도출 계약

`derive(snapshot_id, committed_event_seq, rule_digest, graph_digest, acceptance_digest, evaluation_time)`가 동일하면 동일한 canonical 결과와 state_digest를 내야 한다. 시간 기반 freshness는 숨은 wall clock 대신 명시적 evaluation_time을 사용한다.

1. 손상·미지원 의미·중복/깨진 필수 참조 → `conflicted` 또는 입력 오류. 조용히 skip하지 않는다.
2. 요구/구현/필수 테스트 목록을 모르면 `unknown`; 알려진 테스트가 0개라고 vacuous pass를 만들지 않는다. 테스트 불필요 예외는 승인된 명시적 contract가 있어야 한다.
3. 목표 snapshot과 run의 코드·데이터·환경·검사 정의·수락 조건·규칙을 비교한다. 영향 없음은 독립된 호환/영향 증거로 명시되어야 하며 경로 추정만으로 pass를 이월하지 않는다.
4. “latest”는 시계가 아닌 원장 sequence와 test slot의 attempt 순서다. 현재 선택된 필수 attempt가 진행 중이면 running, 실패면 failed다. 과거 pass를 골라 최신 fail을 덮지 않는다. 같은 attempt의 서로 다른 최종 결과는 conflicted다.
5. 현재 버전의 필수 runs가 전부 종료·통과했고 증거가 온전하며 blocker가 없을 때만 verification=passed. 목표에 맞는 run이 없고 이전 증거만 있으면 stale, 증거 자체가 없으면 unverified.
6. acceptance와 delivery는 verification에서 자동 생성하지 않는다. `released`는 manifest 존재만으로, `deployed`는 CLI exit 0만으로 도출하지 않는다.

호환용 task summary의 우선순위는 `conflicted > blocked > verification_failed > stale > active > verified > implemented_unverified > planned`. release/deployment는 별도 badge이며 이 요약에 섞지 않는다. `status --explain`은 선택·제외된 증거, blocker, rule version, snapshot, watermark를 반환한다.

### 5.3 필요한 레코드 계약

기존 예시를 즉시 교체하지 않는다. 구현 시에는 다음 정의를 기계 스키마와 의미 검사로 제공한다.

| 레코드 | 최소 계약 |
|---|---|
| 공통 envelope | schema_id/version, workspace_id, globally unique immutable id, record_type, created_at(UTC), producer identity, payload digest, namespace extensions |
| Execution | stable task_id, execution_id, parent/resume linkage, attempt_id, mode, requested command, input_snapshot, actor, start/end, outcome, failure/retry class |
| Snapshot/ChangeSet | Git commit/tree 가능 시 기록, dirty/untracked의 포함 목록과 bytes hash, 비Git manifest hash, data/config/test/env/toolchain hashes, scope·제외 사유 |
| Acceptance/TestDefinition | machine/human/mixed, 필수 slot·검사 argv·환경·timeout·성공 판정·영향 범위, 정의 digest; human 판단의 actor/권한/source_ref |
| TestRun/Evidence | 실행 신원·slot/attempt·target manifest, pass/fail/error/cancelled, 시작/종료, exit, raw artifact refs+sha256+size, producer, supersedes/invalidation |
| Event | event_id, command/operation_id, sequence, subject, execution_id, event_type+version, evidence refs, prev/expected revision, payload digest; timestamp는 정렬 권위 아님 |
| Relation | from/to/type, 지정 provenance enum, 근거 refs, source snapshot, observed_at, 유효 시작/대체·철회. `verified_by`는 test definition과 test run을 구별 |
| Release/Compatibility | cli/core/rules/storage/protocol/adapter version와 digest, verified capability별 evidence, supported read/write versions, migration/rollback refs |
| OperationReceipt/Failure | idempotency scope/key, normalized request digest, durable phase/outcome, provider request id, attempts, error code/retry class, observed effect, recovery refs |

검증은 JSON parse와 구분한다. 필수 값·enum·UTC·digest 형식·중복 ID뿐 아니라 dangling ref, relation endpoint type, execution/task 연결, TestRun의 snapshot, 범위 밖 경로, 승인 권위도 검사한다. 알 수 없는 최상위 의미 필드는 거부하고 비의미적 확장은 namespace 아래 보존한다. 추론 근거에 confidence='confirmed'를 붙이는 방식으로 provenance를 승격할 수 없다.

## 6. 제안 CLI 명령 계약

명령 이름은 `eh`를 가칭으로 쓴다. 배포·Git push·credential 작업은 MVP에 포함하지 않는다.

### 6.1 공통 규칙

- `--workspace <absolute-path>`, `--format json|text`, `--no-input`, `--timeout`, `--dry-run`의 지원 범위를 help와 machine-readable command manifest에 명시한다.
- query/analysis는 원장·projection·cache·migration·네트워크를 쓰지 않는다. 저장소가 없어도 자동 init하지 않는다. read 명령은 실행 ID를 응답에 생성할 수 있으나 원장에 기록하지 않는다.
- `--dry-run`은 잠금·journal 포함 영속 변경 없이 예상 쓰기·권한·선행 조건을 출력한다. `plan --out <path>`만 사용자가 지정한 새 계획 파일을 생성하는 명시적 예외이며 기존 파일을 덮지 않는다.
- `plan`은 등록과 검토를 허용할 뿐 제품 구현이나 외부 side effect를 승인하지 않는다. `apply`는 승인된 정확한 계획과 권한 범위에만 작용한다.
- text는 사람용이다. JSON stdout은 성공/오류에 하나의 versioned envelope만 출력하며 progress·diagnostics는 stderr. 비TTY/--no-input에서는 prompt하지 않고 필요한 입력·승인 오류를 반환한다. bootstrap parser 오류도 JSON 모드 요청을 가능한 한 먼저 처리한다.
- JSON envelope: `protocol_version, command, workspace_id, request_id, execution_id?, operation_id?, outcome, data, evidence_refs, revision, warnings, error{code,message,retry_class,next_action}?`. 비성공도 같은 외형이다. 파일 경로·증거 해시를 제공하되 credential 값은 기록하지 않는다.
- write는 `--expect-revision`과 stable `--idempotency-key`를 받는다. `--yes` 같은 옵션이 policy 권한을 확대하지 않는다. 승인 근거가 이미 있으면 동일 범위의 재확인을 요구하지 않는다.

### 6.2 명령별 입력·쓰기·실패

| 명령(제안) | 입력 / 출력 | 쓰기 소유권 | 주요 실패·재시도 |
|---|---|---|---|
| `eh inspect`, `eh status --explain`, `eh doctor` | root/revision → 발견된 상태·근거·복구 안내 | 없음; doctor도 자동 fix 없음 | 없거나 손상된 원장은 명시적 오류/제한된 진단 |
| `eh check` | snapshot/rules → 무결성·호환·projection drift 결과 | 없음 | 검사 실패와 내부 오류 분리 |
| `eh init --plan`, `eh init --apply <plan>` | 점유 경로·권한·템플릿 hash → 계획/초기화 영수증 | 신규 managed 영역만 | 동일 bootstrap 재요청은 결과 재사용, 사용자 파일 충돌은 중단 |
| `eh task register`, `eh execution start` | intent source, task, mode, snapshot → ID·revision | 원장 | ID/request 충돌·권한 부족·revision conflict |
| `eh evidence add` | evidence manifest+blob refs+execution → evidence ID | blob CAS와 원장 | 손상·다른 digest·범위 밖 참조 거부 |
| `eh project --check`, `eh project --apply` | watermark/rules → drift 또는 생성물 목록 | --apply만 projection | stale plan, 수동 수정 충돌. 원장 성공과 projection 실패 구분 |
| `eh operation status <id>` | operation ID → durable phase/effect | 없음 | unknown이면 임의 성공/실패 추정 금지 |
| `eh recover --plan`, `eh recover --apply <plan>` | incomplete operation → 재조정·복구 계획/결과 | 허가된 원장·projection만 | lock 소유자·외부 불명 결과 확인 필요 |
| `eh migrate --plan`, `eh migrate --apply <plan>` | 현재/목표 format·snapshot → 호환 보고/새 generation | 원장 migration 영역 | 미지원·손실 변환·dirty drift 거부 |
| `eh harness activate/rollback --plan|--apply <plan>` | release digest, expected active digest, compatibility/rollback proof | 로컬 하네스 선택 기록 | reader 불일치·복구 불가·승격 증거 없음이면 중단 |

첫 제품의 evidence add는 외부 파일을 읽어 복사하는 동작과 단순 ref 저장을 구별한다. 외부 스크립트 실행·네트워크 수집은 별도 등록 어댑터의 명시적 capability로만 추가한다. query에서 임의 test runner를 실행하지 않는다.

종료 코드 계약(제안): `0` 완료/동일 요청 결과 재생/정당한 no-op, `2` 입력·스키마 오류, `3` 선행 조건·참조 부재, `4` policy/승인 부족, `5` revision·소유권·key 충돌, `6` 무결성·검사 실패, `7` 버전 비호환, `8` 일시 환경 장애/lock timeout, `9` partial·effect_unknown·복구 필요, `10` 내부 결함, `130` 사용자 취소. OS 강제 종료는 프로세스 JSON을 보장할 수 없으며 durable receipt로 확인한다. `status` 조회 성공은 태스크 통과가 아니므로 exit 0과 verification을 구분하고, gate 목적은 `check`를 사용한다.

계획에는 command digest, workspace identity, input/revision, 예상 파일별 before/after hash, required permissions, expiry/evaluation_time, rollback 범위를 포함한다. apply 직전에 전부 재대조한다. 바뀐 입력에 과거 승인을 재사용하지 않는다.

## 7. 파일 소유권과 트랜잭션

### 7.1 저장 방식 대안

| 안 | 장점 | 단점 | 판단 |
|---|---|---|---|
| A. JSON/JSONL을 모두 권위 원본으로 유지 | Git diff와 수동 확인이 쉬움, 초기 의존성 작음 | 다중 파일 commit/lock/receipt/깨진 append 회복을 직접 설계해야 함 | 읽기 전용 prototype에는 적합; mutable CLI 출시 기본안으로 비권고 |
| B. 로컬 트랜잭션 DB 원장 + 불변 blob + JSON/Markdown projection | 이벤트·receipt·revision을 한 transaction으로 결합; CAS·재생·중복 방지가 명확 | DB tooling·backup·migration 비용, Git merge 불가 | **MVP 권고**. SQLite를 후보로 삼되 crash/Windows eval 전 보장 주장 금지 |
| C. 외부 서비스 원장과 분산 worker | 중앙 권한·여러 장치 조정 | 인증·운영·네트워크 장애·비용·설치 복잡성 | 수요·실측 전 도입 보류 |

### 7.2 제안 소유권 표

아래 `.harness/` 경로는 아직 만들지 않는다.

| 경로 | 소유자 / 권위 | 편집·수명 규칙 |
|---|---|---|
| `AGENTS.md`, `docs/harness/source-authority.md`, policy | 사람/프로젝트 관리; 의도·권한 원본 | init가 덮지 않음. 현행 파일에 managed marker 없으면 전체 사용자 소유로 취급 |
| `.harness/workspace.json`, config | 프로젝트 설정; workspace identity | 설정 변경 명령 또는 명시적 사용자 편집 후 validate. secrets는 외부 credential store 참조만 |
| `.harness/store/<generation>/ledger.sqlite` | CLI 단일 writer; 이벤트·assertion·영수증·활성 선택의 원본 | 업무 사실 append-only. 정정·철회는 새 record. 내부 index/queue는 운영 상태이며 사실의 별도 원본 아님 |
| `.harness/store/ACTIVE` | recovery manager; 검증된 store generation 선택자 | 정상 명령은 수정 금지. journal과 expected digest를 사용한 migration switch만 허용 |
| `.harness/blobs/sha256/<digest>` | CLI 불변 증거 저장 | 원본 bytes, size/hash 확인. 초기 제품은 자동 GC 없음 |
| `.harness/cache/`, `.harness/staging/` | CLI 파생/임시 영역 | 부분 파일은 권위 아님. recover가 operation 소유권을 확인하고 처리 |
| `.harness/releases/<digest>/` | 불변 로컬 release package | 전체 package hash·호환성 확인. 활성 release 선택은 원장 event의 projection |
| `.harness/snapshots/` | CLI 일관 snapshot·manifest | 원장·blob 목록·활성 release/rules 연결. raw live DB 복사로 backup을 대신하지 않음 |
| `docs/harness/objects.json`, `relations.json`, `events.jsonl`, checkpoint/backlog | 이관 이후에만 생성기 소유 projection/export | 기존 bytes의 snapshot과 사용자 검토 후 명시적으로 소유권 전환. 다른 원본과 dual-write 금지 |
| RFC, 수동 Decision 문서 | 사람/작성자 | 승인 사실은 출처와 함께 원장에 수집; 문서를 자동 approved로 해석하지 않음 |
| Newgame 코드·registry·CSV·Notion·Sheet·CI | 기존 프로젝트/외부 시스템 | 기본 read-only adapter. 새 코어가 소유권·자격증명·기존 standing authorization을 가져오지 않음 |

managed projection에 예상하지 못한 수동 변경이 있으면 충돌 diff를 내고 중단한다. `--force`로 사용자 파일을 지우는 우회는 MVP에서 제공하지 않는다. canonical 절대경로, workspace ID, symlink/junction/reparse point 및 case 충돌을 검사하고 workspace 밖 쓰기를 막는다. Git clone/worktree/복사본의 workspace 신원 재사용은 `adopt` 검토 없이는 write 불가다. 공유 DB를 Git merge하거나 네트워크 공유 경로에서 쓰는 기능은 MVP 미지원이다.

### 7.3 commit과 장애 경계

1. 입력을 읽고 대상 manifest·policy·schema·호환성을 검사한다. 검증 전 init/migration을 하지 않는다.
2. blob을 같은 관리 영역의 임시 파일에 쓰고 digest·size를 확인하여 불변 위치에 게시한다. 이 단계의 고아 blob은 업무 사실이 아니다.
3. 단일 writer lock과 transaction 안에서 expected revision, idempotency scope, payload digest를 검사한다. event·references·receipt·revision을 함께 commit한다. 이것이 **업무 기록의 commit point**다.
4. commit된 event에서 뷰를 만든다. projection은 temp→replace하고 마지막에 generation manifest를 게시한다. 독자는 완성된 동일 watermark의 묶음만 읽는다.
5. 3 이후 projection 실패는 원장 rollback이 아니라 `committed_projection_pending`, exit 9로 보고한다. 같은 key를 다시 적용해 사건을 중복 생성하지 않고 project/recover로 뷰만 복구한다.

Windows file sharing, antivirus lock, ENOSPC, 프로세스 중단, rename/flush 실패를 실제 파일시스템에서 eval해야 한다. 원자적 rename만으로 전원 장애 내구성이 자동 입증됐다고 말하지 않는다. lock은 timeout과 owner identity를 기록하고 시간 경과만으로 살아 있는 writer lock을 훔치지 않는다. 여러 요청은 직렬화하며 stale revision은 덮어쓰기 대신 conflict다.

## 8. 버전 호환성과 이관

버전을 `cli SemVer`, `command protocol major/minor`, `storage format`, `record schema`, `state rule digest`, `adapter version`, `harness release/capabilities`로 분리한다. 하나의 v2 숫자로 모두 호환됨을 표현하지 않는다.

| 조합 | reader / writer 계약 |
|---|---|
| 지원 format·schema·필수 capabilities 일치 | 읽기 가능; policy·revision 검사를 통과한 write만 가능 |
| 미래 major 또는 미지원 required feature | doctor의 제한적 진단만; derived truth 생성·write 금지, exit 7 |
| 같은 major의 추가 optional metadata | 명시적으로 비의미적이라고 선언된 namespace만 보존/통과; 알 수 없는 상태/event는 무시 금지 |
| 구 storage → 새 storage | read가 자동 upgrade하지 않음. migrate plan·snapshot·검사·명시적 apply 필요 |
| 새 rule → 기존 event | 과거 증거 원문 보존, 새 rule로 별도 projection. 이전 판정은 해당 rule과 watermark로 조회 가능 |
| adapter/overlay 불일치 | 해당 effect 차단. 코어 읽기를 가능한 범위에서 유지하되 의존 상태는 unknown/blocked |

Newgame 이관은 read-only inventory → ID namespace 매핑 → 불변 snapshot → legacy assertion import → relation 출처 분류 → 최신 계약의 필수 run 연결 → dual-read 비교 → 선택적 write 전환 순서다. source:e2e 링크는 source reference로 이관하고 TestRun pass로 바꾸지 않는다. 문서 ‘완료’와 오너 결정 역사는 삭제하지 않는다. 기존 registry와 새 원장에 동일 업무 상태를 동시에 쓰지 않는다. ID map·source hash·import key를 보존하여 재수입 중복을 방지한다.

Migration은 writer를 잠시 중단하고 검증된 일관 snapshot으로 새 generation을 staging한다. 레코드 수·ID·참조·원본 blob hash·정정/철회 계보·replay 결과를 검사한 뒤 ACTIVE를 전환한다. 실패하면 구 generation을 계속 사용한다. 형식이 같아도 상태 규칙 변경은 재평가 대상이다. core/domain/project overlay는 permission 축소와 domain 확장만 허용하며 root authority나 stability anchors 충돌은 명시적 인간 판단 대상으로 남긴다.

## 9. Rollback 계약

rollback은 다음 네 가지를 구분한다.

1. **실행 실패 회복**: commit 전이면 업무 변경 없음; commit 후면 receipt로 완료 여부 확인. 증거는 삭제하지 않고 abort/compensation event를 추가한다.
2. **projection 복구**: 신뢰 가능한 event watermark와 rule로 재생성한다. 원장 변경이나 과거 성공의 소거가 아니다.
3. **하네스 release rollback**: 이전 CLI/rule/adapter가 **현재** ledger format·event semantics를 읽을 수 있을 때만 활성 선택을 이전 digest로 바꾼다. capability·compatibility·복구 검사 증거가 필요하다.
4. **migration/외부 effect 복구**: 전환 직후 새 업무 write가 없으면 사전 snapshot의 generation으로 되돌릴 수 있다. 이후 event가 생겼다면 단순 snapshot 복원은 금지한다. 새 event를 보존하는 검증된 역변환/forward repair가 없으면 blocked다. 외부 배포·데이터·credential 변경은 해당 provider의 별도 보상 작업과 권한이 필요하다.

Rollback plan은 `from/to release+store digest`, expected active revision, snapshot manifest, 영향을 받는 adapters, 데이터 손실 여부, 보존해야 할 이후 event, 권한, 성공 관측, 실패 시 안전한 next action을 포함한다. raw Git reset이나 DB 파일 복사로 원장·외부 진실을 복구했다고 선언하지 않는다.

release 활성화 전 snapshot을 실제로 별도 위치에서 restore·read·replay하고 필수 check를 통과시켜야 한다. rollback 후에는 새 Execution과 `ROLLBACK_*` event로 시도·효과·확인을 남긴다. rollback 자체의 결과가 불명이면 `rollback_pending/unknown`을 유지하고 다음 release 활성화를 차단한다. 오래된 snapshot/이전 artifact를 지우는 retention은 보호 참조와 복구 가능 기간이 정해지기 전 자동화하지 않는다.

Newgame의 artifact prefix 전환·이전 download 보존은 좋은 출발점이지만 Worker 코드·wiki/auth·원장 schema 복구까지 보장하는 것으로 확대 해석하지 않는다.

## 10. Idempotency와 재시도

`task_id`는 업무 신원, `execution_id`는 시도 묶음, `attempt_id`는 테스트/재시도, `operation_id`와 `idempotency_key`는 논리적 side effect다. 외부 작업을 재시도할 때 Execution이 바뀌어도 operation key는 유지한다.

키 범위는 `(workspace_id, authority principal, command kind, provider/resource target, key)`다. canonical request digest는 protocol version, 정규화된 인자·target·input snapshot·effect payload·권한 범위를 포함하고 로그 시각/표시 형식 같은 비의미 값은 제외한다. canonicalization version도 저장한다.

| 상황 | 계약 |
|---|---|
| 같은 key + 같은 digest + completed | 저장된 원래 결과·증거·operation ID 반환, 새로운 effect/event 없음 |
| 같은 key + 다른 digest | exit 5; 기존 요청을 덮거나 새 요청으로 해석하지 않음 |
| 같은 key + 실행 중 | 기존 operation 반환, 중복 dispatch 금지 |
| 같은 key + committed_projection_pending | 기존 commit 유지, 명시적 projection 복구만 수행 |
| 같은 key + 원격 effect_unknown | provider request ID·target version·digest를 조회하고 reconcile. 확인 불가능하면 차단 |
| 프로세스가 원격 성공 응답을 받기 전 종료 | 성공/실패 어느 쪽으로도 추정하지 않음. 재시도보다 state check 우선 |

원격 호출 전 durable intent를 저장하고, dispatch 이후 결과가 확정될 때까지 phase를 유지한다. provider가 idempotency/CAS를 지원하면 그 key·expected version을 전달한다. 지원하지 않으면 효과의 안정적 신원을 조회할 수 있어야 하며, 조회도 불가능한 작업에는 exactly-once를 약속하지 않는다. retry는 기존 policy의 safe_retry / state_check_before_retry / human_approval_before_retry / not_retryable로 분류하고 attempts·deadline·backoff 상한을 명시한다.

receipt는 operation 수명과 audit/rollback 보존 기간보다 짧게 만료시키지 않는다. 초기 제품에서는 삭제하지 않는다. payload가 큰 로그는 hash ref로 분리할 수 있지만 key/digest/outcome tombstone은 남긴다. 관측되지 않은 key 만료 후 동일 key를 새 effect로 받아들이지 않는다.

## 11. Failure mode와 복구 표

| 입력/중단점 | 보존해야 할 사실과 사용자 결과 | 재시도/복구 | 수락 fixture |
|---|---|---|---|
| JSON 손상·부분 legacy JSONL·중복 ID·필수 ref 없음 | 원본 bytes 보존, check 실패; 잘못된 record를 skip하여 verified 생성 금지 | not_retryable; 명시적 정정/import 계획 | F01 |
| 미지원 schema/event/rule | 미지원 위치와 필요한 reader 출력; write 0건 | compatible reader/migration 선택 | F02 |
| 증거 hash 불일치·파일 누락·data drift | 이전 pass 역사와 현재 stale/conflict 함께 노출 | snapshot 재취득·필수 검사 | F03 |
| 같은 revision에 두 writer | 한쪽만 commit; 다른 쪽 conflict | 최신 revision에 새 plan. 같은 key는 receipt 조회 | F04 |
| blob 게시 후 DB commit 전 중단 | 업무 event 없음, 고아 blob은 증거로 자동 채택 금지 | recover plan; 새 요청은 안전하게 원래 key 사용 | F05 |
| DB commit 후 projection/응답 전 중단 | committed receipt 존재, 성공 업무 중복 금지 | receipt 조회→project 복구 | F06 |
| disk full·권한 오류·Windows 공유 위반 | 원본·이전 projection 유지, temp는 incomplete | 환경 수정 후 bounded retry; 무조건 loop 금지 | F07 |
| 원격 timeout/429/5xx/취소 | not_found와 구별; effect_unknown 기록 | key+provider readback, 미확인 재dispatch 차단 | F08 |
| 원격 활성화 성공+응답 유실 | 원격 관측 후 completed 또는 보상 필요 판정 | state_check_before_retry | F09 |
| rollback 실패/새 기록 발생 후 snapshot 복원 요청 | 신규 event와 과거 evidence 모두 보존 | 역변환/forward repair 없으면 blocked | F10 |
| 사용자 파일·dirty tree·외부 경로/junction 충돌 | 대상별 diff·소유자, 쓰기 0건 | 명시적 새 계획; 사용자 파일 자동 덮어쓰기 금지 | F11 |
| 시계 역행·늦게 도착한 event·상충 증거 | sequence/attempt로 정렬; 충돌 보존 | 동일 evaluation_time replay 검사 | F12 |
| 승인 취소·policy 변경·plan 입력 drift | 과거 승인 사실은 보존, dependent apply 차단 | 새 권한/새 계획 필요 | F13 |
| adapter 의존성/실행 도구 없음 | environment_failure; 테스트 assertion failure와 분리 | doctor 안내; 읽기 중 자동 install 금지 | F14 |

`failure()`나 프로세스 exit만으로 외부 effect 유무를 판단하지 않는다. 부분 성공에는 수행된 범위·미수행 범위·관련 evidence·다음 허용 동작을 함께 반환한다. 상세 diagnostic이 있어도 비밀이나 token은 기록하지 않는다.

## 12. 상호 감사 후 대안 비교

| 비교 기준 | Newgame 현행 | Evolutionary 현행 | RFC 권고 조합 |
|---|---|---|---|
| 즉시 프로젝트 운영 | 실행기·생성 검사·CI 흐름 존재, 이번 일부 검사 통과 | 실행 CLI 없음 | 구현 전이므로 즉시 대체 금지 |
| 진실성 원칙 | source separation·owner boundary 강점; 일부 상태 표기 혼합 | 증거·human acceptance 원칙이 명확; 자기 manifest와 충돌 | 원칙을 schema/reducer/receipt로 강제 |
| 명령 일관성 | Python/PS/CI별 인터페이스·오류·환경 상이 | 계약 부재 | 하나의 envelope·exit·mode·권한 모델 |
| 파일 소유·동시성 | 생성물 경계와 run-scoped transport는 구체적; 공통 업무 transaction 없음 | 객체·event·projection 권위 불명확 | 원장 1개 + 재생 가능 projection |
| 버전·rollback | commit/tree/artifact와 구 download 호환 실용적; 전체 하네스 migration 아님 | 계층·rollback 선언만 있음 | 버전 축과 store/release/외부 effect 복구 분리 |
| 일반화·설치 | Godot, SFH, Notion, Sheet, Cloudflare 결합 비용 큼 | 도메인 중립 문서라 출발 비용 낮음 | generic core + opt-in adapter |
| 실패 진단·idempotency | 일부 fail-closed·동일 대상 거부; 통일 영수증 없음 | 분류 원칙만 있음 | phase·request digest·불명 효과 조정 |
| 운영 비용 | 실제 프로젝트에 필요한 검사·뷰 축적; 이식 시 불필요한 결합 발생 | 파일 수가 적어도 수동 기록·검증 비용은 미측정 | 초기 DB/계약 비용 증가, 이후 중복 기록 감소 가설 |

선택:

- **Newgame 운영을 당장 유지·개선하는 목적**: Newgame이 더 최적화되어 있다. 동작하는 특화 도구를 문서형 코어로 대체할 이유가 없다.
- **새 프로젝트들에 설치하는 범용 CLI 제품**: Evolutionary의 권위·증거·안정성 원칙을 기반으로 이 RFC의 계약을 구현하는 방향이 더 적합하다. 현행 Evolutionary 자체의 완성도 우위는 아니다.
- **현재 바로 배포 가능한 범용 제품**: 둘 다 입증되지 않았다. Newgame은 특화 시스템, Evolutionary는 설계 seed다.
- **권고**: Newgame을 운영 기준·회귀 fixture 제공자로 두고 Evolutionary에서 local-only MVP를 별도 검증한다. V3/V4 자율 승격·다중 장치 동기화·외부 deploy는 뒤로 미룬다.

## 13. 구현 전에 승인할 수락 게이트와 순서

| 단계 | 검토할 구체 결과 | machine gate | human gate |
|---|---|---|---|
| M0 RFC/계약 | 상태 축·authority·소유권·명령·버전 표 | 문서 참조·충돌·요구 추적 | RFC 선택, MVP 경계와 비용 수용 |
| M1 read-only core | schema, inspect/check/status/explain, legacy import 계획 | malformed/future/stale 입력 거부, deterministic replay, read의 파일·네트워크 mutation 0 | 상태가 업무 판단에 충분한지 |
| M2 local writer | transaction, receipt, projections, init/import | F01–F07/F11–F14; 충돌 요청 중 1회만 commit; 같은 key 재실행 업무 delta 0 | 기존 사용자 파일의 이관 정책 |
| M3 migration/recovery | snapshot·restore·release rollback | F10/F12, 신규 history 보존, 이전 reader 호환 또는 명시적 차단 | 복구 범위·보존 기간 |
| M4 Newgame adapter pilot | legacy 상태·source hash·artifact/test 연계 | 원본 Newgame 쓰기 0, 기존 검사 결과 보존, 지원 환경에서 contract test | 오너 판단과 게임 수락 유지 |
| 이후 외부 effects | provider adapter와 reconciliation | F08/F09 포함 장애 주입; 불명 결과의 중복 dispatch 0 | 별도 외부 side-effect 권한 |

모든 machine gate는 테스트 대상 소스/데이터·runtime·rules·시험 정의 digest와 실행 결과를 남긴다. mock 성공을 live 검증으로 승격하지 않는다. full regression은 그래프 기반 선택 누락을 검출하기 위해 별도로 유지한다.

최적화 비교 실험은 같은 고정 소스·작업 묶음(새 요구 등록, dirty CSV 변경, 실패 재시도, 오래된 증거 조회, 복구)을 Newgame 현행 절차와 MVP에서 수행한다. false_verified 수, duplicate effect 수, 사용자 소유 파일 변경 수는 0이 필수다. p50/p95 처리 시간, peak memory, 읽은 파일/bytes, 명령 수, 수동 상태 수정 횟수, 복구 시간은 같은 장치·cold/warm·반복 횟수를 명시하여 측정한다. 시간·비용 우위의 임계값은 측정 전에 오너가 정한다. 이 감사에는 해당 benchmark 수치가 없다.

## 14. 하네스 개선 후보와 미확인 사항

- `HARNESS-REQ-20260913-001` (project, candidate): capability 선언에 version-bound eval evidence를 요구한다. EH-01의 구조적 자기 모순을 근거로 등록하며 manifest 변경은 제안에 그친다.
- `HARNESS-REQ-20260913-002` (project, candidate): CLI 제품 출시 전에 schema/state/ownership/transaction/compatibility/rollback/idempotency 계약을 gate로 묶는다. EH-02~11와 P01/P02의 전이 위험을 근거로 한다.
- 기본 Python에 yaml이 없어 기존 venv로 검사한 것은 환경 마찰 1건이다. 반복 장애로 포장하거나 설치 정책을 자동 개정하지 않는다.
- 전체 게임 E2E, 라이브 CI/배포, 강제 종료·전원 장애, 실제 provider timeout, 다중 writer stress, CLI 성능은 미검증이다.
- Evolutionary의 Git 부재 때문에 감사 버전은 파일 manifest hash에 묶었다. Git 초기화·commit/push/merge·deploy는 하지 않는다.
- 새 제품이 다른 프로젝트·도메인에서도 타당하다는 승격 증거는 없다. Newgame 한 사례로 core promotion을 승인하지 않는다.
- 다음 허용 동작은 RFC 검토와 수정이다. 구현은 별도의 명시적 요청과 버전 결합 수락 계약 이후다.

## 15. 로컬 근거 색인

아래 line은 감사 baseline 기준이다. 새 내용이 들어간 뒤에는 baseline hash와 함께 확인한다.

| Ref | 파일 / 핵심 위치 |
|---|---|
| E1 | [AGENTS.md](C:/Users/uyess/Desktop/codex_evolutionary_harness/AGENTS.md), [README](C:/Users/uyess/Desktop/codex_evolutionary_harness/docs/harness/README.md) |
| E2 | [object example](C:/Users/uyess/Desktop/codex_evolutionary_harness/docs/harness/schemas/object.schema.example.json), [event example](C:/Users/uyess/Desktop/codex_evolutionary_harness/docs/harness/schemas/event.schema.example.json), [evidence example](C:/Users/uyess/Desktop/codex_evolutionary_harness/docs/harness/schemas/evidence.schema.example.json), [relation example](C:/Users/uyess/Desktop/codex_evolutionary_harness/docs/harness/schemas/relation.schema.example.json), [harness change example](C:/Users/uyess/Desktop/codex_evolutionary_harness/docs/harness/schemas/harness-change.schema.example.json) |
| E3 | [release manifest](C:/Users/uyess/Desktop/codex_evolutionary_harness/docs/harness/releases/current-harness.json:3); 최초 빈 records는 baseline 참조 |
| E4 | [state rules](C:/Users/uyess/Desktop/codex_evolutionary_harness/docs/harness/state-rules.md), [test map](C:/Users/uyess/Desktop/codex_evolutionary_harness/docs/harness/test-map.md) |
| E5 | [source authority](C:/Users/uyess/Desktop/codex_evolutionary_harness/docs/harness/source-authority.md) |
| E6 | [policy](C:/Users/uyess/Desktop/codex_evolutionary_harness/docs/harness/policy.md) |
| E7 | [promotion](C:/Users/uyess/Desktop/codex_evolutionary_harness/docs/harness/evolution/promotion-policy.md), [stability](C:/Users/uyess/Desktop/codex_evolutionary_harness/docs/harness/evolution/stability-anchors.md), [eval](C:/Users/uyess/Desktop/codex_evolutionary_harness/docs/harness/evals/README.md) |
| N1 | [ontology 설명](C:/Users/uyess/Desktop/Newgame/docs/architecture/project-ontology.md), [registry 상태](C:/Users/uyess/Desktop/Newgame/docs/assets/owner-decision-registry.json:46) |
| N2 | [milestone 변환](C:/Users/uyess/Desktop/Newgame/scripts/generate_project_ontology.py:54), [freshness](C:/Users/uyess/Desktop/Newgame/scripts/generate_project_ontology.py:171), [관계 검사](C:/Users/uyess/Desktop/Newgame/scripts/generate_project_ontology.py:374), [version 전달](C:/Users/uyess/Desktop/Newgame/scripts/generate_project_ontology.py:435), [check/write](C:/Users/uyess/Desktop/Newgame/scripts/generate_project_ontology.py:507) |
| N3 | [wrapper](C:/Users/uyess/Desktop/Newgame/scripts/check-project-ontology.ps1:39) |
| N4 | [Notion 대조](C:/Users/uyess/Desktop/Newgame/scripts/check_notion_audit.py:16) |
| N5 | [CI transport](C:/Users/uyess/Desktop/Newgame/scripts/ci_transfer.py:49), [CI proof](C:/Users/uyess/Desktop/Newgame/scripts/ci_budget.py:41) |
| N6 | [release identity](C:/Users/uyess/Desktop/Newgame/scripts/release_state.py:9) |
| N7 | [배포 workflow](C:/Users/uyess/Desktop/Newgame/.github/workflows/deploy-wiki.yml:729), [rollback](C:/Users/uyess/Desktop/Newgame/.github/workflows/deploy-wiki.yml:888) |
| N8 | [asset upload](C:/Users/uyess/Desktop/Newgame/scripts/deploy_cloudflare_assets.py:106), [retention](C:/Users/uyess/Desktop/Newgame/scripts/prune_windows_releases.py:119) |
| N9 | [main 복구 PR](C:/Users/uyess/Desktop/Newgame/.github/workflows/restore-main.yml) |
| N10 | [release tests](C:/Users/uyess/Desktop/Newgame/scripts/test_cloudflare_release.py), [retention tests](C:/Users/uyess/Desktop/Newgame/scripts/test_windows_release_retention.py), [Newgame 정책](C:/Users/uyess/Desktop/Newgame/AGENTS.md) |

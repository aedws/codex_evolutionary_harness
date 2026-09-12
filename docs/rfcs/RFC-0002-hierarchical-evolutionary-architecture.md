# RFC-0002 — 계층적 진화형 하네스 상위 아키텍처

- 상태: seed baseline design; 사용자 목표는 확인됨. 아키텍처 전 기능의 구현·검증·인간 수락 선언은 아님.
- 기준: [REQ-HARNESS-VISION-001과 G01–G17](../requirements/HARNESS-GOALS.md)
- 이번 산출물: contract seed v0.2.0 / contract 2. V2/V3/V4와 배포 SemVer를 구분한다.
- 범위: 공통 seed 설계, 최초 project 검증. 여러 프로젝트·도메인에서 검증된 core 승격으로 표현하지 않는다.
- 하위 문서: [RFC-0001 CLI 제품 계약](RFC-0001-evolutionary-harness-cli.md). 그 문서의 DB·단일 writer·명령 이름은 후속 제안이며 이번 씨앗의 필수 구현이 아니다.

## 1. 목적과 경계

목적은 프로젝트마다 하네스를 새로 만드는 비용을 줄이면서 실제 운영에서 얻은 개선을 검증 가능한 공통 규격으로 축적하는 것이다. CLI, 위키, 에이전트는 같은 계약을 쓰는 인터페이스와 실행 주체다. 어떤 하나도 상태의 최종 진실이 아니다.

씨앗은 신뢰 규칙과 빈 기록을 제공한다. AI가 문서를 지킨다는 기대만으로 강제 보장이 생기지는 않는다. 실제 정책 집행, 결정적 reducer, sandbox와 canary controller는 후속 구현이며 능력 manifest에 미구현으로 표시한다.

## 2. 계층과 의존 방향

| 계층 | 책임 | 읽는 것 / 만드는 것 |
|---|---|---|
| Reality & source adapters | 코드·CSV·테스트·실행·배포·인간 결정을 관측 | 권위 원본 → 버전 결합 snapshot/evidence |
| DOP records | 사건·증거·실행·관계·정책·평가 저장 | provenance, identity, immutable raw refs |
| Derivation | 명시적 규칙으로 상태와 영향 계산 | evidence+rule version → 상태·사유·unknown/conflict |
| OOP View | 사람이 목적·책임·관계·다음 행동을 이해 | 파생 상태와 원본 설명 → 위키·객체 탐색·CLI 조회 |
| Action & policy | 사람/AI의 요청을 권한·입력·부작용 범위로 제한 | 명시적 command → execution·effect·receipt |
| Evolution control | 마찰을 후보로 만들고 평가·승격·전파 | HarnessReq/Change/Eval/Compatibility/Release/Rollout |

관측의 흐름은 Reality → Evidence/Event → Derived Projection → OOP View다. 행동의 흐름은 Human/Agent → 객체 행동 요청 → Policy → Execution → Reality다. View 상태를 직접 바꿔 현실이 바뀐 것으로 처리하지 않는다.

## 3. OOP View: Newgame 위키 전체를 참고하는 표면

| 객체 | 사람이 알아야 하는 것 | DOP에서 가져오는 것 |
|---|---|---|
| Requirement | 목적·범위·수락 조건·출처 | intent authority, acceptance class, supersession |
| Task | 할 일·책임·선행 조건·다음 행동 | execution, change snapshot, verification, blocker |
| Decision | 대안·판단자·결정 이유·적용 범위 | explicit human/source record, effective version |
| Module | 공개 계약·의존·교체/제거 방법 | relation provenance, black-box contract, impact |
| Test | 검증 대상·방법·최근 결과·공백 | definition+run+target digest+evidence |
| Release | 포함 변경·아티팩트·적용 환경·복구 | release identity, deployment observation, rollback lineage |

위키의 전체 문서 구조, 기능 설명, 객체 탐색, 관계 양방향 조회, 검색, 역할별 작업 흐름이 참조 범위다. 모든 문장을 자동 생성할 필요는 없다. 수동 설명·의도·인간 판단과 파생 상태 표시의 소유권을 구분한다.

상태를 보여주는 모든 표면은 `as_of`, 대상 버전, rule version, 근거 링크, blocker/unknown, 다음 허용 행동을 설명할 수 있어야 한다. 사용자는 상세 그래프를 항상 읽지 않고도 목적과 행동을 이해할 수 있어야 한다. 이번 씨앗에서는 Markdown checkpoint가 최소 View이며 완성 위키 UI는 제공하지 않는다.

## 4. DOP와 신뢰 계약

공통 레코드는 stable ID, record type/version, subject, execution, source refs, observation time, 적용 snapshot을 가진다. 구체적인 최소 필드는 [seed contract](../../seed/docs/harness/contract.md)가 정한다.

정상 상태에는 unknown/unverified/stale/conflicted/blocked가 포함된다. 인간 수락과 기계 검증을 합치지 않는다. task가 passed여도 새로운 데이터 버전에 대한 검증은 stale일 수 있고, 과거 deployment 사실은 보존한다.

같은 source snapshot·evidence watermark·rule version·명시적 evaluation time은 같은 결과를 내야 한다. 반대 증거·늦게 온 실패·철회·권한 충돌을 삭제하지 않는다. 최신성은 단순 파일 수정 시각이 아니라 관측 시간·원본 revision·유효성 조건으로 판단한다.

새 snapshot마다 프로젝트 전체를 무조건 읽을 필요는 없다. 필요한 subgraph와 영향 범위를 선택하되, 영향이 불명확하면 보수적 검사와 unknown을 선택한다. 테스트 파일 존재와 실행 통과를 구별한다.

## 5. 검증 가능한 블랙박스

Module, Tool, Agent, 외부 API는 내부 구현을 전부 이해하지 않아도 사용할 수 있다. 대신 다음을 선언한다.

1. 입력 schema·전제 조건·고정된 입력 digest.
2. 출력 schema·관측 가능한 상태 변화·postcondition.
3. 부작용 target·권한·idempotency key와 조회 방법.
4. timeout·실패 분류·불명 효과·재시도/보상 경계.
5. 검증 정의·실행 환경·증거 위치·관측하지 못한 범위.

내부 설명이 설득력 있다는 이유로 테스트를 생략하지 않는다. 외부 성공 응답이 없다고 효과도 없었다고 추정하지 않는다. SDK·에이전트가 바뀌면 공개 계약과 증거의 호환성을 다시 검사한다.

## 6. Core / Domain / Project Overlay

Core는 공통 identity, evidence/provenance, state derivation interface, policy boundary, eval/promotion/rollback 계약을 소유한다. Domain은 특정 분야의 반복 규칙·도구·평가를, Project는 현재 프로젝트의 원본·필수 검사·도구 바인딩·수락 조건을 추가한다.

Overlay는 `id, version, scope, base_contract_version, source_refs, additions, restrictions, eval_refs, compatibility_refs`를 선언한다. 프로젝트 설정은 프로젝트가 소유하고 업스트림 core 파일을 몰래 수정해 별도 포크로 운영하지 않는다. 공통 계약 변경은 후보와 릴리스로 올린다.

조합 순서는 Core → 선택된 Domain → Project다. 의미 충돌은 last-write-wins가 아니라 conflict다. 하위 정책은 상위 권한을 자동 확대하지 않는다. root authority·파괴적 권한·credential·증거 보존·eval 무결성·human boundary·rollback 제거는 명시적 인간 판단 대상이다.

버전은 고정한다. 새 Core를 내려받았다고 프로젝트에 자동 적용하지 않는다. seed의 `overlays/project.json`은 미설정 상태로 시작하며 도메인·실행 환경을 추정해 채우지 않는다. adapter는 외부 시스템의 연결 구현이고 overlay는 규칙 조합이므로 서로 대체하지 않는다.

## 7. 하네스 자체의 개발 루프

```text
Failure/Friction + version-bound evidence
  → classification → HARNESS-REQ candidate
  → HarnessChange (scope, assumptions, expected improvement)
  → isolated sandbox + baseline comparison
  → Eval + compatibility + rollback evidence
  → authorized promotion/rejection
  → HarnessRelease + rollout observations
```

후보에는 원인 가설, 실제 문제 refs, 영향 범위, 기존 규칙과의 차이, 복잡도 비용, 반례, 예상 이익, 평가·복구 계획을 포함한다. 단발성 마찰은 기록하되 반복·구조적 일반성·심각성 근거 없이 규칙을 늘리지 않는다.

평가는 task correctness뿐 아니라 false verified, stale evidence 사용, missed tests/relations, duplicate effects, 수동 개입, context 양, 규칙 수, 유지 비용을 비교한다. 신뢰가 떨어졌는데 빠르다는 이유로 개선을 승인하지 않는다. 같은 신뢰도로 규칙과 context를 줄이는 변경도 승격할 수 있다.

## 8. 상향 승격

| 이동 | 필요한 증거 | 결정 |
|---|---|---|
| 실행 로컬 → Project | 문제와 원인의 연결, local eval, 회귀·rollback | 허가된 저위험 범위만 적용; 그 밖은 검토 |
| Project → Domain | 같은 도메인 2개 이상 프로젝트에서 유사 원인, 프로젝트 전제 제거, domain eval | domain maintainer의 권한 있는 결정 |
| Domain → Core | 여러 도메인에서 공통 원인, domain 의미 제거, core 회귀·호환·복구, 복잡도 평가 | core maintainer의 권한 있는 결정 |

프로젝트 수만 채운 것으로 충분하지 않다. 결과를 재현할 수 있는 입력·조건·실패 반례와 독립된 적용 증거를 확인한다. AI의 후보 생성·sandbox 실행 권한과 위험 변경 승인 권한을 분리한다. 평가를 수행한 AI의 서술만으로 승격하지 않는다. 이번 최초 코어 씨앗은 디자인 출발점이며 이 승격 게이트를 통과했다고 주장하지 않는다.

## 9. 하향 전파와 Canary

새 release는 immutable digest, 적용 가능한 base/overlay versions, 변경 범위, evidence/eval/compatibility refs, migration과 rollback target을 선언한다.

`candidate → compatibility_checked → canary → expanded → adopted`를 기본 흐름으로 두고 `pinned/blocked/aborted/rolled_back`을 별도로 보존한다. 이 값들은 rollout record의 관측·결정에서 생성되어야 한다.

Canary 계획에는 대상과 제외 이유, baseline, 기간/작업 수, 신뢰·비용 metric, 중단 threshold, 책임자, 확대 조건, 복구 대상이 필요하다. threshold는 실행 전에 고정한다. 증거 부족은 확대 승인이 아니다. 새 core가 실행 중인 task·새 event의 형식과 충돌하면 pin 또는 block한다.

## 10. 최소 씨앗과 파일 소유권

| 구성 | 배포/소유 계약 |
|---|---|
| `seed/AGENTS.md`, `seed/BOOTSTRAP_PROMPT.md` | 기본 행동·첫 읽기. 기존 프로젝트 동명 파일에 자동 덮어쓰기 금지 |
| `seed/docs/harness/contract.md`, source-authority, policy | 공통 core 계약. 변경은 후보/새 seed release로 관리 |
| 객체·관계·이벤트·checkpoint | 설치 시 빈 project 기록. 이후 대상 프로젝트가 소유 |
| overlays | 프로젝트 특화. upgrade 때 보존 |
| release manifest | seed 배포 version과 목표 capabilities를 구분 |
| `seed-manifest.json` | 배포 원본 파일 allowlist와 SHA-256. 수신 프로젝트의 최신 증거가 아님 |
| `.harness-seed.json` | 설치 영수증. 공급된 버전·파일 해시만 증명하며 task verified를 만들지 않음 |

원본 저장소의 audit evidence, 과거 Task/Execution, Newgame 파일, 계정·경로는 seed에 포함하지 않는다. GitHub 전체 저장소 템플릿 복제는 개발 기록까지 복사하므로 권장 설치 경로로 제공하지 않는다. 버전 고정 clone 후 seed 유틸리티 또는 seed-only ZIP을 사용한다.

## 11. 버전·재시도·복구의 씨앗 범위

배포 SemVer와 contract_version, V2/V3/V4 capability level을 분리한다. 현행 v0.2.0의 contract_version은 2이며 자동 강제 능력은 없다. unsupported manifest/version은 복사 전에 거부한다.

init는 전체 사전 점검 후 allowlist 파일만 신규 생성한다. 기존 대상 파일은 덮지 않는다. 같은 요청은 설치 영수증과 원본 파일 해시가 모두 일치할 때만 no-op이다. 부분 설치나 이후 프로젝트 변경은 conflict로 표시하고 재설치로 지우지 않는다. dry-run은 쓰기를 하지 않는다. 복사 중 OS 장애는 부분 상태로 명시하며 디렉터리 전체를 삭제하는 자동 rollback은 제공하지 않는다.

새 프로젝트에서 잘못 설치했다면, 사용 전이며 영수증 해시와 일치하는 생성 파일만 검토하여 제거한다. 실제 기록이 생겼으면 snapshot을 보존하고 migration/revert 계획을 만든다. upgrade는 새 버전 별도 checkout → diff → project/overlay/evidence 보존 → 평가 → 명시적 적용이다. 전체 runtime의 트랜잭션·분산 idempotency·migration/rollback 설계는 RFC-0001의 후속 과제다.

## 12. 단계와 수락 기준

| 단계 | 제공 | 증거 기준 |
|---|---|---|
| Seed (이번) | 목표·아키텍처·최소 계약·빈 기록·private 배포·복사 도구 | 출처·17원칙 연결, seed 오염 없음, 해시, dry-run/충돌/no-op/부분 실패 검증, clone 재사용 |
| V2 | 실제 validator/reducer/policy hooks·version-bound evidence | false verification 방지·재생·권한·복구의 실행 증거 |
| V3 | 프로젝트 마찰 집계·후보·sandbox 평가 | baseline 대비 신뢰/개입/복잡도 개선과 안전한 local 적용 |
| V4 | cross-project/domain 승격과 Canary 전파 | 독립 적용 증거, 호환성·중단·회수·rollback 검증 |

V3/V4의 자동 실행은 나중에 구현하지만 관련 레코드의 ID·scope·출처·버전·평가·복구 연결은 지금 계약에 남긴다. 이번 배포로 V2 이상을 verified로 올리지 않는다.

## 13. 인터뷰와 남은 선택

이미 명시된 목표와 private 배포 권한은 재질문하지 않는다. 대상 프로젝트의 원본 권위·필수 검사·도메인·기존 AGENTS 충돌은 bootstrap 때 필요한 범위만 묻는다. 실제 runtime DB, wiki 구현, 자동 승격 범위, Canary 수치·기간은 후속 구현 시 결정하며 이번 씨앗이 임의로 확정하지 않는다.

## 14. 목표와 운영 계약의 연결

상위 설계의 원칙을 실행 시 판단 가능한 의무로 구체화한 규범 원본은 `seed/docs/harness/contracts/`다. 이 RFC는 책임·구조를 정의하고 세부 조항을 연결한다. RFC-0001의 명령/저장 구현 제안은 이 구조와 호환되어야 한다. 문서끼리 충돌하면 임의의 최신 문장을 선택하지 말고 사용자 목표·원본 권위에 따라 Decision으로 해소한다.

| 보완 영역 | 구체화한 계약 | 연결 목표 |
|---|---|---|
| 전체 위키 객체 표면 | 수동/생성 필드 소유권, 상태의 이유·버전·접근 가능한 표시, 객체 행동 입력 | G01/G04: V01–V02 |
| 파생 상태·관계·컨텍스트 | 결정적 입력 묶음, 실패/진행 중 시도, 테스트 정의와 Run 분리, 관계 불확실성, 재개 시 최신성 | G02–G07/G15: V03–V05 |
| 증거와 실행의 소유권 | dirty/data/tool/skill 버전, 단일 writer, 부분 쓰기, 증거 보존과 경로 경계 | G02/G10/G12: X01 |
| 행동 권한·블랙박스 | actor/target/effect 계약, 승인 범위, 정책 집행 수준, tool/skill 교체 검증 | G06/G11–G13/G16: X02–X03 |
| 재시도·복구 | logical operation key와 payload, 불명 효과, bounded retry, 이후 기록을 보존하는 복구 | G05/G12/G17: X04–X05 |
| 오류·스킬 피드백 | 작업 경계 검토, 사용 단계·소유권·의존 파일 digest, 분류·후보 중복 방지 | G06/G10/G14/G15: F01–F04 |
| 상향 전송과 씨앗 반영 | 최소 공유 묶음, exact export 권한, 제출/승격 분리, 원 프로젝트 효과 관측 | G10/G14: F05–F07 |
| 계층과 버전 | pin된 effective overlay, 확장 충돌, 읽기 호환, reviewed migration | G08/G14: E01/E05 |
| 평가·승격·단순화 | frozen grader와 반례, 독립성, 신뢰 하한, 복잡도 비용, 유지보수와 경험적 승격 구분 | G09–G12/G15/G17: E02–E03 |
| 하향 배포와 능력 주장 | 사전 canary 중단 조건, 회수 실패, 인간 수락, 문서/구현/관측 능력 구분 | G10/G12/G14/G16/G17: E04–E06 |

표는 영역 탐색용이다. 정확한 G01–G17의 개별 연결과 수락 시나리오는 [coverage.json](../../seed/docs/harness/contracts/coverage.json)에 둔다. 모든 23개 세부 조항이 적어도 한 목표에 연결된다. `scripts/check_contracts.py`는 연결·배포 기본값만 검사하며 시나리오의 실행 결과를 만들지 않는다. 모든 runtime 시나리오는 현재 planned_not_executed다.

- [객체·파생 상태·관계·컨텍스트 V01–V05](../../seed/docs/harness/contracts/views-state.md)
- [실행·권한·증거·복구 X01–X05](../../seed/docs/harness/contracts/execution.md)
- [자가피드백·스킬 F01–F07](../../seed/docs/harness/contracts/feedback.md)
- [호환·평가·승격·하향 전파 E01–E06](../../seed/docs/harness/contracts/evolution.md)

## 15. 닫힌 자가피드백 루프와 기본값

```text
Project error fix / skill observation
 → bounded task-boundary review → classify / no_candidate
 → stable candidate + baseline/candidate eval
 → exact authorized sanitized submission
 → upstream intake → scoped decision → immutable seed release
 → pinned Project → compatibility / recovery / canary where applicable
 → explicit adoption → observe original failure and cost again
 → linked follow-up / regression / rollback candidate
```

절차와 대안 비교는 [RFC-0003](RFC-0003-feedback-common-contract.md)에 정의한다. 후보를 받아 두는 것과 배포 seed를 바꾸는 것은 별도 행동이다. submit, export, merge, release, adopt의 권한을 분리하며 새 프로젝트의 설정에는 어떤 외부 권한도 상속하지 않는다. private 저장소 접근 가능성만으로 다른 프로젝트의 자료를 전송하지 않는다.

자동 hook이 없는 씨앗에서는 AGENTS의 작업 종료 의무와 사람이 실행 가능한 기록 절차로 시작한다. 스킬은 그 방법을 도울 수 있지만 호출 여부를 보장하는 실행 엔진이 아니다. 실제 hook/collector/submitter는 후속 V2/V3 기능이다. 이미 승인된 로컬 개선과 후보 준비는 불필요한 인터뷰 없이 진행하며, 필요한 외부 경계가 미정일 때만 묻는다.

이번 contract 2는 사용자가 요청한 설계 공백의 유지보수 릴리스다. 교차 도메인 운영에서 검증된 Core 승격이나 성능 최적화 완료로 주장하지 않는다. 모든 목표에 계약과 수락 시나리오를 연결했지만, 알려지지 않은 운영 failure mode까지 완전히 열거했다는 주장은 하지 않는다.

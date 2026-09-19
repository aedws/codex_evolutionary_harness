# RFC-0016 — 고정 V2에서 평가된 프로젝트 V3로

- 요청: 2026-09-16 `정리.txt` 아이디어를 기준으로 씨앗 자체를 처음부터 재작성.
- Task: TASK-20260916-V2-REWRITE-001 / EXE-20260916-V2-REWRITE-001.
- 범위: 새로운 로컬 씨앗·고정 실행기·CLI·객체 위키·회귀 평가. 현 제품 도입·원격 배포·유료 호출 없음.
- 위치: 새 기본 배포는 `seed/`. v0.12는 `legacy/v0.12.0/`에 그대로 보존. 과거 설계 문맥에서 사용한 V2/V3 capability 명칭과 아래 새 운용 단계를 구분한다.

## 1. 목표와 바뀐 기준

V2는 프로젝트마다 같은 Markdown을 읽고 실행기를 새로 만드는 방식이 아니다. 객체·증거·이벤트 규격, 상태 판정, 역할 경계, 준비 판정, 후보 비교, 채택·복구가 **동일한 배포 실행 파일**이다. 프로젝트는 원본과 검사 어댑터만 연결한다.

V3는 끝없는 규칙 변경이 아니라 현재 프로젝트·사용자·모델·평가 조건에서 채택한 **고정 운용 구성**이다. 전역 최적해/일반화된 코어가 아니다. 현재 목표의 실행 순서는 다음과 같다.

```text
고정 V2 → 기본 개발·제품 흐름 → 관측 기록
                         ↓ 작업 경계 판정
                   탐색 준비 이벤트
                         ↓ 예산 내 후보
                 활성 구성과 격리된 후보
                         ↓ 동일 기준 비교
                  evaluator의 평가 근거
                         ↓ owner의 결정
                     고정된 V3
```

V3 조건을 못 채우면 V2에서 계속한다. 이 경로는 오류가 아니다. 이전 RFC-0015의 전체 Newgame/외부 연동 동등성 계획은 삭제하지 않고 후속 확장 참고로 유지한다. 새 씨앗에 그 계획의 미구현 기능이 있다고 주장하지 않는다.

## 2. 고정 경계

배포: `2.0.0-dev.1`; ledger schema: 2; contract: fixed-v2-1. 각 Task가 config ID를 가진다. init은 엔진 hash, 원본 목록, 검사 adapter, 역할, eval suite, 후보 예산, 모델 조건을 고정한다. core drift는 실행을 차단한다.

명시적으로 바꿀 수 있는 것은 별칭·문맥 읽기 순서·결과 형식·모듈 탐색·체크리스트다. 이 값은 제안으로 전달되며 임의 코드를 실행하지 않는다. 권한·보존·검증 문턱·원본 권위·배포 승인은 고정 경계다. 새 core 버전은 별도 배포와 도입 평가를 요구한다.

파일 소유권은 배포/프로젝트/실행원장/파생위키로 나눈다. 설치 충돌은 사전 실패하며 덮어쓰기하지 않는다. 기존 v0.12 원장은 자동 이관하지 않고 새 경로에서 원본을 연결한다. 기존 증거와 진행 중 Task는 해당 버전에서 계속 조회한다.

## 3. DOP 원본과 OOP 투영

SQLite는 append-only 이벤트와 logical operation receipt를 저장한다. 이벤트는 sequence/previous hash/body hash로 연결된다. mutable 객체 상태를 저장해 완료를 주장하지 않는다. 입력 파일 hash와 실제 subprocess exit/output, 인간 MVP 결정, resume readback에서 상태를 계산한다.

6 OOP 객체는 Requirement/Task/Decision/Module/Test/Release다. 위키는 대문 → 주제 → 객체 상세로 탐색하며 상태 노드 아래 객체를 모은다. 객체 관계는 안정 ID로 연결되고 Run/Event/Observation/Eval은 상세의 근거로 둔다. 모든 Task 상태는 rule ID, Run ID, 입력 hash, 시작 config, event head를 설명한다. 생성 위키는 근거가 아니라 투영이며 수정/누락되면 탐색 준비를 차단한다.

unknown/unverified/stale/failed/interrupted와 인간 판단 대기를 정상으로 보여준다. Test 실행 pass는 제품 전체 수락이 아니다. 생성 위키 품질·사용자 흐름의 인간 판단도 자동 통과시키지 않는다.

## 4. 준비와 전환

준비 판정은 연결된 6개 객체 유형, 최신·현 버전의 실제 pass, owner의 기본 사용자 흐름 수락, 해당 Run의 재개 readback, 분류된 관측, 미해결 unknown 없음, 위키 무결성을 요구한다. 활성 구성이 바뀌면 새 active 구성에서 다시 실제 루프를 확인해야 다음 탐색이 가능하다.

체크포인트에서 조건을 검사하고 SpecializationReady를 기록한다. 자연어 “준비됐다”는 투영일 뿐이다. 조건 통과 시 관측에 들어 있는 허용 suggestion을 예산 내 후보로 정규화한다. LLM이 필요한 후보 작성은 외부에서 제안할 수 있지만 이 배포본은 임의 LLM 호출·자동 지출을 하지 않는다.

관측 분류: expression_preference / product_correctness / authority_violation / workflow_friction / skill_change / unknown. 오류와 권한 위반을 표현 취향으로 승격시키지 않는다. 스킬의 변경은 근거에 provenance를 남기고 core 변경은 별도 HARNESS-REQ로 다룬다.

## 5. 비교·채택·고정

평가 데이터는 init 때 고정한다. development/selection/holdout이 분리되며 동일 input/oracle 중복을 거절한다. 현재 내장 평가기는 command resolution을 비교한다. selection과 holdout 모두 개선, 고정 회귀/권한 사례 전수 통과, 기존 성공 손실 0, 구성 크기 상한 이내여야 평가 통과다. 출력 형식/문맥 순서의 효과를 실제 LLM 품질로 대신 점수화하지 않는다.

후보는 baseline ID, adoption epoch, 입력 hash, suite hash, observation에 귀속한다. evaluator label만 평가하고 owner label만 명시 결정을 기록해 채택한다. 세 label은 서로 다르지만 로컬 OS 사용자가 호출하는 **운영 역할 표시**이며 독립 인간 인증은 아니다. 고위험 외부 효과 명령은 제공하지 않는다.

채택 시 새 immutable V3 config를 만들고 active pointer만 바꾼다. 진행 중 Task는 기존 config를 유지한다. 이후 새 후보를 만들 때도 기존 V3는 바꾸지 않는다. rollback 역시 future-task pointer만 복귀한다. 제품 파일이나 외부 효과가 자동 rollback되었다고 주장하지 않는다. active가 원상복귀해도 epoch가 달라 오래된 후보는 다시 사용할 수 없다.

## 6. 실패와 재시도

SQLite write transaction이 동일 operation key의 중복 실행을 막는다. Run 예약을 먼저 commit하고 subprocess를 실행한다. 중단 후 receipt가 없으면 unknown으로 남겨 재실행을 거절한다. 실제 프로세스 정지/외부 영향 확인 후 owner가 interrupted로 reconcile해야 새 operation key로 실행할 수 있다. 이를 pass로 바꾸지 않는다.

엔진 변경, 입력 변경, 새 실패, eval 재실행, 예산 소진, 권한 위반, 설치 충돌, 위키 사용자 수정, chain 손상은 각기 거절/미검증으로 남긴다. 파생 위키 실패는 원장 기록과 분리해 경고하고 재생성한다. 렌더 lock 중단은 정지 확인 뒤 lock을 보존/이동해 복구한다. 원장 backup/새 경로 restore로 데이터 회복 경로를 둔다.

## 7. 검증 전략과 남는 한계

1. 같은 정규화 입력·이벤트·규칙에서 상태 동일.
2. 불허 필드/원본 경로/권한/고정 oracle 변경은 거절.
3. 등록→실제 검사→관측→resume→MVP→checkpoint→candidate→eval→adopt 경로를 설치된 CLI로 실행.
4. 고정 V3의 동일 요청 반복 결과와 in-flight V2 유지.
5. 독립 새 V2 인스턴스 3개에서 동일 고정 탐색 절차를 반복해 계약 준수 V3 도달.
6. 실패·중단·경합·입력 drift·ABA rollback·위키 충돌·원장 손상·backup/restore 회귀.

5번은 합성 사례의 고정 탐색 재현이다. 실제 사용자·모델로 독립 특화 시도가 반복 성공한다는 증거는 아니다. 실제 산출물 품질, 전체 Newgame 동등성, OS sandbox, 인증된 평가자 분리, 외부 배포/Canary, 도메인·코어 일반화는 여전히 미검증/후속 범위다. 문서에 프레임워크 사례가 있어도 LangGraph/DSPy 도입 의무로 해석하지 않는다.

## 8. 선택 근거

기존 씨앗은 다양한 Newgame 기능 대응에 유리했지만 계약/실행기가 누적되어 출발점과 특화 종료점이 흐려졌다. 새 씨앗은 **작은 고정 실행 규격과 명확한 전환**에 집중한다. 대신 기존 원격 어댑터·복잡한 문서 import 등은 새 기본 경로에 포함하지 않는다. 과거 기능을 삭제된 것처럼 숨기지 않고 legacy로 분리했다. 두 구현의 파일 수 감소는 범위 차이가 있으므로 동일 품질 최적화의 증거로 사용하지 않는다.

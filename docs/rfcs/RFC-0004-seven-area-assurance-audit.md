# RFC-0004 — 일곱 상위 계약 재감사와 contract 3 보완

- 기준: 사용자 지정 일곱 영역, v0.2.0 / contract 2, commit `880c144`에서 시작한 별도 실행.
- Task / Execution: TASK-20260913-ASSURANCE-001 / EXE-20260913-ASSURANCE-001.
- 판단: 일곱 영역 모두 원칙은 존재했으나 운영 판단을 재현하기 위한 세부 의무가 부분적으로 부족했다. 이전의 17목표·23조항 연결 검사는 이 의미적 충분성을 증명하지 않았다.
- 변경 범위: 계약·기록 형식·오프라인 배포 검사. 전체 위키/정책/reducer/rollout 구현은 포함하지 않는다.

## 1. Newgame 참조 범위와 경계

Newgame의 `mkdocs.yml` 전체 내비게이션 105개 항목과 Markdown 문서 105개 파일을 대조했다. 참조 경로 누락은 없었다. `knowledge-map.json`의 전체 분류/그룹 구조와 온톨로지·검색·위키 협업·역할 인증 문서를 읽어 문서 탐색과 운영 객체가 만나는 구조를 확인했다. 각 문서의 모든 본문을 정독하거나 배포 UI를 실행 검증한 것은 아니다.

참조한 구조는 문서 중심 개요→주제→상세, 상·하위/관련 링크, 선택적 그래프, 역할별 작업실, 객체의 목적·수락·다음 행동, 양방향 관계·근거·최신성, 서버의 읽기 권한 경계다. 온톨로지 콘솔 하나로 전체 위키를 대표하지 않았다. 프로젝트의 게임 규칙, 계정, 외부 원본과 상시 권한은 씨앗에 이식하지 않는다.

원본 버전과 파일 digest, 인벤토리 및 한계는 [Newgame 구조 관측](../harness/evidence/EXE-20260913-ASSURANCE-001/newgame-structure.json)에 남겼다. 이는 정적 분석이며 실행 사실을 독립적으로 확증하지 않는다.

## 2. 일곱 항목의 전후 판단

| 항목 | contract 2에 있던 내용 | 부족했던 판정 계약 | contract 3 보완 / 조항 |
|---|---|---|---|
| 위키 전체의 객체 탐색 | 위키 영역, 목적·관계·다음 행동, 수동/생성 구분 | 전체 문서 분모, 상·하위 복귀, 스크립트 실패 대안, 역할별 탐색 및 색인/그래프 유출 | inventory·포함/제외·문서/묶음/원본/역할 참조, purpose→object→relation→action→evidence 여정, 접근 통제: V01/V02 |
| View 생성 설명 | 대상 snapshot, rule version, evidence tuple | generator/template/유효 overlay 결합, 필드별 소유권, 기각된 증거, 같은 상태지만 규칙이 바뀐 경우 | View explanation manifest, claim별 input→rule 계보, output digest와 독립적 재생: V03 |
| 계층 조합과 pin | Core→Domain→Project, namespaced 확장, conflict | 여러 Domain의 순서/DAG, 타입별 merge 연산, 버전 범위 해소, 충돌 영수증 | immutable pin·확장 schema·per-key owner/operator, 교집합 권한/누적 거부·필수 검사, 미해결 조합 차단: E01 |
| 일반화·교차 평가 | 프로젝트/도메인 수, 가정·반례, 독립성 원칙 | 적용 predicate, 반증 조건, 공유 ancestry/fixture, holdout 오염, 실패한 적격 cohort | 인과 불변식→전제 제거/매개변수화→적용 조건→평가 matrix, 독립성/반례/실패 분모: E03 |
| Canary 확대·회수 | cohort·기간·작업수·threshold·rollback | 기간 AND 작업량, 저유량/지연 효과/관측 누락, 대표성·blast radius, release 철회와 프로젝트 복구 구분 | 사전 대상 선택·최소/최대 경계·결정표·응급 권한, 철회 후 프로젝트별 결과: E04 |
| 역할·실행 강제 | actor 권한, high-risk 자기승인 금지, enforcement 수준 | authenticated principal, evaluator write set, 직접 API/CLI 우회, 철회·payload 변동 재검사 | 제안/평가/승인/실행 write 경계·gate map·직접 거부 테스트; 미강제 시 보호된 자율 실행 차단: X02 |
| 신뢰 유지와 단순화 | 신뢰 gate, 비용/문맥/개입 지표 | 동일 workload 분모, 추정 불확실성·비열등 기준, 규칙 감추기·외부화 비용, 복합 tradeoff | 모든 시도/계층 결과, 규칙+본문량, 누적 context·사람 시간·이전/복구 비용, optimized/inconclusive 판정: E02 |

## 3. 서로 다른 계약의 충돌 검토

- View가 설명 가능하다는 주장도 권한 밖 원자료의 노출을 허용하지 않는다. 제한된 근거는 그 사용자에게 독립 확인 불가임을 표시한다.
- 하위 overlay는 권한을 자동 확대하지 않는다. 명시적 연산자 없는 값 충돌은 Domain 순서로 덮지 않는다.
- 두 프로젝트 또는 두 도메인이라는 수만 채워도 독립 평가가 되는 것은 아니다. 공유 ancestry·복제 fixtures·평가 권한의 겹침을 별도로 본다.
- Canary 시간이 지났거나 평균 비용이 좋아도 필수 관측량·개별 cohort·신뢰 gate가 미달이면 확대하지 않는다.
- release 철회는 태그 삭제나 모든 프로젝트의 복구 완료가 아니다. 도달하지 못한 프로젝트는 unknown으로 보존한다.
- 실행 강제가 없는 상태의 명시적 인간 감독 작업과, 강제가 검증된 자율 실행을 구분한다. 이미 유효한 사용자 권한을 템플릿 위치 때문에 재요청하지 않는다.
- 문서 보완 자체는 경험적 범용 승격이 아니다. 이번 릴리스는 사용자 요청에 따른 seed-maintenance이고 실제 성능 우위는 미측정이다.

## 4. 재사용·검사·수락

기존 23개 조항을 확장하여 규칙 ID 수를 늘리지 않았다. [7영역 검토 절차](../../seed/docs/harness/contracts/review-protocol.md), [빈 검토 패킷](../../seed/docs/harness/templates/assurance-review.example.json), [21개 계획 시나리오](../../seed/docs/harness/contracts/review-cases.json)를 추가했다. 평소 모든 영역을 로드하지 않고 관련 변경에서만 사용한다.

오프라인 검사는 일곱 영역 누락, 거부/판단 보류 시나리오 누락, 계획을 runtime 성공으로 바꾸는 오류, 템플릿에 이전 승인/관측을 상속하는 오류를 거부한다. 문장이나 빈 템플릿이 있다는 이유로 실제 정책·통계·UI·Canary가 검증된 것은 아니다. 최종 로컬/원격 검사 결과는 해당 실행 Evidence로 따로 기록한다.

새 필수 의미를 추가했으므로 distribution v0.3.0 / contract 3으로 배포한다. contract 1/2의 기존 프로젝트는 pin을 유지하고 필요한 지침·검토 레코드를 명시적으로 migration한다. 이미 존재하는 데이터와 이벤트에 새 필드를 만들어 사실인 것처럼 채우지 않는다.

## 5. 결론의 적용 범위

사용자가 지정한 일곱 항목에서 이번 정적 검토로 확인한 계약 공백은 문서·기록 의무·수락/반례 시나리오에 반영했다. 실제 사용성, 정책 차단, 독립 재생, 통계적 신뢰 유지, 안전한 Canary/복구는 여전히 구현과 운영 증거가 필요하다. 이를 숨기고 '일곱 기능 완전 검증'으로 표시하지 않는다.

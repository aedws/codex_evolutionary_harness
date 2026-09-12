# RFC-0005 — 전체 목표를 연결하는 판정 시스템

- Task / Execution: TASK-20260913-DECISION-001 / EXE-20260913-DECISION-001.
- 출발점: v0.3.0 / contract 3, README 사용법 개선까지 반영한 원본 snapshot.
- 범위: 현재 사용자 요청에 따른 전체 판정 계약 재검토와 구조 개선. 사용자는 인터뷰에서 **최소 실행 코어까지 구현하고 검증**하도록 명시적으로 승인했다.

## 1. 재감사 판단

감사 시작 시의 v0.3.0 씨앗은 범용적인 원칙·절차를 담지만, 입력 레코드에서 최종 판정까지 같은 결과를 재현할 공통 규격이 부족했다. 목표/조항/시나리오 목록이 온전한 것과 목적에 맞게 작동하는 시스템은 다르다. 따라서 단순한 문서 연결 검사를 '요구 목표를 달성할 수 있는 실행 구성'의 충분한 근거로 삼지 않는다.

| 공백 | 잘못된 판정 경로 | 개선 원칙 |
|---|---|---|
| 필수 입력/형식의 기계 계약 부족 | bool을 숫자 1로, NaN을 정상 수치로, 빈 배열을 전부 통과로 처리 | 엄격한 타입·단위·유효시간·필수 집합; unknown과 누락을 구별 |
| 복합 상태의 우선순위 부재 | 실패+stale+blocked에서 편리한 상태만 선택 | 독립 축 유지, 전체 reason set와 실행 허용 여부를 별도 계산 |
| evidence 진위와 파일 무결성 혼합 | JSON에 actor=human, passed라고 써서 승인/검증으로 인정 | 주장과 인증된 관측 분리; source adapter·producer·승인 경계를 명시 |
| overlay 권한 의미 모호 | 제한만 추가한 Domain을 빈 grant로 해석하여 전부 차단하거나 권한 확대 | 권한 원본과 restriction delta 분리; inherit/deny_all/unconfigured 구별 |
| 기록 간 referential/temporal 규칙 부족 | 다른 Task·acceptance·시도의 결과 또는 미래 관측을 재사용 | exact subject/target/acceptance/attempt/rule 결합, 무효화·철회 적용 |
| 단계별 의존성과 통과 기록 불명확 | 문서 평가 통과가 release/adopt/runtime 완료로 승격 | 고정된 gate graph와 단계별 증거·권한·후속 행동 |
| 평가 입력과 판정 입력 혼합 | 후보 작성자가 threshold/분모를 바꾸어 자기 통과 | 실행 전 고정된 profile과 원시 결과 분리, 모든 시도 보존 |
| 범용 운영 adapter 계약 불충분 | 특정 도구를 쓰면 관측·권한·복구가 자동 해결된 것으로 추정 | 소스/검사/권한/부작용 adapter별 경계·한계·conformance |
| 최종 목표의 완료 단위 부재 | 한 프로젝트·합성 설치 성공을 Core 진화 완료로 표시 | 능력별 구현/관측과 여러 실제 맥락의 효과를 따로 요구 |
| 자기평가의 무한 확장 가능성 | 피드백 검토를 개선하느라 매번 새 검토와 규칙 생성 | bounded review, 기존 후보 연결, 다음 실행으로 defer |

## 2. 공통 구조

```text
Authoritative source / tool observation / scoped human decision
  → typed immutable records + exact input snapshot
  → structural and semantic validation
  → pinned gate profile + source/authority resolution
  → independent state axes + complete reasons
  → eligible / blocked / unknown action decision
  → scoped executor or authorized manual action
  → readback / evidence / reconciliation
  → derived OOP View and feedback follow-up
```

관측을 파생시키는 경로와 외부 효과를 수행하는 경로는 별도 계약이다. 순수 판정기가 존재해도 임의 shell/API의 권한을 차단한다고 주장하지 않는다. 파일 digest가 같아도 관측 주체의 신뢰·권한이 성립하지 않으면 종속된 강한 주장은 보류한다.

## 3. 구현·이관 경계

기존 수동 JSON/JSONL과 감사 이력은 자동으로 새 인증된 원장에 이관하지 않는다. 과거 기록은 당시의 입력과 의미로 보존하고 필요한 범위만 legacy assertion 또는 확인된 관측으로 명시적으로 연결한다. 새 규격에서 필수인 actor/target/grade를 옛 자료에 추정해서 채우지 않는다.

정적 계약 검토, 실행 가능한 판정/기록 코어, 실제 시스템에 연결된 adapter와 운영 controller를 구분해 수락한다. 전체 목표가 도달 가능한 구성인지의 판단에는 각 단계의 owner·input·output·validation·fallback·next gate가 필요하다. 실제 목표 달성에는 그 경로를 따라 생성된 운영 증거와 인간 수락이 추가로 필요하다.

## 4. 검증 계획

정상 사례뿐 아니라 누락·중복·다른 대상의 근거·최신 실패·진행 중 재시도·반대 주장·철회·무효화·시간 경계·미지원 형식·빈 필수 집합·거짓 승인·부분 쓰기·중복 효과를 검증한다. gate graph의 도달성 검사는 필요조건이며 사회적 독립성, 제품 적합성, 계정 권한과 운영 성공을 증명하지 않는다.

평가 결과의 범위와 아직 미검증인 최종 목표를 감추지 않는다. 현재 실패를 해결하기 위해 신뢰 기준을 낮추거나 인간 수락을 기계 통과로 바꾸지 않는다.

## 5. 이번에 구현한 최소 경로

`harness.py`는 별도로 초기화하는 SQLite 이벤트 원장과 엄격한 task/policy/record 검사, 고정된 argv 목록의 로컬 검사 실행, 대상/정책/engine digest에 결합된 TestRun, 독립 상태·Markdown Task View, operation key/CAS, 무효화·명시적 중지 확인, 로컬 후보, 검증된 백업의 별도 경로 복원을 제공한다. 문서 씨앗의 기존 JSON/JSONL은 자동 이관하지 않는다.

원장과 명령 영수증은 같은 transaction의 사건으로 저장한다. 실행 시작은 프로세스 호출 전에 commit하며, 중단/불명 효과는 다음 실행을 차단한다. `passed` 입력을 가져오는 public CLI는 없으며 실제 허용된 검사 프로세스의 종료 관측에서 생성한다. 재시도는 같은 입력/키의 기존 관측을 반환하고 실패 종료 코드도 유지한다. 원장 상태를 갱신하기 위해 이전 사건을 삭제하지 않는다.

정책 pin/허용 argv/pending 검사는 `harness.py run`의 진입점에서 수행한다. 정책의 authority_ref는 인간 인증 수단이 아니며, OS 파일 소유자나 외부 shell을 차단하지 않는다. 실행 코어는 OS sandbox나 역할별 IAM이 아니다. 명시적 운영자 reconciliation도 실제 프로세스 사망을 자동 인증하지 않는다. 이 경계를 넘는 자율 실행은 X02/D04의 별도 enforcement adapter가 필요하다.

따라서 기존의 문서·복사 도구만 있는 구성에서 **관측→기록→판정→설명→로컬 후보→보존 복구**를 실행 가능한 공통 기반으로 개선한다. 목표로 향하는 구체적인 로컬 경로와 16개 lifecycle gate의 연결을 제공하지만, 전체 위키·인간 인증·외부 효과·교차 도메인 평가·Canary의 운영 성공은 여전히 별도 증거가 필요하다.

## 6. 대안 비교와 최적화 판단

| 항목 | v0.3.0 문서·복사 씨앗 | v0.4.0 최소 로컬 코어 |
|---|---|---|
| 도입 비용 | 문서와 Python 배포기만 필요 | 실제 policy/task 바인딩과 SQLite 원장 운영 필요 |
| 판정 재현성 | 사람이 계약을 해석하고 수동 기록 | 선언한 입력/검사 범위에서 고정 규칙으로 재계산 |
| 실패·중복 요청 | 절차 준수에 의존 | 최신 실패, pending, operation key/CAS를 CLI가 처리 |
| 근거·복원 | 파일 출처를 사람이 연결 | 실제 프로세스 출력과 이벤트 계보, 별도 복원 검증 |
| 권한 경계 | 문서상 제한 | 자체 진입점에서만 강제; OS/IAM은 별도 |
| 진화 | 후보/평가/승격 공통 절차 | 실제 run 기반 로컬 후보까지 연결; 상위 평가/승격은 후속 |
| 유지 비용 | 코드가 적지만 수동 해석 비용 미측정 | 코드·테스트 증가; 반복 판정 자동화의 순효과는 운영 실측 필요 |

요구된 CLI 제품화와 증거 기반 재현성에는 v0.4.0 구성이 더 적합하다. 문서 열람만 필요한 프로젝트에는 v0.3.0의 단순함이 유리하지만 실행 중 허위 완료·중복 효과를 막는 메커니즘이 부족하다. 전체 비용과 신뢰 하한을 같은 workload에서 측정하지 않았으므로 v0.4.0의 시간·토큰·개입 비용 절감이나 V3/V4 우월성을 검증된 결과로 선언하지 않는다.

이번 검토는 동일 작성자의 계약↔코드↔반례 테스트 교차 검토다. 독립 평가자나 교차 프로젝트 감사로 표시하지 않는다. 실행 중 정책 변경, Windows 리다이렉션 인코딩, 계약 시나리오 개수 회귀를 발견해 수정하고 회귀 검사를 포함했다. 실제 검증 결과와 소스 hash는 [실행 증거](../harness/evidence/EXE-20260913-DECISION-001/validation.json)에 연결한다.

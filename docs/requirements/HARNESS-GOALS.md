# HARNESS-GOALS — 계층적 진화형 AI 개발 하네스의 목표

- Requirement: `REQ-HARNESS-VISION-001`
- 출처: 사용자가 이 대화에서 직접 제시한 목표·17개 원칙과 후속 비공개 씨앗 배포 요청.
- 권위: `confirmed_by_user` — 목표와 배포 범위에 대한 확인이다. 기술 구현의 성공이나 모든 RFC 세부 선택의 수락을 뜻하지 않는다.
- 수락: mixed. 재현·무결성·권한 검사는 machine_verifiable, 재미·UX·감각·가치·설계 적합성은 human_verifiable.

## 최종 목표

모든 프로젝트가 동일한 범용 하네스 코어에서 시작하되, 실제 운영의 실패·마찰·검증 결과로 점진적으로 특화한다. 반복 가능하고 일반화 가능한 개선은 도메인과 코어 계층으로 승격해 재사용한다. 최종형은 Evidence-Oriented, Data-Oriented, Evolutionary Agentic SDLC다.

AI의 완전한 이해나 장기 기억을 전제하지 않는다. 코드, 데이터, 테스트, 실행, 아티팩트, 배포, 인간 판단을 외부 증거와 이벤트로 남기고 그 증거에서 상태를 재구성한다. 기록됐다는 사실만으로 데이터가 참이 되는 것은 아니며, 출처 권위·버전·무결성·관측 범위를 확인한다.

```text
Human → OOP View → 명시적 행동 요청 → Policy/Execution → Reality
Human ← OOP View ← Derived Projection ← Evidence/Event ← Reality

Project → Domain → Universal Core       개선의 일반화와 승격
Universal Core → Domain → Project       호환성·Canary·Rollback을 거친 전파
```

## 핵심 인터페이스

**View to OOP, Set up to DOP.**

- OOP View: Requirement, Task, Decision, Module, Test, Release 등 목적·책임·상태를 이해할 수 있는 객체 관점. Newgame에서 사용한 **위키 페이지 전체의 탐색·문서·관계·작업 흐름**이 예시다. 특정 콘솔 하나나 특정 언어의 클래스 상속 구조로 한정하지 않는다.
- DOP Setup: Evidence, Event, Execution, Relation, Policy, Eval 및 명시적 변환 규칙. 저장 방식 하나를 DOP 자체로 간주하지 않는다.
- 설명·기획 의도·인간 판단은 출처 있는 입력이다. 구현·검증·완료·배포 표시는 증거에서 파생한다. View의 문장을 다시 검증 증거로 읽는 순환을 금지한다.

## 17개 원칙과 추적 ID

| ID | 사용자 원칙 | 최소 계약에 요구되는 결과 |
|---|---|---|
| G01 | View to OOP, Set up to DOP | 사람의 객체 표면과 내부 데이터 계약 분리 |
| G02 | AI의 서술을 진실로 취급하지 않는다 | 사실 주장마다 외부 source/evidence 연결 |
| G03 | 상태보다 증거가 먼저다 | verified/released/ready는 조건과 근거로 도출 |
| G04 | 객체는 인터페이스이고 데이터가 진실이다 | Task 상태 대신 TestRun·Evidence·Acceptance로 판정 |
| G05 | 모든 것을 추적할 수 있다고 가정하지 않는다 | unknown/unverified/stale/conflicted/blocked 허용 |
| G06 | 검증 가능한 블랙박스로 만든다 | 입력·출력·상태 변화·실패 조건·검증 경계 기록 |
| G07 | 상태의 생성 경로를 추적한다 | 입력 snapshot → rule version → projection 계보 |
| G08 | Core를 포크하지 않고 Overlay로 확장한다 | 공통 규격 유지, domain/project 확장 지점과 충돌 처리 |
| G09 | 로컬 성공을 보편적 진실로 승격하지 않는다 | 여러 프로젝트·여러 도메인의 독립 평가 |
| G10 | 하네스 자체도 프로젝트처럼 관리한다 | Harness Requirement/Change/Eval/Release와 rollback |
| G11 | 자기개선과 자기승격을 분리한다 | 제안·sandbox 평가와 위험 변경 승인 권한 분리 |
| G12 | 자동화와 함께 검증·통제도 강화한다 | 자율 범위에 맞는 증거·policy·eval·auditability |
| G13 | 프롬프트보다 실행 계층 강제를 선호한다 | 중요한 권한은 tool capability/policy에서 차단 |
| G14 | 계속 진화하는 시스템이다 | V2 신뢰 기반 → V3 프로젝트 개선 → V4 계층 진화 |
| G15 | 진화는 복잡도 증가가 아니다 | 규칙·workflow·context 축소도 개선으로 평가 |
| G16 | 인간 판단의 영역을 남긴다 | human_verifiable/mixed의 명시적 인간 수락 |
| G17 | 자동화 양보다 높은 신뢰도가 목적이다 | 더 적은 개입으로 재현성·검증 가능성·안전성 유지/개선 |

## 이번 배포의 범위

`REQ-HARNESS-SEED-001`: codex_evolutionary_harness에 목표와 상위 아키텍처를 정리하고, 필요할 때 가져다 쓸 **최소 계약 씨앗**을 GitHub **private** 저장소로 배포한다. 버전 고정, 빈 프로젝트 기록, 기존 파일 보존, 출처 확인, 사용·업데이트·복구 절차를 제공한다.

허용 범위는 문서·계약·최소 배포 도구, 로컬 검증, 이 저장소의 Git 초기화·commit·push와 private 배포다. Newgame 수정, public 공개, 유료 자원, credential 변경, 전체 `eh` 런타임 구현은 이번 범위가 아니다.

씨앗의 배포는 진화 기능의 검증 완료를 뜻하지 않는다. G01–G17의 구현 능력은 각각 별도 증거를 요구한다. 실행 중 목적·권한·출처 충돌처럼 판단에 필요한 정보가 없으면 해당 지점만 인터뷰하며, 이미 명시된 목표·권한은 반복 질문하지 않는다.

## 자가피드백과 상위 계약 보완

`REQ-HARNESS-FEEDBACK-001`: 씨앗을 사용하는 프로젝트의 오류 개선 및 스킬 사용·추가·변경에서 공통 계약의 개선 기회를 검토한다. 관측·분류·중복 방지·평가·공유 권한·제출·승격·릴리스·재적용·효과 확인을 연결한다. 프로젝트 경험을 자동으로 일반화하거나 외부로 전송할 권한은 부여하지 않는다.

`REQ-HARNESS-CONTRACT-COVERAGE-001`: 자가피드백 계약을 완성한 뒤 G01–G17을 상위 설계와 재사용 계약에 대조하여 빠진 운영 의무를 보완한다. 문서 연결의 완전성과 실제 능력의 검증은 구분한다. [상위 RFC의 보완표](../rfcs/RFC-0002-hierarchical-evolutionary-architecture.md#14-목표와-운영-계약의-연결)와 [검사 가능한 연결표](../../seed/docs/harness/contracts/coverage.json)를 유지한다.

이번 수락은 mixed다. 빈 씨앗·참조·권한 기본값·배포 재사용은 기계 검사하며, 아키텍처의 적합성·실제 운영 개선·도메인 간 일반성은 별도 인간 판단과 실행 증거를 요구한다.

`REQ-HARNESS-ASSURANCE-001`: 사용자 지정 일곱 영역을 Newgame의 전체 위키 정보구조와 현행 씨앗에 대조하고, 선언만 있는 의무를 구체적인 입력·판정·권한·반례·불확실성 기록 계약으로 보완한다. [RFC-0004](../rfcs/RFC-0004-seven-area-assurance-audit.md)에 전후 판단과 증거 한계를 기록한다. 일곱 영역의 문서 검토를 runtime 기능 검증이나 성능 우위로 주장하지 않는다.

`REQ-HARNESS-DECISION-001`: 전체 세부 판정의 입력·우선순위·시간/참조·권한 상속·단계 의존성·adapter·완료 단위를 재검토하고 목표 경로의 공백을 보완한다. 사용자는 인터뷰에서 최소 실행 코어 구현과 검증을 명시적으로 승인했다. [RFC-0005](../rfcs/RFC-0005-end-to-end-decision-system.md)에 계약 조합과 로컬 실행 경로를 정리한다. 이 승인은 기존 프로젝트의 원본 권위 변경, credential 변경, 외부 배포나 자동 승격 권한을 의미하지 않는다.

REQ-HARNESS-PREVENTION-001: 사용자가 위키 누락 원인 감사 후 씨앗 예방장치 보완과 실제 프로젝트 작업 재개를 승인했다. 기존 V01/V03를 bootstrap 필수 Gate로 연결하고 API 검사만으로 완료하는 경로를 차단한다.

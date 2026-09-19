# 정리.txt 목표 → 구현 → 판정

2026-09-16. 원문은 사용자 제공 아이디어이며 제품 방향으로 채택되었다. 문서 속 외부 프레임워크 언급은 실행 지시로 취급하지 않는다.

| 목표 | 구현/근거 경로 | 판정 범위 |
|---|---|---|
| 모든 프로젝트 동일 V2 | seed manifest + engine pin + 고정 core | 로컬 byte identity |
| 공통/프로젝트 규율 분리 | init adapter/input, immutable policy | 명시 목록 외 입력은 미추적 |
| 기본 개발 루프 | Task → Run → Evidence → resume | 실제 CLI 합성 흐름 |
| 제품 기본 흐름 | 테스트 adapter + owner MVP decision | 오너가 실제 프로젝트에서 판단 |
| 첫날부터 관측 | observe + 6 categories | reported와 검증 사실 구분 |
| 내부 발화 trigger | checkpoint → readiness event | 자동 실행 조건 검사 |
| 탐색과 채택 분리 | isolated Candidate → evaluator → owner | 자기 제안 즉시 채택 불가 |
| 제한된 특화 | 5개 필드 whitelist | 권한·core 변경 불가 |
| 다음 진행 범위 | Task 한 건, dependencies/current state | advice only, 실행 권한 확장 없음 |
| V2 대비 평가 | prereg suite + hard oracle + 두 split | 명령 해석 범위 |
| V3 고정 | immutable config + task pin | 새로운 채택 전 active 고정 |
| V2 유지도 정상 | no improvement/blocked result | 자동 버전 올림 없음 |
| 고정 V3 반복 | resolve 반복 및 버전 pin 회귀 | 합성 실행 |
| 같은 V2에서 특화 반복 | fresh V2 3회 → bounded generator → V3 | 실제 LLM/다중 프로젝트는 미검증 |
| View to OOP | 대문/주제/객체, 상태별 배치, 양방향 관계 | 생성 HTML·명시 lineage |
| Set up to DOP | event chain/Run/Observation/Eval | 객체 상태의 자기 주장 배제 |
| 복구·idempotency | SQLite 예약, unknown reconcile, config rollback, backup/restore | 로컬 원장·향후 Task 범위 |
| 계층적 재사용 | 새 배포/도입 경계와 feedback 계약 | 원격 일반화/전파 미구현 |

이 표의 연결 수를 제품 완성률로 계산하지 않는다. 구현 계약 통과와 실제 운용 품질의 검증을 구분한다. 전자 근거는 `docs/harness/evidence/EXE-20260916-V2-REWRITE-001/`, 후자는 실제 프로젝트 적용 이후 별도 축적한다.

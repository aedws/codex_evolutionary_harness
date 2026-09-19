# Checkpoint — 2026-09-15 기능 동등성 확정 계획

TASK-20260915-PARITY-PLAN-001 / EXE-20260915-PARITY-PLAN-001

- Changed: RFC-0015와 구조화 계획. F01~F20 및 D01을 P0~P9에 전수 연결. 오너가 별도 비공개 검증 프로젝트→현 프로젝트 선택 적용 방향을 선택.
- Verified: 계획 구조 21항목/10단계 및 선행 DAG 검사. 씨앗 manifest와 프로젝트 기존 Run의 239개 입력 bytes 보존. 새 실행 검사/동등성 인증 아님.
- Unverified: P0 범위·예외·독립 검토자, 외부 대상/권한/예산, Canary 제안값 확정. C1 공통 기능, C2 선택 적용, C3 계층 진화 판정을 구분.
- Evidence/events: EVD-20260915-PARITY-PLAN-001; PLANNING_STARTED / PLAN_RECORDED. docs/harness/evidence/EXE-20260915-PARITY-PLAN-001/plan-validation.json.
- External: 없음. 구현·새 저장소·계정·배포·예약 자동화 생성 없음.
- Feedback: no_candidate. 기존 감사와 환경 선택을 계획으로 연결; 새 런타임 실패나 skill 변경 없음.
- Current project evidence: 9da8890에서 씨앗 v0.12 선택 적용, 353개 필수 검사와 bootstrap_ready. 인간 수락·전체 기능 동등성·계층 진화는 별도.
- Next allowed action: 계획 범위를 검토한 뒤 P0 상세 case manifest와 P1 오프라인 비교 실행기 구현 Task를 시작. 외부 효과는 해당 단계의 구체적 대상/권한 판단 후.

[실행 계획](../rfcs/RFC-0015-newgame-parity-certification-plan.md)

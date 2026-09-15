# 씨앗 v0.12.0 보완·동일 결과 검사

TASK-20260915-PARITY-CHECK-001 / EXE-20260915-PARITY-CHECK-001

**보완한 로컬 기능과 지정한 비교 필드는 통과했다. Newgame 전체 기능 동등성을 확정하지 않는다.** 기준 Newgame은 be23c7c, 씨앗 baseline은 4b4db5d이다.

| 확인 대상 | 결과 | 근거 경계 |
|---|---|---|
| 자동 객체 생성 | 실제 모듈 61개·마일스톤 28개 대응 | 원문 ID·제목·목적/경로, 작업의 사용자 수락 조건 대조 |
| 원본 연결 | 89/89 documented_by 관계 | 나머지 Newgame 전체 관계망의 완전 복제 주장이 아님 |
| 동일 입력 재실행 | 중복 없이 unchanged | 변경 입력에 같은 키를 쓰면 conflict |
| 상태 엄밀성 | 원문 완료와 실행 verified 분리 | 실제 Core Run·독립 수락 없는 객체는 미검증 |
| 관계·결정 | 타입/출처 검증, 충돌 차단, 수락 후 대체, 이력 보존 | 실제 외부 원본의 의미 수락은 별도 |
| 위키 | 검색·유형·상태·선택 유지, 양방향 관계·원본 링크 | 1280/390px 합성 화면 관찰; 오너 수락 대기 |
| 회귀 검사 | 최종 145개 통과, 60.883초 | 씨앗 로컬 검사이며 기존 제품의 60초 gate 통과가 아님 |
| 최적화 | passed/stale 전체 projection 동일, Core.status 24→1회 | 같은 합성 workload; Newgame 전체 성능 우위 주장이 아님 |
| 배포 패키지 | 새 설치·재실행 byte/mtime·ZIP 일치 | v0.11 원장을 덮어쓰지 않음 |

## 의도한 결과 차이

Newgame의 원문 완료·현행화 표기를 씨앗의 구현 검증 또는 인간 수락으로 바꾸지 않는다. 외부 ID는 namespace와 native-ID hash로 보존하며 동일성 대조는 원문 ID 매핑을 사용한다. Newgame E2E 문자열은 원본에 남아 있지만 그 문자열 자체를 TestRun으로 만들지 않는다. HTML 전체가 같은 것이 아니라 지정된 업무 값과 새 계약의 정상·실패 결과를 확인했다.

## 남은 동등성 범위

실제 Notion/Sheet 수집, PR·CI·Cloudflare 배포, 전체 서비스 복구, 장기 Canary와 교차 프로젝트 승격은 미완/미검증이다. 기존 AI-Agent-Execution-Platform은 v0.11 구성과 부분 도입 판정을 유지한다. 원장 핀과 권한을 자동 확장하지 않는다. 기존 15/17 부분 메커니즘 비율을 전체 동등성 점수로 바꾸지 않는다.

## 재현

```powershell
python -B scripts/seed.py check
python -B scripts/check_contracts.py
python -B -m unittest discover -s tests
python -B scripts/check_newgame_parity.py --reference C:/path/to/Newgame --commit be23c7cad570c47e117d7521d998f5062ee23ec0
```

참조 checkout의 대상 파일이 commit과 다르면 대조를 거부한다. 검사는 원본을 쓰거나 외부 요청을 하지 않는다. 실제 원문 데이터는 배포 씨앗에 넣지 않는다.

근거: [검증 영수증](../harness/evidence/EXE-20260915-PARITY-CHECK-001/validation.json), [Newgame 대조](../harness/evidence/EXE-20260915-PARITY-CHECK-001/final-newgame-differential.json), [최종 테스트](../harness/evidence/EXE-20260915-PARITY-CHECK-001/final-tests-v2.log), [최적화](../harness/evidence/EXE-20260915-PARITY-CHECK-001/optimization.json).

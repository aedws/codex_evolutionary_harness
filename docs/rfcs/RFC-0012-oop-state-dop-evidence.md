# RFC-0012 — OOP state view / DOP evidence

TASK-20260915-SEED-STATE-001 / EXE-20260915-SEED-STATE-001. v0.10.0 local candidate; mixed acceptance.

# 상태별 OOP 탐색과 DOP 근거 분리

오너 정정: 보고서 간 노드가 아니라 상태별 노드가 필요하다. 기존 화면은 같은 작업의 Task/Report/Execution/Evidence 이름을 동급으로 반복했다.

기본 단위는 판정 상태다. 상태마다 요구·작업·결정·모듈·검사·릴리스의 안정 ID를 한 번씩 배치한다. 상태는 입력 객체의 status 필드가 아니라 외부 reducer 결과로 결정한다. 지원하지 않는 상태는 unknown, 검사 근거가 없는 객체는 unverified다. 검사 통과가 인간 수락·배포 완료를 뜻하지 않으며 별도 축을 유지한다.

Report/Execution/Evidence/Event/Run은 DOP 레코드다. 기본 업무 목록/집계에서 제외하고, 업무 객체의 상세나 별도 근거 목록에서 조회한다. 보고서를 열면 명시적으로 연결된 Task의 상태를 보여준다. 제목이 같다고 서로 다른 업무 ID를 병합하거나, 연결된 Task가 통과했다고 Requirement도 통과시키지 않는다. 미연결 근거는 판정 대상 없음으로 남긴다. 상태 사이에 실제 규칙이 없는 전이 화살표를 만들지 않는다.

state-object-view-1은 기존 object-node-map-1의 기본 화면 지시를 대체한다. 과거 관계 renderer와 기록은 보존한다. 좁은 화면은 한 열로 표시하고 긴 목록은 개수와 전체 펼치기를 제공한다. seed와 project adapter는 별도 버전/채택이며 기존 engine·policy·키·LLM 보고서/원본을 변경하지 않는다.

검사: DOP 제외, OOP 고유 ID 중복 없음, 같은 제목의 다른 ID 보존, 숨겨진 객체 제외, 미확인/오래된 검사/실패/통과 분리, 인간 수락·배포 축 보존, 과도한 목록/escaping, report→Task 투영, 링크·권한·bootstrap 회귀. 화면 의미와 직관성은 오너 수락 대기다.

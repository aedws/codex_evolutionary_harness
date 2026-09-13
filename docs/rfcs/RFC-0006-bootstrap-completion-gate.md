# RFC-0006 — 위키 누락을 막는 bootstrap 완료 Gate

원인: V01/V03에 위키 의무가 있었으나 bootstrap 진입점·필수 산출물·판정 경로·반례 테스트로 이어지지 않았다. 에이전트가 API/기록 검사만 선택해 통과한 결과를 셋업 완료로 확대 보고했다.

v0.5.0 / contract 5는 bootstrap.py의 고정 profile을 추가한다. 9개 탐색 범주, 6개 객체 유형, source/hash, 관계 endpoint/provenance, 최소 3문서의 역할별 경로, 진입점에서의 전체 문서 도달성을 검사한다. 기존 위키/Markdown을 재사용할 수 있으며 웹 서버를 강제하지 않는다.

installed, bootstrap_partial, wiki_ready, bootstrap_ready, product readiness를 구분한다. Artifacts-only는 wiki_ready까지만 반환한다. 최종 Gate는 pinned local ledger에서 validation_task의 현재 pass를 확인하고 human_pending을 유지한다. 프로세스 pass만으로 bootstrap_ready를 생성할 수 없다. 실제 쓰기를 하는 임의 외부 도구/OS를 강제하는 기능은 아니며 기존 harness.py run의 의미도 바꾸지 않는다.

부트스트랩은 필수 Gate를 프로젝트 검사 명령에 연결하고 최종 보고 전에 전체 Gate를 실행해야 한다. 부족한 문서/해시/유형/관계/경로는 partial로 남긴다. 의미적 문서 품질과 인간 신원은 이 구조 검사로 인증하지 않는다.

기존 v0.4.0 engine은 byte-identical하게 유지한다. 추가 component와 binding/check 통합으로 기존 원장/정책을 이관하지 않고 예방장치를 적용한다. 설치 영수증을 덮어쓰지 않으며 별도 adoption 영수증으로 출처·범위·hash·복구를 기록한다. version-5 전체 payload 재설치는 기존 문서/위키/기록을 덮어쓰지 않는다.

반례: API 테스트만 통과하고 위키가 없는 상태, 필수 범주/유형 삭제, stale/missing source, 경로 탈출, 고아 문서, dangling relation, 중복 JSON key, 자기 승인 필드, 현재 Run이 없는 완료 주장. 66개 seed 검사가 통과했다. 실제 프로젝트의 delta 적용 검증은 별도 증거에 연결한다.

단순 경고 문구보다 실행 가능한 필수 Gate가 누락을 탐지한다. 모든 프로젝트에 같은 UI를 복제하는 방법보다 기존 wiki를 binding하는 편이 프로젝트 소유권과 기술 선택을 보존한다. 그러나 binding 작성 비용과 문서 품질의 인간 검토는 남으며, 독립 프로젝트 전반의 개선 효율은 아직 실측하지 않았다.

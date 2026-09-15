# RFC-0009 — 설치 시 객체 위키 초안 자동 생성

2026-09-15 / 범위: 공통 초안 생성 계약. 로컬 구현 후보이며 외부 릴리스·전체 bootstrap 수락과 별개.

## 문제와 Newgame 대조

v0.7.0은 `wiki_template.py scaffold`와 첫 AI 요청을 사용자가 별도로 실행해야 했다. 기본 renderer도 작업 객체만 지원하므로 6개 객체와 근거/관계 탐색은 프로젝트에서 추가해야 했다. 설치만 하고 첫 제품 작업을 시작하면 객체 위키가 빠질 수 있다.

Newgame의 전체 docs Markdown 목록/해시는 이번 실행 근거에 보존하고, mkdocs 중첩 목차, features/index, architecture/index, project-ontology, 위키 협업 문서를 집중 검토했다. 전체 문서의 의미를 모두 검증했다는 주장은 하지 않는다.

| Newgame 구조 | 범용 씨앗 초안 |
|---|---|
| 종합 문서 → 큰 주제 → 세부 기능 | 대문 → 9개 주제 → 6종 객체의 작은 문서 |
| 중첩 목차에서 경로·직계 자식 생성 | 공통 타입 매핑에서 부모·자식·돌아가기 생성 |
| 온톨로지 객체·관계·행동·원본 계보 | 객체 탐색, 양방향 관계, 다음 행동, 근거 조회, View 입력/규칙 |
| 역할·권한의 실행 경계 | 초안은 계정/역할/서버 없이 로컬 파일. 실제 접근은 오너 인터뷰와 기존 gate |

게임 내용·계정·역할 이름·Notion/Sheet 운영 결정을 배포하지 않는다.

## 명령과 판정 계약

`seed.py init`은 파일 쓰기 전에 기본 draft-input을 검증하고 HTML/manifest 전체 바이트를 계산한다. 복사와 같은 충돌 사전 점검에 포함해 설치 시 자동 생성한다. ZIP에도 같은 결정론적 초안을 포함한다. 독립 명령은 `wiki_draft.py build/check --input ... --out ...`이다.

초안은 Requirement/Task/Decision/Module/Test/Release 전부와 객체별 목적·행동·관계·근거·미확인을 표시한다. 임의 파일 탐색·본문 수집·네트워크·LLM 호출은 없다. 경로 참조는 선언일 뿐 근거 검증이 아니다. 원본 registry는 계속 비어 있다. 객체 입력의 authored status/승인 필드는 거부하고 출력 상태는 항상 unverified/human_pending/interview_pending이다.

`draft_generated`는 보기 가능한 초안이다. `presentation_checked`, `bootstrap_ready`, 구현·검증·배포·인간 수락을 뜻하지 않는다. 오너는 설치 직후 초안을 볼 수 있지만 실제 역할/HTTP 정책 확정은 기존 인터뷰와 bootstrap-wiki-2가 담당한다.

## 소유권·멱등성·복구

`docs/wiki/draft-input.json`은 설치 후 프로젝트가 편집하는 초안 원본이다. `.local/wiki-draft/*`는 생성 출력이며 receipt의 draft_files로 seed component 해시와 분리한다. 동일 설치/ZIP은 동일 바이트, dry-run은 쓰기 없음, 출력 충돌·내용 변조·부분 쓰기·symlink/reparse·버전 차이는 거부한다. 기존 위키/registry/role/tree를 덮어쓰지 않는다.

입력 수정 후 새 출력 경로를 사용한다. 중단된 출력과 기존 설치 영수증은 보존한다. Rollback은 이전 입력/renderer/출력 묶음을 선택하는 방식이며 자료 삭제·과거 증거 재작성은 없다. 전체 디렉터리의 다중 파일 원자성이나 OS 파일 접근 제어를 주장하지 않는다.

## 호환성과 비교

새 구성요소 `newgame-object-draft-1`을 추가하며 contract 6, 원장 engine, bootstrap, 기존 wiki_template 프로필은 유지한다. v0.7.0 프로젝트에는 재설치하지 않는다. 별도 preview 위치에 적용하고, 실제 위키로 채택하려면 프로젝트 원본/관계/권한 및 기존 gate와 연결한다.

기존 방식은 최소 배포 크기와 자유로운 구현이 장점이나 AI가 초기 문서 작업을 누락할 수 있다. 이번 방식은 추가 클릭 없이 객체 초안을 보여주고 공통 구조를 검사하는 장점이 있으며, 6개 초안과 렌더러를 유지하는 비용 및 실제 의미/권한을 채워야 하는 한계가 있다. 설치 단계의 누락 예방에는 이번 방식이 적합하다. Newgame의 모든 동적 수집·검색·운영 권한을 복제했다는 뜻은 아니다.

## 완료 증거

신규 설치/ZIP에서 별도 scaffold 명령 없이 대문·객체·관계·근거 경로가 존재하고 모든 로컬 링크가 닫혀야 한다. 두 도메인 fixture, 누락 타입/관계/상태 주입/HTML 주입/경로, 재생·편집 충돌·부분 출력·권한 미확정을 검사한다. 실제 프로젝트 동작·인간 가독성·외부 배포와 교차 프로젝트 승격은 별도 증거가 필요하다.

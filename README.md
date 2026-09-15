# Evolutionary Harness — reusable contract seed

<!-- SEED-USAGE:START — keep this usage block immediately after the title. -->
## 씨앗 사용법 — 여기서 시작

**현재 개발 후보: v0.12.0 / contract 6 / operating-workspace-1.** 자동 객체·관계·결정 이력과 Newgame 기준 입력 비교 검사를 포함합니다. 전체 기능 동등성과 실제 프로젝트 도입은 아직 수락되지 않았습니다. [설정·사용법](seed/docs/harness/workspace/README.md) · [기능 대응 RFC](docs/rfcs/RFC-0013-newgame-functional-parity.md). 안정 태그 v0.7.0과 구분합니다. 아래 순서로 설치한 뒤 대상 프로젝트에서 bootstrap을 요청한다. 내려받기만으로 자기개선·승격·Canary가 자동 실행되지는 않는다.

### 1. 개발 후보 내려받고 commit 고정

비공개 저장소 접근 권한과 인증된 Git, Python 3.10 이상이 필요하다. 아래는 PowerShell 예시다. 두 경로를 자신의 환경에 맞게 바꾸고, 배포 원본은 대상 프로젝트 밖의 **새 디렉터리**에 둔다. 기존 checkout이나 프로젝트 위에 전체 저장소를 복사하지 않는다.

```powershell
$SeedSource = "C:/tools/evolutionary-harness-v0.12.0-candidate"
$ProjectPath = "C:/projects/my-project"
git clone --branch codex/wiki-auto-draft-20260915 --depth 1 https://github.com/aedws/codex_evolutionary_harness.git "$SeedSource"
if ($LASTEXITCODE -ne 0) { throw "씨앗 다운로드 실패: 다음 단계로 진행하지 마세요." }
git -C "$SeedSource" rev-parse HEAD
git -C "$SeedSource" checkout --detach
python -B "$SeedSource/scripts/seed.py" check
if ($LASTEXITCODE -ne 0) { throw "씨앗 무결성 검사 실패" }
python "$SeedSource/scripts/check_contracts.py"
if ($LASTEXITCODE -ne 0) { throw "씨앗 계약 구조 검사 실패" }
```

### 2. 대상 프로젝트에 설치

같은 터미널에서 먼저 예상 파일을 확인한다.

```powershell
python "$SeedSource/scripts/seed.py" init --target "$ProjectPath" --dry-run
if ($LASTEXITCODE -ne 0) { throw "설치 사전 점검 실패: 충돌 또는 대상 경로를 확인하세요." }
```

예상 경로가 맞으면 설치한다.

```powershell
python "$SeedSource/scripts/seed.py" init --target "$ProjectPath"
if ($LASTEXITCODE -ne 0) { throw "설치 실패: 기록된 부분 상태와 오류를 확인하세요." }
```

기존 `AGENTS.md` 등과 겹치면 설치는 중단된다. 이 경우 빈 임시 경로에 설치한 뒤 [기존 프로젝트 통합 절차](docs/REUSE.md#2-기존-프로젝트)를 따른다. 동일 원본·영수증·파일이면 재실행은 no-op이며, 작업으로 파일이 바뀌었다면 재설치 대신 [업데이트·복구 절차](docs/REUSE.md)를 사용한다.

### 3. AI에게 첫 bootstrap 요청

**대상 프로젝트 폴더**를 작업 공간으로 열고 아래 요청을 보낸다. v0.8.0에서는 객체 위키 초안이 설치 시 이미 생성됩니다. 실제 프로젝트의 의미·근거·역할 바인딩은 아래 bootstrap 요청으로 이어갑니다.

```text
이 프로젝트의 AGENTS.md와 BOOTSTRAP_PROMPT.md를 읽고 bootstrap을 수행해라.
기존 코드·문서·테스트·데이터·지침을 조사하고, 목표·원본 권위·필수 검사·수락 조건을 정리해라.
확인된 사실만 Project Overlay에 반영하고 Task/Execution/Evidence/Event/checkpoint를 연결해라.
역할·문서 범위·열람/수정/승인/실행 권한은 오너에게 먼저 인터뷰하고 확정 전에는 설정하지 마라.
wiki_template.py와 docs/harness/wiki/README.md를 사용해 Newgame식 종합 대문·주제 9개·남은 작업 상세를 기본으로 작성하고 표현 검사를 필수 검사로 등록해라.
V01/V03와 bootstrap 계약을 적용해 큰 문서 → 주제 → 작은 문서 계층과 오너가 선택한 접근 모드를 구성해라. 오프라인 단일 작업 공간은 명시적 선택에 따라 로그인을 생략할 수 있다.
bootstrap.py의 필수 위키·근거·검사 Gate를 통과하기 전에는 셋업 완료로 보고하지 마라.
불명확한 목표나 권한 충돌은 필요한 항목만 인터뷰해라.
첫 실제 작업과 필요한 검증을 제시하되, 제품 구현·외부 쓰기는 해당 작업의 승인 범위에 따라 진행해라.
```

이후 실제 작업마다 근거를 기록하고 종료 시 오류·마찰·스킬 사용의 개선 후보를 검토한다. upstream 제출은 기본 비활성이고 제출·공유·merge·release·adopt 권한은 각각 확인한다. 제품별 빌드·테스트·배포 설정은 bootstrap에서 출처와 함께 연결해야 한다.

### 4. 최소 실행 코어 시작

bootstrap에서 실제 검사 명령과 입력 파일을 확정한 뒤 [로컬 코어 사용법](seed/docs/harness/runtime/README.md)에 따라 policy/task 파일을 준비하고 `python harness.py init`, `task`, `run`, `status`, `view`를 사용한다. `.harness` 원장이 실제 검사 관측을 보존하며, 기존 수동 기록을 자동 이관하지 않는다. 예제의 빈 권한·ID를 사실로 채우기 전에는 실행을 시작하지 않는다.

### 5. Newgame 대응 운영 위키

[운영 계층 사용법](seed/docs/harness/workspace/README.md)에 따라 오너 인터뷰 → 원본/객체 연결 → collect → 운영 위키 → 현재 Run/독립 판단 → 승인된 배포 어댑터 순서로 진행한다. 문서 초안을 운영 완료로 취급하지 않는다. 기존 프로젝트는 덮어쓰지 말고 새 경로에서 도입을 평가한다.

### 6. 최종 목표 달성 여부

**현재 씨앗만 설치해서 최종형 하네스가 완성되지는 않는다.** 공통 계약에 더해 로컬 원장·검사 실행·상태 판정·Task View·로컬 후보·원장 복원 경로가 제공된다. 실제 프로젝트 바인딩, OS/인간 신원의 권한 경계, 독립 평가와 외부 승격·Canary 실행 및 효과 관측은 추가로 필요하다.

[범용 프로젝트 적용 범위·V2/V3/V4 도달 조건](docs/ADOPTION.md)에서 제공 기능, 프로젝트가 채울 내용, 아직 검증하지 못한 부분을 확인한다. 사용 순서는 **설치 → bootstrap → 첫 실제 작업의 증거 연결 → 로컬 피드백 → 승인된 상향 개선 → 검증된 재적용**이다.
<!-- SEED-USAGE:END -->

## 목표와 설계

**View to OOP, Set up to DOP.** 사람은 객체와 목적을 다루고, 시스템은 데이터와 증거를 다룬다.

모든 프로젝트가 공통 코어에서 시작하고 Overlay로 특화한다. 실제 실패·마찰·검증에서 얻은 개선은 Project → Domain → Universal Core로 평가·승격하고, 상위 변경은 호환성 검증·Canary·Rollback을 통해 다시 전파한다.

안정 태그는 **v0.7.0**, 현재 개발 브랜치 후보는 **v0.11.0**이다. [기본 위키 생성기](seed/docs/harness/wiki/README.md)가 Newgame식 대문·주제·작업 상세를 제공한다. 최소 로컬 기록·검사·판정 코어를 포함한다. v0.11.0에는 선택적 업무 상태/HTTP/로컬 계정 경계와 지정 대상 Canary 어댑터가 추가됐다. OS 신원 격리·외부 수집·자동 승격·다중 프로젝트 확대는 미완료다. V2/V3/V4는 목표 능력이며 배포 버전과 다르다.

## 먼저 읽기

1. [사용자가 확정한 목표와 17개 원칙](docs/requirements/HARNESS-GOALS.md)
2. [상위 아키텍처 RFC-0002](docs/rfcs/RFC-0002-hierarchical-evolutionary-architecture.md)
3. [재사용되는 최소 계약](seed/docs/harness/contract.md)
4. [가져오기·업데이트·되돌리기](docs/REUSE.md)
5. [하위 CLI 설계 제안 RFC-0001](docs/rfcs/RFC-0001-evolutionary-harness-cli.md)
6. [자가피드백 공통 계약 RFC-0003](docs/rfcs/RFC-0003-feedback-common-contract.md)와 [17개 목표 연결표](seed/docs/harness/contracts/coverage.json)

오류 개선·스킬 사용/추가/수정/제거는 작업 종료 시 한 번 검토한다. 일반화 근거가 있으면 로컬 후보를 만들고, 승인된 제출 → 범위별 평가 → 새 씨앗 릴리스 → 프로젝트의 명시적 적용 → 효과 재관측으로 연결한다. 초기 설정은 외부 제출 권한이 없는 local-only다. 자세한 계약은 필요한 항목만 읽는다.

[일곱 핵심 계약 재감사 RFC-0004](docs/rfcs/RFC-0004-seven-area-assurance-audit.md)는 전체 위키 탐색, View 생성 계보, 계층 조합, 일반화, Canary, 역할 강제, 신뢰 유지 비용 비교의 세부 의무를 보완한다. contract 6에는 기존 7영역·21개 계획 시나리오, D01–D08 판정 조합, 16개 lifecycle gate, 최소 로컬 코어가 포함된다. [전체 판정/실행 설계 RFC-0005](docs/rfcs/RFC-0005-end-to-end-decision-system.md)를 참고한다.

## 배포 경계

- `seed/`: 새 프로젝트로 복사하는 공통 계약과 빈 기록. 프로젝트 경험·감사 이력·계정 정보 없음.
- `seed/harness.py`: 설치 후 프로젝트에서 사용하는 최소 로컬 코어. 실제 강제 범위는 자체 검사 진입점이며 OS sandbox나 인간 인증이 아님.
- `scripts/seed.py`: 씨앗 검증·충돌 없는 복사·ZIP 생성용 작은 유틸리티. RFC의 `eh` CLI가 아님.
- `scripts/check_contracts.py`: 17개 목표·31개 조항·16개 lifecycle 의존성·링크·안전한 배포 기본값 검사. 전체 운영 검증이나 자동 피드백 실행기가 아님.
- `docs/requirements`, `docs/rfcs`: 목표와 설계.
- `docs/harness`: 이 하네스 자체를 개발한 기록. **다른 프로젝트로 복사하지 않음.**
- `.local/`, `dist/`: 로컬 실행 영수증·배포 산출물. Git 제외.

GitHub 저장소는 비공개로 운영한다. 재사용은 태그와 파일 해시로 버전을 고정하며, 기존 태그를 이동시키지 않는다. 공개 라이선스를 임의로 부여하지 않는다.

배포 원본 검사는 `python scripts/seed.py check`, `python scripts/check_contracts.py`, `python -m unittest discover -s tests -v`로 실행한다. 실제 프로젝트에서 설정·기록을 채운 뒤에는 빈 배포 원본 전용 검사를 프로젝트 검증기로 사용하지 않는다.

고정된 [bootstrap 완료 검사](seed/docs/harness/bootstrap/README.md)는 v0.5.0에서 추가됐다. 기존 원장 engine은 변경하지 않으며, v0.4.0 프로젝트는 새 검사 파일과 로컬 binding을 명시적으로 추가 적용한다. 9개 분류/6개 객체/역할 경로의 누락은 bootstrap_partial이다.

Owner interview is mandatory before wiki role/access setup. The seed has no fixed roles or accounts. Confirm project roles, document scope and read/edit/approve/execute boundaries, then bind the approved tree and authenticated adapter under bootstrap-wiki-2. Interview pending or untested access enforcement blocks completion.

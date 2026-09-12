# 씨앗 가져오기·업데이트·복구

## 1. 권장: 태그 고정 clone 후 안전한 복사

저장소 접근 권한이 있는 GitHub 계정으로 로그인한다. 계정/credential 변경은 설치 도구가 수행하지 않는다.

```powershell
gh repo clone aedws/codex_evolutionary_harness C:/tools/evolutionary-harness
git -C C:/tools/evolutionary-harness checkout v0.2.0
python C:/tools/evolutionary-harness/scripts/seed.py check
python C:/tools/evolutionary-harness/scripts/seed.py init --target C:/projects/my-project --dry-run
python C:/tools/evolutionary-harness/scripts/seed.py init --target C:/projects/my-project
```

예시 경로를 환경에 맞게 바꾼다. 도구는 Python 3.10+ 표준 라이브러리만 사용하며 패키지를 설치하지 않는다. clone은 배포 저장소용 별도 경로에 둔다. 대상 프로젝트에 전체 저장소를 복사하거나 GitHub의 전체 repository template 기능을 사용하면 감사 기록까지 섞이므로 이 방식으로 안내하지 않는다.

`check`는 seed allowlist/hash, 빈 기록, seed capability 표시를 검사한다. 전체 하네스 스키마·의미·정책 검증기가 아니다. `init`는 대상 파일을 신규 작성하고 `.harness-seed.json`에 설치 원본 manifest hash와 파일별 hash를 남긴다. 제품 Git init/commit/push를 자동 수행하지 않는다.

## 2. 기존 프로젝트

이름이 겹치지 않는 기존 파일은 보존한다. 설치할 경로 중 하나라도 점유되어 있으면 아무 payload도 쓰지 않고 exit 5다. `AGENTS.md`가 이미 있는 프로젝트는 먼저 임시 빈 디렉터리에 seed를 생성하고, 현재 정책과 비교하여 명시적으로 통합한다. 기존 정책을 seed로 대체하지 않는다. 원본 권위나 권한이 충돌하면 해당 항목을 인터뷰한다.

수동 통합에서는 적용 파일/변경 diff, 기존 지침의 보존, seed version/hash, 결정 이유를 프로젝트 Execution/Evidence에 기록한다. 서로 다른 파일을 섞은 통합을 원본 그대로 설치한 영수증으로 가장하지 않는다.

설치가 끝나면 `BOOTSTRAP_PROMPT.md`를 사용해 프로젝트 목표·도메인·원본·필수 검사부터 조사한다. 공통 계약은 유지하고 `docs/harness/overlays/project.json`에 프로젝트별 규칙과 출처를 추가한다. 과거 프로젝트의 Task/Execution/권한을 가져오지 않는다.

## 3. ZIP 대안

```powershell
gh release download v0.2.0 --repo aedws/codex_evolutionary_harness --pattern 'evolutionary-harness-seed-0.2.0.zip' --pattern 'SHA256SUMS.txt' --dir C:/downloads/harness-seed
Get-FileHash C:/downloads/harness-seed/evolutionary-harness-seed-0.2.0.zip -Algorithm SHA256
```

출력 hash를 SHA256SUMS.txt와 비교한다. ZIP에는 seed payload와 설치 영수증만 들어 있다. 새 빈 디렉터리에만 푼다. 기존 프로젝트 위로 압축을 풀면 압축 프로그램의 덮어쓰기 동작이 적용되므로 안전한 init를 대신하지 못한다. 일반 GitHub 소스 ZIP은 개발 기록을 포함하므로 seed 전용 자산과 구분한다.

## 4. 재실행·실패

| 상황 | 결과 / 다음 행동 |
|---|---|
| dry-run | 신규 대상 경로도 생성하지 않음; 예상 파일만 반환 |
| 같은 manifest와 영수증, 파일 hash 일치 | exit 0, unchanged; 파일·mtime 불변 |
| 기존 파일, 다른 version/영수증, 설치 후 프로젝트 변경 | exit 5; 덮어쓰기 없이 diff/upgrade 검토 |
| `.harness-seed.pending.json` 존재 | exit 5; 중단/진행 중 설치를 확인. 시간만 보고 삭제하지 않음 |
| source hash/manifest/version 오류 | exit 2; 검증된 태그를 다시 취득 |
| 복사 도중 디스크/권한/OS 실패 | exit 9; 생성된 파일과 pending을 남겨 부분 상태를 식별 |

CLI 출력은 JSON이며 인자 파싱 오류는 argparse의 표준 usage/exit 2를 사용한다. 성공적인 복사 영수증은 runtime crash durability나 task verification의 증거가 아니다. 동시에 실행한 install은 pending marker로 구분하며 adversarial filesystem 교체나 전원 장애 안전성은 별도 미검증이다.

중단 시 자동 삭제·자동 rollback은 없다. 실행이 끝났는지 확인하고 pending/영수증/배포 manifest를 비교한다. 아직 쓰이지 않은 파일이 배포 hash와 정확히 일치하면 해당 생성 파일만 삭제하거나 별도 검토 디렉터리로 보존한 뒤 재시도할 수 있다. 프로젝트 기록이나 변경 파일은 먼저 snapshot을 만들고 사람과 복구 범위를 정한다. 디렉터리 전체를 삭제하지 않는다.

## 5. 업데이트·되돌리기

새 태그를 별도 checkout에 받아 manifest와 계약 diff를 검토한다. Core 변경은 새 release로 받고 Project/Domain overlay, 객체, 이벤트, 증거, 인간 결정은 보존한다. 새 seed를 기존 프로젝트 위에 재설치하는 명령은 제공하지 않는다.

적용 전 입력 snapshot, 현재 seed/overlay versions, 변경 계획, 검사·rollback 범위를 기록한다. 계약 호환과 필요한 검사를 확인한 뒤 명시적으로 적용한다. 실제 controller가 없는 현재는 수동 계획·기록 단계다. 자동 migration이나 Canary가 실행됐다고 주장하지 않는다.

되돌리기는 이전 계약과 현재 기록의 호환성을 확인한 뒤 수행한다. 설치 이후의 증거·이벤트를 과거 snapshot으로 덮어 없애지 않는다. 호환되지 않으면 pin/blocked로 유지하고 forward repair를 계획한다.

## 6. v0.1.0 / contract 1에서 v0.2.0 / contract 2로

contract 2는 작업 경계의 자가피드백 검토와 세부 운영 의무를 추가한다. 원본 v0.1.0 태그는 유지한다. 새 설치 도구는 두 manifest contract 번호를 읽지만, 이것은 기존 프로젝트의 의미 호환이나 자동 업그레이드를 증명하지 않는다.

새 버전을 별도 빈 경로에 설치하여 `AGENTS.md`, `BOOTSTRAP_PROMPT.md`, `contract.md`, `contracts/` 변경을 검토한다. 프로젝트가 소유한 객체·이벤트·증거·checkpoint·스킬·overlay와 기존 결정은 보존한다. `feedback/config.json`은 외부 권한 없이 추가하고 필요한 프로젝트 정보만 출처와 함께 설정한다. `templates/` 예제를 실제 사건이나 실행 증거로 등록하지 않는다.

공통 파일의 검토된 diff만 적용하고 overlay의 base contract 변경은 호환성 판단 뒤 기록한다. 기존 설치 영수증은 과거 설치 사실로 보존하며 migration 영수증에 이전/새 원본 manifest, 적용 diff·결정·검사·복구 범위를 남긴다. 새 원본을 그대로 설치했다는 영수증으로 수동 병합을 가장하지 않는다. 전역 스킬 설치·캐시 수정·프로젝트 간 데이터 공유 권한을 이관하지 않는다.

자가피드백 첫 사용에서는 상향 제출 대상, 제출/공유 권한, 로컬 평가 예산 중 필요한 미확정 항목만 인터뷰한다. 설정이 없어도 승인된 로컬 작업과 후보 준비는 계속할 수 있다. 자동 PR, 자동 merge, scheduler, canary, rollback controller는 제공하지 않는다.

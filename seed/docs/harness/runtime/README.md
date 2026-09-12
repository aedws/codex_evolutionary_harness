# 최소 로컬 실행 코어 사용법

`harness.py`는 설정된 로컬 검사 실행 → 입력/출력 관측 → SQLite 이벤트 → 상태 설명 → 로컬 개선 후보를 연결한다. 전체 V2 인증, 위키 서버, OS sandbox, 인간 신원 인증, 외부 배포/승격/Canary controller는 제공하지 않는다.

## 1. 프로젝트에 바인딩

설치 후 프로젝트 목표·원본·필수 검사를 bootstrap에서 확인한다. [policy 예제](policy.example.json)와 [task 예제](task.example.json)를 프로젝트가 소유한 별도 파일로 복사하고 빈 값을 실제 출처로 채운다. 예제는 빈 값 그대로 실행할 수 없다.

- policy: `project_id`, 실제 승인 범위의 `authority_ref`, `commands`의 검사 ID→정확한 argv/시간 제한, 출력 예산.
- argv 첫 항목은 실행 파일의 절대 경로다. Python 경로는 `python -c "import sys; print(sys.executable)"`로 확인할 수 있다. 문자열 shell 명령을 조립하지 않는다.
- task: ID·목적·수락 분류·기준·입력 파일 목록·필수 검사 ID. 검사 스크립트, 관련 코드/데이터/config를 입력에 포함한다. 자동 의존성 탐색은 없으므로 누락된 동적 의존성까지 검증했다고 주장하지 않는다.
- `authority_ref`는 설정을 허용한 결정의 출처다. 문자열만으로 인간 신원이 인증되는 것은 아니다. 정책 파일은 후보 코드와 다른 소유·쓰기 경계에 두는 것이 필요하며, 실제 격리는 실행 환경이 제공해야 한다.

예를 들어 확인된 Python 검사의 command 값은 `{"argv": ["C:/실제/Python/python.exe", "checks/check_project.py"], "timeout_seconds": 30}`처럼 지정한다. 임의의 예제 경로를 실제 검사로 등록하지 않는다. 경로·대상·권한이 미정이면 해당 사실만 인터뷰한다.

## 2. 실행과 조회

아래 명령은 대상 프로젝트 디렉터리에서 실행한다. `project-policy.json`, `task.json`은 위에서 준비한 실제 파일이다. 각 명령의 종료 코드를 확인하고 실패하면 다음 효과를 진행하지 않는다.

```powershell
python harness.py init --policy C:/project-control/project-policy.json
python harness.py task --spec task.json --key task-registration-001
python harness.py run --task TASK-001 --key test-attempt-001
python harness.py status --task TASK-001
python harness.py view --task TASK-001
python harness.py check
```

`init`가 `.harness/ledger.sqlite3`와 그 디렉터리 전용 `.gitignore`를 만든다. 기존 프로젝트의 AGENTS, 수동 JSON/JSONL, checkpoint, Git 설정은 바꾸지 않는다. 같은 초기 설정의 재실행은 no-op이고 다른 설정은 충돌이다. 조회 명령은 원장이 없다고 초기화하거나 복구하지 않는다.

`task`는 엄격한 필드/타입 검사 후 새 revision을 기록한다. 변경은 `--expected-revision 1`처럼 현재 revision을 지정하고 새 operation key를 사용한다. 같은 key에 다른 요청을 주면 충돌이다. 정책에 없는 검사 ID나 변경된 정책은 `run` 직전 차단된다. 직접 `harness.py run` 호출에도 같은 검사가 적용된다.

`run`은 pending 이벤트를 먼저 commit하고 검사 프로세스를 실행한다. stdout/stderr는 제한된 크기의 base64 원본, 결과/종료 코드·시간·명령 digest와 함께 원장에 보존된다. 이벤트 hash chain과 SQL append-only trigger, 단일 writer transaction을 사용한다. 동일 key/동일 입력의 완료 요청은 결과를 재사용하며 실패 결과도 실패 종료 코드를 유지한다. 코드·데이터·task·policy·engine·실행 파일이 바뀌면 이전 pass를 현재 것으로 사용하지 않는다.

`passed`는 **선언된 입력과 설정된 필수 검사 프로세스의 성공**이다. 제품의 모든 요구, 테스트 내용의 적절성, 전체 의존성, 인간 수락을 증명하지 않는다. mixed/human 수락은 `human_pending`, 배포는 `unobserved`로 남는다. `view`는 Task의 목적·상태·근거 이벤트·규칙·다음 행동을 Markdown으로 출력하며 문서를 자동 덮어쓰지 않는다.

## 3. 실패·재시도·복구

| 조건 | 결과 |
|---|---|
| JSON 중복 키/NaN/잘못된 필드·타입·미지원 형식 | 거부; 강한 상태를 만들지 않음 |
| 필수 검사 목록 없음 | unknown; 빈 목록을 pass로 처리하지 않음 |
| 최신 검사 실패 | failed; 이전 pass를 선택하지 않음 |
| 새 시도 시작 후 종료 기록 없음 | running/pending; 다른 효과 실행 차단 |
| 입력 삭제/변경, 검사 중 입력 변경 | stale 또는 blocked; 새 입력 확인 필요 |
| timeout/출력 초과/자식 스트림 불명 | unknown; 새 실행은 중지 확인까지 차단 |
| 같은 key의 다른 입력 | conflict; 새 작업/시도라면 새 key |
| 원장 손상/미지원 사건 | replay 거부; 손상 원본을 보존 |

실행이 실제로 멈췄고 남은 자식 프로세스·외부 효과를 확인한 운영자만 다음과 같이 기록한다. 이는 운영자의 명시적 확인 기록이며 프로세스 사망이나 인간 신원을 자동 인증하지 않는다.

```powershell
python harness.py reconcile --run RUN-ID --reason "중지와 잔여 효과를 확인한 실제 근거" --key reconciliation-001 --confirm-stopped
python harness.py invalidate --run RUN-ID --reason "무효화의 실제 근거" --key invalidation-001
python harness.py backup --out C:/project-backups/ledger-001.json
python harness.py --root C:/inspection-copy restore --backup C:/project-backups/ledger-001.json
```

백업은 고정된 이벤트 snapshot과 hash chain이다. 별도 경로에 복원하여 사건 동일성과 조회를 검증할 수 있다. 더 늦은 사건이 있는 활성 원장은 덮어쓰지 않는다. 같은 백업의 재실행은 no-op이다. 새 경로에 복원된 원장에는 원래 경로의 실행 권한을 옮기지 않으므로 검사 실행이 차단된다. 제품 코드/외부 데이터는 별도 백업 대상이고 이 원장 백업이 이를 복원하지 않는다.

## 4. 피드백과 버전

`candidate --spec candidate.json --key candidate-001`는 [후보 형식](candidate.example.json)의 task/run 참조를 검증하고 `local_proposal_only`로 기록한다. 같은 후보 ID나 operation key를 중복 의미로 재사용할 수 없다. scope=core는 제안 범위일 뿐 승인·전송·승격이 아니다. 알려진 run 없이 좋은 설명만 써서 후보 근거를 만들 수 없다. 반복 관측의 분류·원인 판단·평가·승격에는 F/E 계약을 계속 적용한다.

원장은 storage schema 1, task/policy schema 1, rule `local-verification-1`, protocol `local-core-1`을 사용한다. 원본 engine·policy를 init에 pin하므로 변경 시 실행이 멈춘다. 정책 확대/engine·storage 이관은 이 릴리스에서 자동 제공하지 않는다. 이전 원장·runner·policy·프로젝트 snapshot을 보존하고 명시적 migration/검증 계획을 세운다. 새 engine을 덮어쓴 뒤 기존 기록을 새 것으로 선언하지 않는다.

현재 수동 `docs/harness/objects.json` 등은 외부 의도/이전 이력이다. 코어가 관리하는 task revision·검사 관측의 원본은 `.harness` 원장이고 문서는 그 출력의 projection으로 연결한다. 과거 수동 passed/approved를 자동 import하지 않는다. 원장의 raw 출력과 절대 policy 경로는 프로젝트 로컬 자료이며 upstream에 자동 공유하지 않는다.

## 5. 정확한 강제 범위와 한계

코어는 자신의 `run` 진입점에서 고정된 argv 목록·정책/입력 digest·pending 상태를 검사한다. 임의의 외부 shell/API, OS 관리자, 원장 파일 소유자를 통제하거나 `authority_ref`의 인간 신원을 인증하지 않는다. 별도 OS/credential/policy adapter 없이 권한이 분리된 자율 시스템이라고 표현하지 않는다.

검사는 최대 32개, 개별 timeout은 1~300초, 출력은 stream당 1KiB~1MiB, 입력은 최대 256개 파일·개별 64MiB다. 선택된 timeout의 합에 시작/조회 비용이 더해지며 전체 OS 자원 한도는 아니다. 한 프로세스의 timeout/출력은 제한하지만 자식의 자식이나 네트워크/파일 부작용을 sandbox하지 않으므로 불명 상태를 보존한다. 백업/복원 형식 한도는 64MiB이며 대규모 원장은 별도 이관이 필요하다.

명령 JSON에는 outcome과 근거가 포함된다. 종료 코드는 0=요청 정상 처리(관측/조회 상태 자체의 성공 인증 아님), 2=구조/필드/미지원 형식, 4=미설정/허용되지 않은 검사·확인, 5=I/O·충돌·원장 문제, 6=검사를 실행했으나 완료 결과가 passed 아님이다. argparse 인자 오류는 표준 usage/exit 2다. `check`는 기록의 구조·계보·무결성을 검사하며 실제 인간 승인·외부 효과를 증명하지 않는다.

CLI 출력은 리다이렉션을 포함해 UTF-8이다. 같은 operation key의 `run` 재조회는 해당 시도의 원래 완료 결과이며 최신 Task의 수락 인증이 아니다. 후속 무효화와 더 늦은 시도를 포함한 현재 판정은 `status`로 확인한다. init/restore 도중 프로세스가 중단되면 부분 DB가 남을 수 있다. 다음 호출은 이를 자동 초기화하거나 삭제하지 않고 오류를 반환한다. 부분 원본을 보존하고 검증된 백업을 새 경로에서 검사한다.

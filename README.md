# Evolutionary Harness — reusable contract seed

**View to OOP, Set up to DOP.** 사람은 객체와 목적을 다루고, 시스템은 데이터와 증거를 다룬다.

모든 프로젝트가 공통 코어에서 시작하고 Overlay로 특화한다. 실제 실패·마찰·검증에서 얻은 개선은 Project → Domain → Universal Core로 평가·승격하고, 상위 변경은 호환성 검증·Canary·Rollback을 통해 다시 전파한다.

현재 배포물은 **v0.2.0 계약 씨앗**이다. 전체 위키 UI, 자동 상태 계산기, 정책 집행 엔진, 자기개선·승격·Canary 실행기는 아직 구현하지 않았다. V2/V3/V4는 목표 능력이며 배포 버전과 다르다.

## 먼저 읽기

1. [사용자가 확정한 목표와 17개 원칙](docs/requirements/HARNESS-GOALS.md)
2. [상위 아키텍처 RFC-0002](docs/rfcs/RFC-0002-hierarchical-evolutionary-architecture.md)
3. [재사용되는 최소 계약](seed/docs/harness/contract.md)
4. [가져오기·업데이트·되돌리기](docs/REUSE.md)
5. [하위 CLI 설계 제안 RFC-0001](docs/rfcs/RFC-0001-evolutionary-harness-cli.md)
6. [자가피드백 공통 계약 RFC-0003](docs/rfcs/RFC-0003-feedback-common-contract.md)와 [17개 목표 연결표](seed/docs/harness/contracts/coverage.json)

오류 개선·스킬 사용/추가/수정/제거는 작업 종료 시 한 번 검토한다. 일반화 근거가 있으면 로컬 후보를 만들고, 승인된 제출 → 범위별 평가 → 새 씨앗 릴리스 → 프로젝트의 명시적 적용 → 효과 재관측으로 연결한다. 초기 설정은 외부 제출 권한이 없는 local-only다. 자세한 계약은 필요한 항목만 읽는다.

## 새 프로젝트에 가져오기

GitHub 인증이 된 환경에서 실행한다. Python 3.10 이상, Git, GitHub CLI가 필요하다. 전체 하네스 저장소를 대상 프로젝트 안에 clone하지 않는다.

```powershell
gh repo clone aedws/codex_evolutionary_harness C:/tools/evolutionary-harness
git -C C:/tools/evolutionary-harness checkout v0.2.0
python C:/tools/evolutionary-harness/scripts/seed.py check
python C:/tools/evolutionary-harness/scripts/seed.py init --target C:/projects/my-project --dry-run
python C:/tools/evolutionary-harness/scripts/seed.py init --target C:/projects/my-project
```

대상 경로는 자신의 환경에 맞춘다. 기존 프로젝트에도 사용할 수 있지만 `AGENTS.md` 등을 포함한 설치 경로가 이미 있으면 전체 작업을 중단한다. 기존 파일을 자동 병합하거나 덮어쓰지 않는다. 같은 씨앗을 같은 대상에 다시 실행하면 설치 영수증과 파일 해시를 확인하여 no-op으로 끝난다. 이후 기록이나 계약이 바뀌었다면 재설치 대신 업데이트 절차를 사용한다.

설치 후 대상 프로젝트의 `BOOTSTRAP_PROMPT.md`로 AI에게 첫 읽기·현황 조사·프로젝트 Overlay 설정을 요청한다. 목표가 불분명하거나 기존 정책과 충돌하면 필요한 항목만 인터뷰한다. 제품 구현, GitHub 배포, 외부 쓰기 권한을 씨앗이 자동으로 부여하지 않는다.

## 배포 경계

- `seed/`: 새 프로젝트로 복사하는 공통 계약과 빈 기록. 프로젝트 경험·감사 이력·계정 정보 없음.
- `scripts/seed.py`: 씨앗 검증·충돌 없는 복사·ZIP 생성용 작은 유틸리티. RFC의 `eh` CLI가 아님.
- `scripts/check_contracts.py`: 17개 목표·조항 참조·링크·안전한 배포 기본값 검사. 의미 검증이나 자동 피드백 실행기가 아님.
- `docs/requirements`, `docs/rfcs`: 목표와 설계.
- `docs/harness`: 이 하네스 자체를 개발한 기록. **다른 프로젝트로 복사하지 않음.**
- `.local/`, `dist/`: 로컬 실행 영수증·배포 산출물. Git 제외.

GitHub 저장소는 비공개로 운영한다. 재사용은 태그와 파일 해시로 버전을 고정하며, 기존 태그를 이동시키지 않는다. 공개 라이선스를 임의로 부여하지 않는다.

배포 원본 검사는 `python scripts/seed.py check`, `python scripts/check_contracts.py`, `python -m unittest discover -s tests -v`로 실행한다. 실제 프로젝트에서 설정·기록을 채운 뒤에는 빈 배포 원본 전용 검사를 프로젝트 검증기로 사용하지 않는다.

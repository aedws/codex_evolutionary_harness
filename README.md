# Evolutionary Harness — 고정 V2 씨앗

## 먼저 사용하는 방법

이 저장소의 기본 씨앗은 **고정 V2 → 관측 → 준비 판정 → 제한된 특화 → 비교 평가 → 고정 V3** 구조입니다. 배포 버전은 `2.0.0-dev.2`이며 **로컬 검증용 개발 배포본**입니다. V2/V3는 프로젝트 운용 단계입니다.

```powershell
# 이 저장소를 원하는 commit으로 고정한 다음, Python 3.10+에서 실행
python -B scripts/seed.py check
python -B scripts/seed.py init --target C:/projects/my-project --dry-run
python -B scripts/seed.py init --target C:/projects/my-project
```

기존 파일/원장과 충돌하면 덮어쓰지 않습니다. 새 경로에 설치해 도입을 검증하세요. 설치 직후 `C:/projects/my-project/wiki/index.html`에 객체 위키 초안이 생성됩니다. 대상 프로젝트의 `AGENTS.md`와 `docs/harness/README.md`를 읽고 오너 인터뷰 → 실제 원본·검사 연결 → 첫 작업으로 진행합니다. 설치만으로 bootstrap/MVP/V3가 완료되지는 않습니다.

실제 프로젝트와 분리된 **합성 예제 전체 흐름**을 바로 확인하려면:

```powershell
python -B scripts/demo.py
```

이 명령은 새 임시 로컬 프로젝트를 만들고 실제 CLI로 설치·검사·관측·준비 판정·후보·비교·V3 채택을 실행합니다. 마지막 JSON이 위키 경로와 근거 경로를 알려줍니다. 예제의 오너 결정은 합성 데이터이며 실제 프로젝트 승인이 아닙니다. 외부 API/비용/배포는 사용하지 않습니다.

- [대상 프로젝트 사용법](seed/docs/harness/README.md)
- [정확한 CLI·상태·복구 계약](seed/docs/harness/contract.md)
- [새 상위 설계 RFC-0016](docs/rfcs/RFC-0016-fixed-v2-specialized-v3.md)
- [요구사항 대응표](docs/requirements/FIXED-V2-GOALS.md)
- [검증 근거](docs/harness/evidence/EXE-20260916-V2-REWRITE-001/validation.json)

## 무엇이 고정되고 무엇이 바뀌는가

| 영역 | 처리 |
|---|---|
| 객체/이벤트/근거, 상태 계산, CLI 권한, 준비·채택 조건 | 같은 실행 파일과 계약으로 고정 |
| 프로젝트 코드·테스트·원본 | 오너가 등록한 어댑터와 입력 목록으로 연결 |
| 별칭, 읽기 순서, 표시 형식, 모듈 탐색, 체크리스트 | 관측 후 후보 공간에서만 수정 |
| 권한·보존·검증 기준·원본 권위·배포 | 습관으로 변경 불가 |
| V3 | 별도 평가 + 오너 채택 후 고정; 기존 Task는 시작 config 유지 |

**View to OOP, Set up to DOP.** 위키는 큰 대문 → 6가지 주제 → 객체 상세로 구성합니다. 객체는 상태별로 모으고 관계와 원본·판정 경로를 보여줍니다. Run/관측/평가를 새 보고서 노드로 복제하지 않습니다.

V2 유지도 정상 결과입니다. 준비되었다는 이벤트는 탐색 시작 근거이며 V3 승격 증거가 아닙니다. 현재 자동 후보 생성은 명시된 관측 suggestion을 정규화하는 유한한 로컬 실행이며 LLM 자기개선으로 과장하지 않습니다.

## 검증과 한계

```powershell
python -B -m unittest discover -s tests -v
python -B scripts/seed.py check
python -B scripts/seed.py pack --out dist/fixed-v2-dev2.zip
```

권한·상태·고정 운용의 로컬 계약과 명령 해석 비교를 검증합니다. 실제 LLM 품질 향상/독립 프로젝트 일반화/원격 인증/배포/상위 승격까지 검증한 배포본은 아닙니다. 각 역할은 오프라인 operator label이며 인증된 독립 사용자라는 뜻이 아닙니다. 테스트 스크립트는 신뢰한 프로젝트 코드이고 OS sandbox는 아닙니다.

## 기존 버전 보존

v0.12.0의 씨앗·실행기·배포 도구·테스트·README·manifest를 [legacy/v0.12.0](legacy/v0.12.0/README.md)에 원본 bytes 그대로 보존했습니다. 이전 설계/근거/이벤트도 삭제하지 않았습니다. 과거 문서의 `seed/` 참조는 해당 보존 경로의 씨앗을 의미하며 새로운 V2 실행 계약으로 간주하지 않습니다. v0.12의 ledger를 새 실행기에 자동 이관하지 않습니다.

현 AI-Agent-Execution-Platform에는 새 씨앗을 덮어쓰지 않았습니다. 별도 검증 후 선택 도입하는 기존 결정은 유지합니다. 이전 기능 동등성 계획 RFC-0015는 역사 자료이며 현재 구현 우선순위는 정리.txt를 반영한 RFC-0016입니다.

## SFH 추출과 ATP 셋업 인계 — 2026-09-20

[전체 추출 일정](docs/rfcs/RFC-0017-sfh-full-extraction-schedule.md)은 12단계이며, [기준 계약 목록](docs/requirements/sfh-contract-catalog.json)은 23개 계약군을 다룹니다. 1,362개 추적 파일을 누락 없이 배정하고 객체 257개·관계 483개의 필드를 원본과 대조했습니다. 전수 의미 검토와 전체 기능 동등성은 아직 미검증입니다.

`source_catalog.py`와 [출처 보존 계약](seed/docs/harness/source-extraction.md)을 새 개발 배포본에 포함했습니다. 2.0.0-dev.1의 11개 payload 파일은 `legacy/2.0.0-dev.1/`에 보존했으며 기존 설치는 교체하지 않습니다.

ATP에는 고정 배포본과 자체 원본·검사 연결, 읽기 검사 및 객체 위키 초안을 준비합니다. 현재 인계는 셋업까지이며 실행기 활성화·제품 배포·전체 SFH 동등성 인증과 구분합니다. 남은 일정은 보존하고 자동 후속 작업은 등록하지 않습니다.

# 출처를 보존하는 객체 추출

`source_catalog.py`는 ontology-snapshot-1 형식의 객체·관계·인터페이스·행동·생애주기 원본을 로컬 파일로 추출합니다. 원본의 모든 필드와 출처, 관계 종류를 보존하며 원본과 재구성 결과를 비교합니다.

```powershell
python -B source_catalog.py extract --source ontology.json --namespace myproject --revision FULL_COMMIT_SHA --out snapshots/first.json
python -B source_catalog.py verify --bundle snapshots/first.json --source ontology.json
```

같은 출력은 재실행해도 변경하지 않습니다. 다른 내용이 이미 있으면 거절하므로 새 revision과 경로를 사용합니다. 끊긴 출력도 덮어쓰지 않고 보존합니다. JSON 중복 키, 끊긴 관계, 필수 필드 누락, 변조된 파생 필드와 권한 선언은 오류입니다.

사람이 다루는 작업·모듈·결정은 OOP 대상이고 문서·출처·권한 선언은 DOP 보조 데이터입니다. 원본의 `verified` 문구나 `verified_by` 관계만으로 새 실행기가 검증 완료 상태를 만들지 않습니다. 기본 검증 상태는 unverified, 실행 동등성은 미확인, 오너 수락은 pending입니다. 원본 계정·권한은 활성화되지 않습니다.

이 도구는 선언된 구조의 보존 검사입니다. 선언 내용의 진실성, 실제 인증·도구 권한, 외부 배포, 프로젝트 품질을 검증하지 않습니다. 씨앗 원장과 자동 연결하지 않으며 원본 자료는 배포 payload에 포함하지 않습니다. 실제 프로젝트의 입력·검사·승인 계약을 등록하는 단계는 별도입니다.

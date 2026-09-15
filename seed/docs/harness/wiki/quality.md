# 자동 위키 품질 계약 — wiki-quality-1

설치 시 객체 위키와 함께 `.local/wiki-draft/quality.json`이 자동 생성된다. structure_passed는 구조 검사 결과이며 시각 수락·bootstrap 완료가 아니다.

## 기본 순서

```powershell
python -B wiki_quality.py check --site .local/wiki-draft --contract .local/wiki-draft/quality-contract.json
python -B wiki_quality.py review-template --site .local/wiki-draft --contract .local/wiki-draft/quality-contract.json
```

둘째 명령은 출력만 한다. 새 경로에 저장할 때 기존 기록을 덮어쓰지 않는다. 템플릿은 빈 관찰자/이미지와 false 판정이므로 완료 gate를 통과하지 않는다.

프로젝트에 맞게 위키를 작성하고 generator가 품질 계약도 생성하게 한다. `schema_version:1`, `profile:wiki-quality-1`, `mode:project`, `pages`, `source_bindings`만 사용한다. pages는 ID→{kind,parent} 사전이고 object는 object_type도 필요하다. 고정 ID는 index/objects/sources/start/product/design/modules/workflows/quality/decisions/history/workspaces다. 나머지는 requirement/task/decision/module/test/release 객체다. 전체 6종을 포함한다. 파일명은 ID.html. 각 객체 parent는 주제 ID이며 양방향 링크를 제공한다.

각 View의 현재 안내는 `source_bindings:[{page:ID,path:프로젝트상대경로,sha256:실제파일SHA256}]`에 하나 이상의 출처를 연결한다. 출처 파일 변경은 차단한다. 낡은 안내를 고칠 때 관련 결정·실행 근거를 읽고 의미도 정정한 뒤 새 snapshot을 생성한다. 해시를 갱신하는 것만으로 서술이 옳아지는 것은 아니다. 원본 권위·현재 상태 reducer·버전 고정은 기존 계약을 유지한다.

## 화면 점검

agent는 사용 가능한 브라우저 도구로 참조 화면과 생성 위키를 직접 본다. 대문/주제/객체 각각 390px와 1280px viewport에서 잘림·읽기·계층·노드 이동·접기를 확인한다. PNG를 프로젝트 내부 근거 경로에 저장하고 바이트 해시를 기록한다. 관찰 시의 HTML hash와 품질 snapshot을 기록한다. 도구가 없거나 로그인/권한으로 접근할 수 없으면 실패/미확인을 설명하고 시각 기록을 지어내지 않는다. 사용자/프로젝트 비공개 화면은 로컬에만 보존하며 배포 씨앗에 포함하지 않는다.

`reference:{label,image:{path,sha256}}`, `observer`, `snapshot`, `observations`를 채운다. 각 observation은 page(파일명), width(390/1280), html_sha256, image{path,sha256}, checks{no_clipping,text_readable,hierarchy_clear,node_links_usable,details_usable}다. viewport와 PNG는 device scale 1~3을 허용한다. 구조/출처/HTML/이미지가 바뀌면 재검토한다. 관찰 bool은 실제 도구 관찰의 기록이며 신원 인증이나 인간 승인이 아니다.

## 최종 완료 경로

```powershell
python -B wiki_quality.py gate --site docs/wiki/site --contract docs/wiki/quality-contract.json --review docs/harness/evidence/EXE-ID/wiki-visual.json --binding .local/bootstrap-binding.json
```

필수 harness 검사에 `wiki_quality.py check`를 등록하고, 현재 Run 확보 뒤 최종 wrapper를 실행한다. 실행 순서는 생성→구조 검사→화면 관찰→필수 Run→위키/바인딩 재생성→최종 gate다. 재생성으로 화면 snapshot이 바뀌면 새 기록을 작성하고, 실패는 보존한다. 이 경로가 wiki_review_ready를 반환하기 전에는 위키 품질 완료를 보고하지 않는다. 기존 bootstrap.py 단독 성공은 새 시각 품질 gate 성공이 아니다.

wiki_template.py는 기존 호환성을 유지한다. 새 프로필에서는 그래프·계보·한국어 필수 표제 등 adapter 조건을 채워야 한다. 기존 프로젝트는 동등성 검사/오너 역할 인터뷰/호환성과 rollback을 확인해 별도로 채택한다. 정적 감사는 가독성의 일부 조건만 측정하고, 디자인의 적절성과 인간 수락은 human_pending으로 남긴다.

필수 테스트 ID는 `wiki-quality`다. 고정 argv는 `[Python절대경로, "-B", "wiki_quality.py", "check", "--site", 사이트상대경로, "--contract", 계약상대경로]`다. `wiki_quality.py`, 품질 계약 파일, 모든 source_bindings 경로를 Task target_paths에 포함한다. 최종 gate는 그 Run과 명령·파일을 검사한다. 이미 pin된 policy를 자동 수정하지 말고 기존 프로젝트의 변경/재채택 절차를 따른다. bootstrap binding은 감사한 사이트의 모든 HTML을 정확히 같은 해시로 포함해야 한다. 다른 위키의 bootstrap 통과를 가져와 쓸 수 없다.

---
title: 작업 일지 (WORKLOG) — Unreal
aliases: [WORKLOG, 작업일지, devlog, UE 작업일지]
tags: [worklog, unreal, unreal-python]
updated: 2026-08-14
---

# 작업 일지 (WORKLOG) — Unreal

git 커밋 기록을 근거로 하루 작업을 요약한다. 최신 날짜가 위.
마야 쪽 일지는 `Maya_Python/JUN_All/docs/WORKLOG.md` 에 따로 있다.

> [!info] 보기
> Obsidian 에서 `JUN_UE/Docs` 를 vault(또는 폴더)로 열면 속성/태그/링크가 동작한다.
> 굵게/링크가 별표째 보이면 소스 모드이므로 `Ctrl+E` 로 읽기/라이브 프리뷰 전환.

---

## 2026-08-14 (오늘)

> [!summary] `A00510_bone_viewport` **스켈레탈 메시 뷰포트 본 표시 설정** (v01.00→01.01) `8cbab30`
- 본 크기를 정할 때마다 **눈 아이콘 > Bones > All Hierarchy** 를 타고 들어가야 하는 불편에서 출발.
  `Show All Bones` 로 **3단계 클릭을 메뉴 한 번**으로 줄이고, `Bone Display Settings...` 팝업에
  Bone Draw Mode 드롭다운 + Show Bone Colors 체크박스를 담았다.
- **요청한 두 기능 중 Bone Draw Size 는 넣지 못했다.** `FAnimationViewportClient::BoneDrawSize` 는
  `UPROPERTY` 도 `UFUNCTION` 도 아닌 **평범한 C++ 멤버**라 리플렉션이 없다 — 파이썬에서 접근할
  통로가 존재하지 않는다. 에디터를 열 때마다 1.0 으로 리셋되는 것도 같은 이유.
  C++ 에디터 모듈이면 `IPersonaViewport::GetViewportClient()` → `SetBoneDrawSize()` 로 가능하지만
  그 순간 플러그인이 컴파일 대상이 되고 엔진 빌드에 묶이므로, **C++ 없이 되는 범위까지만** 만들기로
  결정했다([설계 가이드 3장](00_UE_Tool_Plugin_Guide.md)).
- **파이썬 클래스가 없는 UObject 를 다루는 법**을 확립했다. `unreal.PersonaOptions` 는 생성되지
  않으므로 CDO 를 경로로 직접 잡는다(`unreal.find_object(None, "/Script/UnrealEd.Default__PersonaOptions")`).
  이때 프로퍼티 이름은 파이썬 관례가 아니라 **C++ 원본 이름**(`DefaultBoneDrawSelection`, 5=All Hierarchy).
- **C++ 없이 입력 위젯을 만드는 패턴**도 여기서 확립했다 — `@unreal.uenum()` 은 드롭다운으로,
  `uproperty(bool)` 은 체크박스로 그려지고 `EditorDialog.show_object_details_view()` 로 띄운다.
  앞으로 다른 툴에 그대로 재사용한다.
- **한계 두 가지를 문서에 근거와 함께 남겼다**: 파이썬에 `SaveConfig()` 가 없어 설정이 **세션 한정**이고,
  이미 열려 있는 뷰포트는 엔진이 `BonesToDraw` 를 캐시하므로 **본 선택을 한 번 바꿔야** 갱신된다.
- `ToolSpec.package` 추가 — 한 툴이 메뉴 항목을 여러 개 가질 때 DEV_MODE 리로드가 볼 폴더.
- 검증(헤드리스) 19항목: 모드 읽기/쓰기 왕복, `apply()` 변경 목록, quick 액션,
  다이얼로그 3회 연속 실행(리로드로 uclass/uenum 이 재등록되는 경로 포함). #A00510

> [!summary] **junction 설명 문서** (`Docs/01_Junction_Guide.md`) `5479d6d`
- 설치 안내에 계속 등장하는 `mklink /J` 가 무엇인지 따로 정리했다. **사본이 아니라 입구가 둘**이라는
  점, 바로가기(`.lnk`)는 탐색기만 해석하지만 junction 은 **파일 시스템이 처리**해서 언리얼도 진짜
  폴더로 본다는 차이, `mklink /D`(심볼릭 링크)와 달리 **관리자 권한이 필요 없다**는 점.
- **지울 때가 제일 위험하다**: `Remove-Item -Recurse` 는 링크를 따라가 원본까지 지울 수 있으므로
  `[System.IO.Directory]::Delete(path, $false)` 로 링크만 제거한다. 원본이 git 저장소라 더 그렇다.
- 버전 관리 주의도 함께 — `Plugins/` 안에 걸면 SVN 이 링크를 따라 원본을 커밋하려 들 수 있다. #Docs

> [!summary] **배포 방식을 `UE_ADDITIONAL_PLUGIN_PATHS` 환경변수 우선으로 재정리** `b2f1a1a`
- 프로젝트마다 `Plugins/` 에 복사·붙여넣기 하던 방식을 대체했다. 엔진에 **플러그인 스테이징용
  환경변수**가 있다 — 소스 주석에 *"traditional DCC film pipelines where plugins can be staged"* 라고
  용도가 그대로 적혀 있다. PC 에 한 번 걸면 **모든 프로젝트가 인식**하고 프로젝트 파일은 하나도
  건드리지 않는다. Windows 구분자는 `;`, 에디터 전용이라 패키징된 게임엔 영향이 없다.
- **MANUProject 에서 특히 유리하다**: 그 프로젝트는 SVN(전체) + Git(Source/Config/Plugins) 이중
  관리라, `Plugins/` 에 개인 툴을 두면 회사 버전 관리에 딸려 올라갈 수 있다.
- 우선순위를 **환경변수 > junction > submodule > 복사** 로 다시 세우고, 같은 이름 플러그인이 두
  곳에서 발견되면 엔진이 하나만 채택한다는 주의(사본을 먼저 지울 것)도 적었다.
- 검증(헤드리스): 프로젝트 `Plugins/` 를 **완전히 비운 상태**에서 환경변수만으로 로드 —
  `LogPluginManager: Mounting External plugin JUNTools`, 15/15 통과. #Docs

> [!summary] `JUNTools` **언리얼 에디터 툴 플러그인 초기 구성 + Hello 테스트 툴** (v01.00) `4dea019`
- 마야 툴 모음(`JUN_All`)과 같은 발상을 언리얼로 옮기는 첫 삽. **저장소 루트가 곧 플러그인**이라
  어떤 프로젝트에서든 `Plugins/JUNTools` 로 submodule/junction 한 방에 붙는다.
- **C++ 모듈 0개인 Python 콘텐츠 플러그인으로 시작**했다. 언리얼은 활성화된 플러그인의
  `Content/Python` 을 `sys.path` 에 넣고 `init_unreal.py` 를 자동 실행한다 — 마야에서
  `__dragDrop_A000XX.py` 로 셸프 버튼을 깔던 자리와 정확히 대응된다. C++ 은 Python API 로 막히는
  지점이 나올 때 같은 플러그인에 얹는다.
- **플러그인 1개 + 내부 툴 레지스트리** 구조. `registry.py` 에 `ToolSpec` 한 줄을 더하면 메뉴가
  자동으로 그려지고, 메뉴가 실행하는 명령은 전부 `jun_tools.run("<tool_id>")` 로 통일했다
  (마야의 `tools.A000XX.run(True)` 와 같은 구조). Tools 메뉴가 난장판이 되지 않도록 **"JUN" 하위
  메뉴 하나**만 만들고 그 안에서 섹션으로 나눈다.
- 등록/해제를 **owner 이름으로 묶어** 몇 번을 호출해도 메뉴가 중복되지 않게 했고,
  `Reload JUN Tools` 로 에디터 재시작 없이 코드를 다시 읽는다(마야 `reloader_v02` 대응).
  `init_unreal.py` 는 예외를 삼키지 않고 로그로 남기되 **에디터 부팅은 막지 않는다**.
- `.uplugin` 에 `EngineVersion` 을 **비워** 특정 엔진에 고정되지 않게 하고,
  `EnabledByDefault` 로 `.uproject` 등록 없이도 마운트되게 했다.
- `A00500_hello` — 팝업 → OK → Output Log 에 `Hello`. core/ui 분리 템플릿이자
  **플러그인 배선 전체를 한 번의 클릭으로 검증**하는 도구.
- 설계 판단은 [설계 가이드](00_UE_Tool_Plugin_Guide.md) 에 근거와 함께 정리했다 —
  왜 C++ 을 미뤘는지(사내 커스텀 엔진 빌드 문제 포함), 플러그인 이름을 왜 못 바꾸는지,
  왜 마야 저장소와 분리했는지, 함정 모음.
- 검증(헤드리스, `MANU_Engine_Prebuilt` 5.7.4) 15항목: 플러그인 자동 마운트, `init_unreal.py`
  실행(32ms), `ToolMenus` / `EditorDialog` API 존재, `-unattended` 다이얼로그 기본값 반환. #JUNTools

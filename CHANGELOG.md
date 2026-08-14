# CHANGELOG — JUNTools

## v01.01 (2026-08-14)

### Added
- `A00510_bone_viewport` — 스켈레탈 메시 뷰포트 본 표시 설정.
  - `Show All Bones` : 눈 아이콘 > Bones > All Hierarchy 3단계를 메뉴 클릭 한 번으로
  - `Bone Display Settings...` : Bone Draw Mode 드롭다운 + Show Bone Colors 체크박스 팝업
  - 파이썬 `@unreal.uenum()` / `@unreal.uclass()` + `EditorDialog.show_object_details_view()` 로
    C++ 없이 드롭다운·체크박스 위젯을 만드는 패턴 확립
- `ToolSpec.package` — 한 툴이 메뉴 항목을 여러 개 가질 때 DEV_MODE 리로드가 참조할 폴더.

### Known limitation
**Bone Draw Size 는 넣지 못했다.** `FAnimationViewportClient::BoneDrawSize` 는 `UPROPERTY` 도
`UFUNCTION` 도 아닌 평범한 C++ 멤버라 리플렉션이 없다 → 파이썬에서 접근 불가.
C++ 에디터 모듈이 있어야 한다(`IPersonaViewport::GetViewportClient()` → `SetBoneDrawSize()`).
자세한 내용은 `Docs/Tools/A00510_BoneViewport.md`.

또한 파이썬에는 `SaveConfig()` 가 없어 설정이 **이번 에디터 세션 동안만** 유지되고,
이미 열려 있는 뷰포트는 본 선택을 한 번 바꿔야 갱신된다(엔진이 그릴 본 목록을 캐시하기 때문).

### Verified
헤드리스 19/19 통과 — 모드 읽기/쓰기 왕복, quick 액션, 다이얼로그 3회 연속 실행
(DEV_MODE 리로드로 uclass/uenum 이 재등록돼도 에러 없음).

## Docs (2026-08-14) — junction

### Added
- `Docs/01_Junction_Guide.md` — junction 이 무엇인지, 복사·바로가기와 무엇이 다른지,
  만들기/확인/**안전하게 지우기**, 버전 관리(SVN/Perforce)와의 충돌 주의.
  README / 설계 가이드 6장에서 링크.

## Docs (2026-08-14)

### Changed
- 배포 방식 정리. 프로젝트마다 복사·붙여넣기 대신 **`UE_ADDITIONAL_PLUGIN_PATHS` 환경변수**를
  1순위로 문서화 (README / 가이드 6장). PC에 한 번 걸면 모든 프로젝트가 인식하고
  프로젝트 파일을 건드리지 않는다 — SVN+Git 이중 관리인 MANUProject 에서 특히 유리.
- 같은 이름 플러그인이 두 곳에서 발견될 때의 주의, 폴더 이름과 `.uplugin` 이름의 관계 추가.

### Verified
프로젝트 `Plugins/` 를 **완전히 비운 상태**에서 환경변수만으로 로드되는 것을 헤드리스로 확인.
`LogPluginManager: Mounting External plugin JUNTools` → 15/15 통과.

## v01.00 (2026-08-14)

최초 버전. 플러그인 골격 + 테스트 툴 1개.

### Added
- `JUNTools.uplugin` — C++ 모듈 없는 Python 콘텐츠 플러그인.
  `EnabledByDefault: true`, 의존 플러그인으로 `PythonScriptPlugin` / `EditorScriptingUtilities` 선언.
  `EngineVersion`은 의도적으로 비워 특정 엔진에 고정되지 않게 함.
- `Content/Python/init_unreal.py` — 에디터 부팅 훅. 메뉴만 등록하고 툴 모듈은 지연 로딩.
  예외를 삼키지 않고 로그로 남긴다.
- `jun_tools` 패키지 — `run()` / `reload_all()`, `registry` / `menu` / `config` / `version`.
- `Tools > JUN` 메뉴. owner 이름 기준 등록/해제로 중복 방지, 섹션 분리, `Reload JUN Tools` 포함.
- `A00500_hello` — 테스트 툴. 팝업 → OK → Output Log에 `Hello`.
- `Docs/00_UE_Tool_Plugin_Guide.md` — 설계 가이드, 저장소 분리 판단 근거, 함정 모음.

### Verified
`MANU_Engine_Prebuilt` (5.7.4, Installed Build)에서 헤드리스 실행으로 15개 항목 전부 통과.
- 플러그인이 `.uproject`에 명시되지 않아도 자동 마운트 (`Mounting Project plugin JUNTools`)
- `init_unreal.py` 자동 실행 (32ms) → 메뉴 등록 성공
- `unreal.EditorDialog.show_message`, `AppMsgType` / `AppReturnType`, `ToolMenus` API 존재 확인
- `-unattended` 모드에서 다이얼로그가 기본값(CANCEL)을 반환하는 동작 확인

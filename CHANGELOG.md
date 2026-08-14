# CHANGELOG — JUNTools

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

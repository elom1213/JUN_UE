# Memory Index — JUN_UE

한 줄 = 한 메모. 자세한 내용은 각 파일에 있으니 필요할 때 열어본다.

**저장소 규칙(플러그인 구조 · 검증 방법 · 함정)은 루트 `CLAUDE.md` 에 있다.**
모든 세션 공통 규칙(한국어 · 푸시 · 커밋)은 `JUN_Claude/CLAUDE.md` 가 전역으로 로드한다.

- [JUN_UE 분리 배경 · 푸시 대상 함정](jun-ue-plugin-repo.md) — 왜 마야 repo 에 안 섞었나, origin/main (Dnable_repo 아님)
- [UE 파이썬 헤드리스 검증](unreal-python-tool-verify.md) — `UnrealEditor-Cmd -run=pythonscript` + 실측 확인된 동작 (자동 마운트, EditorDialog, UE_ADDITIONAL_PLUGIN_PATHS, sys.path 충돌, **CallInEditor 버튼으로 모달 안에서 창 안 닫고 실행**)
- [A00530 JUN Renamer](wip-a00530-jun-renamer.md) — Asset Renamer 이식 + Trim/Copy Name. EUW 도킹 탭, v01.02 루트 VerticalBox `Root` + 파이썬 조립 UI 스파이크(화면 확인 대기). EUW 는 5.4 저장. UI 영어만
- [A00510 Bone Viewport](wip-a00510-bone-viewport.md) — PersonaOptions CDO 로 본 draw mode. `BoneDrawSize` 는 리플렉션이 없어 C++ 아니면 불가. 팝업은 Apply/Reset 버튼으로 창 유지

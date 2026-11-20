# CHANGELOG — JUNTools

## v01.10 (2026-11-20)

### Fixed
- `A00530_jun_renamer` v01.06 — **`Mode:` · Match 콤보에서 고른 값이 검정으로 안 보이던 문제.**
  `UComboBoxString` 생성자가 글자색(`ForegroundColor`)을 게임 스타일 글자색(검정)으로 정하고, `EditorUtilityComboBoxString` 은
  배경만 에디터 스타일로 바꾼다. 공용 헬퍼 `umg.combo()` 가 위젯이 그려지기 전에 글자색을 에디터 글자색으로 지정한다
  (공용 위젯이라 이 헬퍼를 쓰는 모든 콤보에 적용).

### Verified
- `verify_a00530_renamer.py` — UE 5.4.4 · 5.7.4 **73/73** (콤보 글자색 검사 추가), 에러 로그 0.

## v01.09 (2026-11-20)

### Changed
- `A00530_jun_renamer` v01.05 — **설정 패널에서 위쪽 화면과 겹치는 항목 제거.**
  - Rename 섹션: `Search` · `Replace` · `Match` · `Rename Preview` · `Preview` 버튼 제거.
  - Assets 섹션: `Loaded` · `Name Filter` · `Load Selected` 버튼 제거.
  - 지운 게 아니라 `Filter and Preview` 카테고리로 옮겼다 — 탭 패널(`categories_to_show = Assets, Rename`)에서는 숨고,
    위쪽 화면이 없는 모달 대체 창에서만 보인다. (패널 필터는 버튼을 카테고리 단위로만 거를 수 있어 카테고리를 나눴다.)
  - 설정 클래스 구성 변경 → **에디터 재시작 필요**. 구성 버전(`CLASS_LAYOUT`)을 두어 옛 클래스가 남아 있으면 Output Log 로 안내.

### Verified
- `verify_a00530_renamer.py` — UE 5.4.4 · 5.7.4 **71/71**, 에러 로그 0. 패널 모양은 에디터 확인 필요.

## v01.08 (2026-11-20)

### Added
- **공용 EUW 위젯 `jun_tools/widgets/`** — 마야 `Framework/qt` 공용 위젯의 대응.
  - `umg.py` : 위젯 조립 헬퍼(에디터 스타일 위젯 · 에디터 글꼴 · GC 에 안전한 `connect()` · 박스 배치). A00530 에서 옮김.
  - `asset_list.py` : **`AssetList`** — 마야 `JUN_mod_tsl_qt_v01`(TSL) 대응. 제목 + 개수 + 행 목록 +
    `Load Selected` / `Add` / `Del` / `Up` / `Down` / `Sort` (+ `Reverse` / `Clear`). 문서 `Docs/Widgets/AssetList.md`.
  - DEV_MODE 에서 툴을 열 때 `jun_tools.widgets` 도 함께 다시 읽는다.

### Changed
- `A00530_jun_renamer` v01.04 — **Default / Copy Name 모드.** 탭 맨 위 `Mode:` 콤보로 고른다 (UMG `WidgetSwitcher`).
  - Copy Name 모드: Base / Targets **리스트 두 개**(AssetList, `Sort Base` / `Sort Targets`), Prefix · Suffix · Search ·
    Replace · Case Sensitive, Base | Target | New Name | Status 미리보기, `Copy Name` 버튼(Ready 가 없으면 꺼짐).
  - 설정 패널의 접히는 **Copy Name 섹션 제거** (`DetailsView.categories_to_show = [Assets, Rename]`). 모달 대체 창에는 남아 있다.

### Verified
- `verify_a00530_renamer.py` — UE 5.4.4 · 5.7.4 **71/71**, 에러 로그 0. 모드 전환 · 리스트 버튼 전부(`obj gc` 뒤 포함) ·
  Copy Name 칸 → 미리보기 → 실행 → 리스트에 새 이름. 화면 배치는 에디터 확인 필요.

## v01.07 (2026-11-20)

### Fixed
- `A00530_jun_renamer` v01.03 — **탭 위쪽 `Load Selected` 가 동작하지 않던 문제.** `add_callable` 의 중계 오브젝트는
  파이썬이 참조를 쥔 위젯의 델리게이트를 통해서만 GC 에서 지켜지는데(`FPyReferenceCollector`), 버튼을 지역 변수로 버려
  에디터 주기 GC 뒤 연결이 끊겼다. 콜백을 단 위젯을 전부 세션 동안 붙잡는다. 목록 행 · 설정 패널(실시간 미리보기)도 같은 처리.
- **글자가 아주 컸던 문제.** 게임용 기본 스타일(글꼴 24) 위젯 → 에디터 스타일 위젯(`EditorUtilityButton` ·
  `EditorUtilityEditableTextBox` · `EditorUtilityComboBoxString` · `EditorUtilityScrollBox`) + 에디터 기본 글꼴(9).
  필터 · 옵션 줄을 원본처럼 어두운 박스에 담고, 목록 행은 투명 버튼(호버 시 살짝 밝아짐). 스파이크 안내 문구 삭제.

### Verified
- `verify_a00530_renamer.py` — UE 5.4.4 · 5.7.4 **56/56**, 에러 로그 0. 에디터 스타일 위젯 · 글꼴 크기 9 ·
  **`obj gc` 뒤에도 Load Selected · 목록 행 · Name Filter 콜백이 살아 있음**. 화면 모양은 에디터 확인 필요.

## v01.06 (2026-11-20)

### Changed
- `A00530_jun_renamer` v01.02 — **원본 Asset Renamer 모양 UI 스파이크** (화면 확인 대기).
  - EUW 루트를 `VerticalBox`(`Root`) 로 바꾸고, 탭 안 화면을 `ui_tab.py` 가 **실행 중에 파이썬으로 조립**한다
    (`unreal.new_object()` + `add_child()`). 에셋과 코드의 약속은 `Root` 하나.
  - 위: 원본 모양 일부 — `Name Filter`(2 글자부터) · `n/m matched` · `Load Selected` · `Search` / `Replace` · 매칭 콤보 ·
    상태 줄 · 열 제목(Type / Current Name / -> / New Name / Status) · 원본과 같은 색의 목록. 행을 누르면 콘텐츠 브라우저에서 찾는다.
  - 아래: 기존 설정 패널(`DetailsView`, 파이썬 생성) — 스파이크 중에도 툴 전체 기능을 쓴다. 두 화면은 같은 설정 오브젝트를 공유.
  - UI 문자열 전부 영어. v01.01 의 루트 `DetailsView` 에셋도 계속 받는다.

### Verified
- `verify_a00530_renamer.py` — **UE 5.4.4 · 5.7.4 헤드리스 51/51**, 에러 로그 0. 위젯 조립 · 목록 행 수 · 상태 줄 ·
  입력칸 / 콤보 → 설정 → 목록, 설정 패널 → 입력칸 역방향. **화면에 실제로 그려지는지는 에디터 확인 필요.**

## v01.05 (2026-11-20)

### Changed
- `A00530_jun_renamer` v01.01 — **모달 창 → 도킹 탭.** 창을 띄운 채 콘텐츠 브라우저를 클릭할 수 있다.
  - Editor Utility Widget `Content/A00530_jun_renamer/EUW_JUNRenamer`(루트 = `DetailsView` 하나, UE 5.4 로 저장)를
    `EditorUtilitySubsystem.spawn_and_register_tab()` 으로 띄우고, 기존 설정 오브젝트를 `DetailsView.set_object()` 로 꽂는다.
    화면 구성 · 버튼 · 로직은 그대로다.
  - **미리보기 자동 갱신** — `DetailsView.on_property_changed` 로 칸 편집이 끝나면 다시 계산한다.
  - 메뉴를 다시 누르면 열린 탭을 앞으로 가져온다. 탭을 닫아도 입력값 · 목록은 남는다.
  - EUW 를 못 찾거나 탭을 못 띄우면 v01.00 의 모달 창으로 대신 연다.
  - 클래스 · 설정 오브젝트를 jun_tools 밖의 세션 모듈(`_jun_tools_session`)에 둔다 — `Reload JUN Tools` 뒤에도
    탭이 붙잡은 오브젝트가 재인스턴싱되지 않는다(엔진 ensure 방지).
  - 모달 시절 우회책 정리 — 열 때 선택 자동 불러오기는 **목록이 비어 있을 때만**, "창을 닫고 다시 열라" 안내 삭제.

### Added
- `Content/` 에셋 규칙 — 툴 전용은 `Content/A00NNN_<name>/`, 공용은 `Content/Shared/`, **UE 5.4 에서 저장**.
- `Docs/Plans/A00530_JUNRenamer_EUW_Tab_Plan.md` — 작업 계획서.

### Verified
- `Docs/verify/verify_a00530_renamer.py` — **UE 5.4.4 · 5.7.4 헤드리스 43/43**. EUW 구조 · 탭 제목, `set_object`,
  칸 편집 이벤트 → 미리보기, 모달 대체, DEV_MODE · `Reload JUN Tools` 뒤 클래스 · 오브젝트 유지. 에러 로그 0.
  탭이 실제로 뜨는지 · 콘텐츠 브라우저를 누를 수 있는지는 헤드리스로 볼 수 없다(커맨드렛은 탭을 등록하지 않는다)
  — 에디터에서 확인 필요(계획서 §6.2).

## v01.04 (2026-11-20)

### Added
- `A00530_jun_renamer` — **JUN Renamer** (`Tools > JUN > Asset > JUN Renamer...`). 에셋 일괄 이름 변경.
  - MANUProject `Tools > Asset Renamer`(MANUEditor C++ Slate 위젯)를 파이썬 디테일 뷰 다이얼로그로 이식 —
    불러오기(선택 · 선택 폴더 · /Game 전체) · 경로/이름 필터 · Search/Replace(Anywhere / Prefix / Suffix) ·
    Prefix · Suffix · 네이밍 규칙(CSV) · 텍스트 정리 · 미리보기 · 실행.
  - **Trim Front / Trim Rear** + `-1 Front` / `-1 Rear` 버튼 — 마야 A00330 Quick Rename 의 앞/뒤 한 글자 지우기.
    누를 때마다 횟수가 쌓이고 미리보기가 갱신되며, `Rename` 한 번으로 실행한다.
  - **Copy Name** — 마야 A00330 Copy Name 이식. `Targets[i] ← Prefix + (Search/Replace 한) Base[i] + Suffix`.
  - 미리보기 상태: `Ready` / `No change` / `Name taken` / `empty name` / `invalid character` — 쓸 수 없는 행은 건너뛴다.
  - 저장은 **바꾼 에셋만**. 원본은 에디터의 더티 패키지를 전부 저장했다.
  - 네이밍 규칙은 로드 없이 **에셋 레지스트리의 클래스 · 조상 클래스**로 판정. 기본값은 꺼짐 —
    원본 CSV 의 버릇(텍스처 `_DIF`, WBP → `BP_`)을 그대로 옮겼기 때문 (툴 문서 §6).
- `Config/jun_asset_rename_rules.csv` — 원본 `MANUEditor/config/AssetRenameRules.csv` 사본.

### Verified
- `Docs/verify/verify_a00530_renamer.py` — UE 5.7 헤드리스 **31/31 통과**. 스크래치 프로젝트에서 머티리얼 ·
  머티리얼 인스턴스를 만들어 실제로 이름을 바꾸고 디스크까지 확인. 참조된 에셋 리네임 후 참조 쪽이 새 이름을
  가리키고 더티 패키지 0 개. DEV_MODE 리로드 후에도 상태 유지 · 클래스 재등록 없음.
  창 모양과 버튼 배치는 헤드리스로 볼 수 없다 — 에디터에서 눈으로 확인 필요.

## v01.03 (2026-09-01)

### Changed
- `A00510_bone_viewport` — **`Apply` 버튼으로 창을 닫지 않고 적용**한다 (툴 v01.00 → v01.01).
  - 전에는 OK 를 눌러 창이 닫혀야만 설정이 적용됐다. 값을 조금씩 바꿔 가며 뷰포트를 보려면
    매번 메뉴를 다시 눌러야 했다.
  - 이제 팝업 안에 `Apply` / `Reset` 버튼이 있다. `Apply` 는 지금 값을 적용하고 **창은 그대로**,
    `Reset` 은 창을 열었을 때의 값으로 되돌려 적용한다.
  - OK 는 아직 적용 안 된 값이 남아 있을 때만 적용하고 닫는다. Cancel 은 그냥 닫으며,
    이미 `Apply` 한 것은 되돌리지 않는다(그건 `Reset` 의 몫).
  - 구현: 인자 없는 UFUNCTION 에 `CallInEditor` 메타를 달면 디테일 뷰가 버튼으로 그려 준다.
    파이썬만으로는 모덜리스 창을 못 만들기 때문에 **창이 아니라 창 안**을 고친 것이다.
  - `core` 에 `CHANGE_BONE_DRAW_MODE` / `CHANGE_SHOW_BONE_COLORS` 상수 추가 — 변경 항목 이름을
    UI 와 core 양쪽에 흩어 두지 않는다.

### Verified
- `Docs/verify/verify_a00510_apply.py` — UE 5.7 헤드리스 **16/16 통과**.
  UFunction 등록 · 인자 없음 · Apply 멱등 · Reset 복원 · show() 뒷정리 · 리로드 3회.
  버튼이 그려지는지는 헤드리스로 볼 수 없어(`-unattended` 는 창을 안 만든다) 엔진 조건
  (`GetBoolMetaData("CallInEditor") && ParmsSize == 0`, `FObjectDetails` 가 "Object" 에 등록)을
  소스에서 확인하고 그 조건을 검사했다. 실제 버튼은 에디터에서 눈으로 확인이 필요하다.

## v01.02 (2026-08-24)

### Added
- `A00520_cinematic_sequence_builder` — MSEQ / CSEQ / SSEQ 시퀀서 3계층 일괄 생성.
  - `Cinematic Sequence Builder...` : 씬 하나의 폴더 + 마스터 + 컷 + 역할별 서브시퀀스 7종을
    한 번에 만들고 SubTrack / CinematicShotTrack 으로 결선. 컷은 마스터 타임라인에 **누적
    오프셋으로 순차 배치**된다.
  - `Validate Cinematic Structure` : 기존 씬을 SOP 와 대조해 리포트만 낸다. 쓰기 없음.
  - CAM 서브시퀀스에 CineCamera 초기 셋업(스포너블 카메라 + 카메라 컷 + Transform ×2 +
    FocalLength / Aperture / ManualFocusDistance) 자동 생성. 실측 에셋과 프로퍼티 경로까지 일치.
  - **비파괴 · 멱등** — 생성 전 전수 존재 확인, 이미 있으면 결선만 보수. 두 번 돌려도 안전.
  - **Dry Run 우선** — 만들어질 이름 전체를 Output Log 에 찍고 확인을 받은 뒤 생성.
  - 우리가 만들었거나 결선한 에셋만 저장한다. 경로 아래를 통째로 저장하지 않는다.
- `Config/jun_cinematic_sop.json` — 이름 템플릿 · SSEQ 7종 · SOP 컬러코드 · 카메라 트랙 ·
  프레임레이트. **코드에 이름 규칙이 한 글자도 없다.** `<Project>/Config/` 에 두면 덮어쓴다.
- `compat.py` — 엔진 버전별 Python 바인딩 차이를 후보 목록으로 흡수. 5.8 로 올라가 API 가
  갈리면 고칠 곳이 이 파일 하나다.
- `Docs/verify/verify_sequencer_api.py` — 헤드리스 검증 스크립트.
- `.uplugin` 의존 플러그인에 `SequencerScripting` 추가 (`MovieSceneSequenceExtensions` 등이 여기 있다).
- `registry.SECTION_ORDER` 에 `Cinematic` 섹션.

### Naming decision
마스터 이름에 `MANU_` 를 **코드에도 설정 기본값에도 넣지 않았다.** 접두 부분은 UI 의
`Name Stem` 텍스트 필드에 사용자가 직접 친다 (`PreDebut_TSR_CT01` / `MANU_PreDebut_TSR_CT01`).
툴은 이 문자열을 해석하지 않고 템플릿에 그대로 끼운다.
근거: 실제 `Teaser/CT01` 에서 씬마다 `MANU_` 유무가 갈렸고, `S02` 는 폴더가 S02 인데 에셋 이름이
전부 `_S01_` 이었다. "정답 이름"을 툴이 정하는 대신 **한 번 정한 stem 을 씬 전체에 일관 적용**하는
쪽으로 풀었다. 마지막 입력값은 `Saved/JUNTools/a00520_last.json` 에 기억한다.

### Known limitation
**아직 헤드리스 실측을 돌리지 않았다.** 미확인 3건 — `MovieSceneCinematicShotTrack`,
시퀀서 폴더 컬러, 트랙 틴트. 셋 다 없으면 각각 SubTrack 폴백 / 컬러 생략으로 계속 진행하고
경고를 남기게 해 두었지만, ShotTrack 폴백은 마스터 구조가 실측과 달라지므로 확인이 필요하다.
에셋 생성은 `ScopedEditorTransaction` 안에 있어도 Ctrl+Z 로 되돌아가지 않을 수 있다.
컷별 길이 지정(균등 길이만 지원) · ML/SL 레벨 생성 · 기존 이름 자동 리네임은 범위 밖.
콘텐츠 타입 약어(`Teaser`→`TSR`) 정본은 확인 중이라 `content_types` 를 비워 두었다.

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

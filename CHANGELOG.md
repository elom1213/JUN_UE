# CHANGELOG — JUNTools

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

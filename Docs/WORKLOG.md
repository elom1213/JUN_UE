---
title: 작업 일지 (WORKLOG) — Unreal
aliases: [WORKLOG, 작업일지, devlog, UE 작업일지]
tags: [worklog, unreal, unreal-python]
updated: 2026-11-20
---

# 작업 일지 (WORKLOG) — Unreal

git 커밋 기록을 근거로 하루 작업을 요약한다. 최신 날짜가 위.
마야 쪽 일지는 `Maya_Python/JUN_All/docs/WORKLOG.md` 에 따로 있다.

> [!info] 보기
> Obsidian 에서 `JUN_UE/Docs` 를 vault(또는 폴더)로 열면 속성/태그/링크가 동작한다.
> 굵게/링크가 별표째 보이면 소스 모드이므로 `Ctrl+E` 로 읽기/라이브 프리뷰 전환.

---

## 2026-11-20 (오늘)

> [!summary] `A00530_jun_renamer` **JUN Renamer — 사내 Asset Renamer 이식 + 마야 NamingTool 기능 추가** (플러그인 v01.03→01.04, 툴 v01.00)
- 요청: MANUProject `Tools > Asset Renamer` 를 **JUN_Renamer** 로 옮기고, 마야 `A00330_NamingTool` 의
  **Quick Rename 앞/뒤 한 글자 지우기**와 **Copy Name(Base → Targets, Prefix · Set suffix · Search · Replace)** 를 더한다.
- 원본은 `MANUEditor` 의 **C++ Slate 탭**(`SMANUAssetRenamerWidget`, 1149 줄)이다. JUN_UE 는 C++ 모듈이 없으니
  A00510 · A00520 과 같은 **디테일 뷰 다이얼로그 + `CallInEditor` 버튼**으로 다시 짰다. 로직은 셋으로 갈랐다 —
  `naming.py`(문자열 규칙, unreal 비의존) · `convention.py`(CSV 규칙, unreal 비의존) · `core.py`(에셋 수집 · 판정 · 실행).
  앞 둘은 일반 파이썬으로 바로 테스트된다.
- **모달 창이라 콘텐츠 브라우저를 못 누른다** — 그래서 ① 창을 열 때 선택을 바로 불러오고 ② 입력값 · 목록을
  창 밖(`jun_tools.tools` 모듈)에 남겨 "Base 고르고 열기 → 닫기 → Targets 고르고 열기" 가 되게 했다.
  Base / Targets 는 에셋 선택 칸 배열이라 창 안에서도 고르고 끌어서 순서를 바꾼다.
- **`-1 Front` / `-1 Rear` 는 즉시 리네임이 아니라 횟수 누적 + 미리보기**로 바꿨다. 에셋 리네임은 디스크 저장 ·
  참조 수정이 따라오는 무거운 작업이라 글자마다 저장을 반복하지 않는다. 실행 뒤 횟수는 0 으로 돌린다.
- **`Set suffix` → `Suffix`** — 마야에서 세트만 받던 이유(DG 노드 이름 충돌)가 언리얼엔 없다. 같은 이름을 못 쓰는
  경우는 "같은 폴더" 이고 그건 미리보기의 `Name taken` 이 잡는다.
- **엔진 소스로 확인한 것**: CallInEditor 실행 뒤 디테일 뷰를 강제로 새로 그리지 않지만,
  `FPropertyNode::EnsureDataIsValid()` 가 틱마다 배열 크기 변화를 보고 다시 그린다 → 미리보기 배열을 버튼에서 갱신해도 된다.
  `FixupReferencers` 는 UFUNCTION 이 아니라 파이썬에서 못 부른다.
- **헤드리스로 확인한 것**: 참조된 머티리얼 이름을 바꾸면 엔진이 인스턴스를 고쳐 저장한다(더티 0, 리디렉터 없음).
  원본의 `SaveDirtyPackages`(전부 저장)는 필요 없어서 **바꾼 에셋만 저장**하도록 좁혔다.
- **함정 하나 발견** — DEV_MODE 리로드마다 uclass 를 다시 등록하면, GC 안 된 이전 인스턴스를 엔진이 재인스턴싱하며
  PythonScriptPlugin ensure(`PySelf->ob_type == PyType`)가 뜬다. 클래스는 세션당 한 번만 등록하고 버튼은
  `importlib` 로 최신 모듈 함수를 부르게 했다.
- 원본 CSV 규칙의 버릇(텍스처가 전부 `_DIF`, WBP 가 `BP_`)은 **그대로 옮기고 기본값을 껐다** — 고치는 건 CSV 의 몫.
- 검증: `verify_a00530_renamer.py` 헤드리스 **31/31**. 창 모양은 에디터에서 확인 필요. #A00530

---

## 2026-09-01

> [!summary] `A00510_bone_viewport` **창을 닫지 않는 Apply 버튼** (플러그인 v01.02→01.03, 툴 v01.00→01.01)
- 요청은 한 줄이었다 — *"OK 를 누르면 적용되고 창이 닫힌다. Apply 같은 걸 눌러 적용하되 창은
  안 닫히게 해 달라."* 문제는 **파이썬만으로는 모덜리스 창을 만들 수 없다**는 것이다.
  창을 만드는 수단이 `unreal.EditorDialog.show_object_details_view()` 하나뿐인데 그건 모달이고,
  내부적으로 `GEditor->EditorAddModalWindow()` 를 부른다 (엔진 소스에서 확인).
- **그래서 창이 아니라 창 안을 고쳤다.** 디테일 뷰는 인자가 없고 `CallInEditor` 메타가 붙은
  UFUNCTION 을 자동으로 버튼으로 그려 준다. 프로퍼티 두 개 옆에 `Apply` / `Reset` 버튼이 생기고,
  이 버튼은 창을 닫지 않으므로 창을 띄워 둔 채 몇 번이고 누를 수 있다.
- **추측 대신 엔진 소스로 조건을 확정했다** (UE 5.7).
  `PropertyCustomizationHelpers::CanCallFunctionBasedOnParams()` 가
  `GetBoolMetaData("CallInEditor") && ParmsSize == 0` 딱 두 가지만 본다.
  `DetailCustomizations` 가 `RegisterCustomClassLayout("Object", FObjectDetails::MakeInstance)`
  로 등록돼 있어 **모든 디테일 뷰**가 이 버튼을 얻는다 — 우리 팝업도 포함이다.
  파이썬 쪽 메타 전달은 `FPyUFunctionDef::ApplyMetaData()` → `UFunction::SetMetaData()` 라
  C++ 로 쓴 것과 차이가 없다.
- **버튼 네 개의 역할을 갈랐다.** `Apply` = 지금 값 적용 + 창 유지(주 경로),
  `Reset` = 창을 열었을 때의 값으로 복귀, `OK` = 아직 적용 안 된 값이 있으면 적용하고 닫기,
  `Cancel` = 그냥 닫기(이미 Apply 한 것은 안 되돌린다 — 그건 Reset 의 몫).
  "적용됐는지"의 정본은 UI 상태가 아니라 **`UPersonaOptions` 의 실제 값**이다. 그래서 `_pending()`
  이 매번 실물을 읽어 비교한다. 창이 오래 떠 있어도 UI 상태가 실물과 어긋날 일이 없다.
- **헤드리스 16/16 통과** (`Docs/verify/verify_a00510_apply.py`, UE 5.7 + 스크래치 프로젝트,
  `UE_ADDITIONAL_PLUGIN_PATHS` 로 마운트). UFunction 등록 · 인자 없음 · Apply 멱등 ·
  Reset 복원 · `show()` 뒷정리 · DEV_MODE 리로드 3회.
- **헤드리스로 확인 못 하는 것도 적어 뒀다.** `-unattended` 면 `ShowObjectsDetailsView()` 가 창을
  아예 안 만들고 false 를 돌려주므로 **버튼이 그려지는 것 자체는 눈으로 봐야 한다.**
  대신 엔진이 버튼을 그리는 조건을 소스에서 읽어 그 조건을 검사하는 쪽으로 대체했다.
- 검증 도중 실패한 probe 하나가 유용했다 — `@unreal.uclass()` 를 거치면 파이썬 함수가
  **네이티브 메서드로 치환**돼 `inspect.signature` 가 안 통한다
  (`no signature found for builtin`). 뒤집어 보면 UFunction 등록이 제대로 됐다는 증거다.
  arity 는 인자를 하나 넣어 `TypeError` 가 나는지로 확인했다. #A00510

---

## 2026-08-24

> [!summary] `A00520_cinematic_sequence_builder` **시네마틱 시퀀서 구조 생성** (v01.01→01.02)
- **먼저 조사부터 했다.** 사내 워크스페이스(`docs/`, `MANUProject/Docs/`, `MANUEditor` 플러그인
  소스 65개, Content 전체 EUW/EUB)를 훑어 **마스터/서브 시퀀서를 만드는 툴이 없다**는 것을 확인했다.
  `LevelSequenceFactoryNew|MovieSceneSubSection|MovieSceneCinematicShotTrack` grep 히트 0건.
  규격 문서는 있다 — `docs/DnableSOP/007 Cinematic/001 Key Base.md` 가 사실상 스펙이다.
- **구조는 문서가 아니라 `.uasset` 바이너리에서 직접 읽어 확정했다.** MSEQ 는
  `CinematicShotTrack`(CSEQ 13개) + `SubTrack`(씬 SSEQ 7개), CSEQ 는 `SubTrack`(컷 SSEQ 7개)
  + `CameraCutTrack` + `MovieSceneFolder`/`FolderColor`. SSEQ 는 3.2KB 짜리 **빈 시퀀스**.
  문서와 실제 에셋이 일치했다.
- **프로토타입(`seq_batch_tool_ue57.py`, 386줄)을 API 검증 자산으로 흡수했다.** 그 파일의 가치는
  기능이 아니라 **5.7 바인딩을 실제로 통과한 호출 조합**에 있다. 특히 `_call_first_working` —
  `add_master_track` 이 버전에 따라 없다는 걸 이미 겪고 처리해 둔 폴백 패턴을 `compat.py` 로
  분리했다. 엔진이 올라가면 고칠 곳이 이 파일 하나다.
- **CAM 셋업을 목표로 승격했다.** 프로토타입이 만드는 카메라 구조를 실측
  `SSEQ_..._C0010_CAM.uasset` 과 대조하니 스포너블 CineCameraActor · CameraCut ·
  Transform ×2 · Float ×3(`CurrentAperture`/`CurrentFocalLength`/`FocusSettings:ManualFocusDistance`)
  까지 **프로퍼티 경로가 전부 일치**했다. 아티스트가 손으로 하던 초기 셋업 그대로라 툴이 해도 된다.
- **프로토타입의 결함 11개를 정리하고 고쳤다.** 존재 확인 없음(재실행 시 `_1`,`_2` 누적) /
  트랜잭션 없음 / dry-run 없음 / 진행률 없음 / `save_directory(recursive)` 로 남의 더티 에셋까지
  저장 / 모든 섹션이 `set_range(0, n)` 이라 마스터에서 컷이 전부 겹침 / 마스터에 샷을 안 넣음
  (그 줄이 주석 처리돼 있었다) / `replace()` 로 이름 역파싱.
- **네이밍은 `MANU_` 를 코드에서 뺐다.** 접두 부분은 UI 의 `Name Stem` 자유 입력이다.
  근거는 실제 사고 — 같은 CT 안에서 `MANU_` 유무가 갈리고, `S02` 폴더의 마스터·SSEQ 7개가
  전부 `_S01_` 로 잘못 들어가 있다. "정답 이름"을 툴이 정하는 대신 **한 번 정한 stem 을 씬 전체
  100여 개 에셋에 일관 적용**하는 쪽으로 풀었다. 씬 안에서 이름이 갈리는 사고가 구조적으로 불가능해진다.
- `Validate` 모드는 그래서 정답 stem 을 강요하지 않는다. **씬 안에서 stem 이 하나로 통일됐는지**만
  본다 — 그것만으로 위 `S02` 사고가 잡힌다.
- 이름 규칙은 코드에 한 글자도 없다. 전부 `Config/jun_cinematic_sop.json`.
  SOP 문서가 시네마틱 Prefix 를 *"추후 확정 예정"* 으로 못박고 있어서다.
- **아직 헤드리스 실측을 돌리지 않았다.** 미확인 3건(`CinematicShotTrack`, 폴더 컬러, 트랙 틴트)은
  `Docs/verify/verify_sequencer_api.py` 로 확인해야 한다. 셋 다 없을 때의 폴백은 코드에 넣어 뒀다.
- 계획서: `Docs/Plans/A00520_CinematicSequenceBuilder_Plan.md` (rev.2) #A00520

---

## 2026-08-14

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

# CLAUDE.md — JUN_UE

언리얼 에디터용 **파이썬 콘텐츠 플러그인**. C++ 모듈이 없어 컴파일 없이 UE 5.7+ 어느 프로젝트에나 배치된다.

- **원격**: `origin` = `https://github.com/elom1213/JUN_UE.git` · 브랜치 **`main`**
  → 마야 저장소의 푸시 대상(`Dnable_repo/dev`)과 **다르다.** 헷갈리지 말 것.
- **푸시**: 그 턴에 요청이 있을 때만 (전역 규칙 2장)

> **언리얼 에디터 툴은 `Maya_Python/JUN_All` 이 아니라 여기서 작업한다.**
> 언리얼 플러그인은 배치 경로가 고정이고(`<Project>/Plugins/<Name>/`), 엔진 버전이라는 축이 하나 더 붙으며,
> 이식이 submodule/junction 단위라 마야 파이썬 트리에 섞을 수 없다.

---

## 1. 구조

**저장소 루트 자체가 플러그인 폴더**다.

```
JUN_UE/                                  = <Project>/Plugins/JUNTools/
├── JUNTools.uplugin                     플러그인 식별자. 에셋 마운트 경로 /JUNTools/ — 변경 금지
├── Content/
│   ├── A00NNN_<name>/                   툴 전용 에셋 (EUW 등). 폴더 이름 = 파이썬 툴 폴더 이름
│   ├── Shared/                          여러 툴이 함께 쓰는 에셋
│   └── Python/
│       ├── init_unreal.py               플러그인 활성화 시 자동 실행
│       └── jun_tools/
│           ├── registry.py              툴 한 줄 등록
│           ├── widgets/                 공용 EUW 위젯 (umg.py 헬퍼 · asset_list.py = 마야 TSL 대응)
│           └── tools/A00NNN_<name>/
│               ├── core.py              로직
│               └── ui.py                UI (디테일 패널 · EUW 탭)
└── Docs/
    ├── 00_UE_Tool_Plugin_Guide.md       ★ 설계 근거 · 함정. 작업 전 열어볼 것
    ├── 01_Junction_Guide.md
    ├── WORKLOG.md
    └── Tools/A00NNN_<Name>.md           툴별 가이드
```

새 툴은 `tools/A00NNN_<name>/` 에 `core.py` + `ui.py` 를 만들고 `registry.py` 에 한 줄 등록한다.

**에셋(.uasset) 규칙** — 툴 전용 에셋은 `Content/A00NNN_<name>/`(파이썬 툴 폴더와 같은 이름), 공용은 `Content/Shared/`.
지원 하한이 **UE 5.4** 라서 에셋은 **5.4 에디터에서 만들고 저장**한다(5.5+ 에서 저장하면 5.4 에서 못 연다).
모달이 아닌 창이 필요하면 EUW 루트에 변수로 노출한 `VerticalBox`(`Root`) 하나만 두고, 화면은 파이썬이 실행 중에
`unreal.new_object(<위젯>)` + `add_child()` 로 조립한다 (A00530 `ui_tab.py` 참고). 설정 패널이 필요하면
`DetailsView` 도 같은 방식으로 만들어 `set_object()`.
**조립은 공용 헬퍼 `jun_tools/widgets/umg.py` 로, 에셋 리스트는 공용 `AssetList`(`widgets/asset_list.py`, 마야 TSL 대응)로.**
여러 툴이 쓸 만한 위젯은 툴 폴더가 아니라 `widgets/` 에 두고 `Docs/Widgets/<이름>.md` 에 사용법을 쓴다.
- **`add_callable` 콜백은 파이썬이 그 위젯을 쥐고 있어야 GC 뒤에도 산다** (`FPyReferenceCollector` 는 파이썬이 참조하는
  오브젝트의 델리게이트만 따라간다). 지역 변수로 만들고 버린 버튼은 에디터 주기 GC 뒤 소리 없이 죽는다 → 리스트에 보관.
  헤드리스로 확인할 땐 `collect_garbage()`(다음 틱 예약) 말고 `execute_console_command(None, "obj gc")`.
- 파이썬으로 만드는 위젯은 **`EditorUtility*` 판**(Button · EditableTextBox · ComboBoxString · CheckBox · ScrollBox ...)을 쓴다.
  일반 `unreal.Button` 등은 게임 스타일(글꼴 24)이다. TextBlock 은 에디터 판이 없어 글꼴을 직접 입힌다(A00530 `editor_font()`).
- 위젯 델리게이트(`on_clicked.add_callable` 등)는 **기본값 인자까지 인자 수로 센다** — `lambda p=x: ...` 는
  `Callable has the incorrect number of arguments` 로 거부된다. 값을 묶을 땐 클로저 팩토리를 쓴다.

## 2. 검증 — 헤드리스 커맨드렛

**추측하지 말고 실제로 돌려 확인한다.**

```
UnrealEditor-Cmd.exe <Project>.uproject -run=pythonscript -script="<verify.py>" \
    -unattended -nosplash -nullrhi -AbsLog="<log>"
```

- 빈 `.uproject`(Modules 없음) + `Content/` + `Plugins/` 만 있으면 스크래치 프로젝트로 충분하다
  → **사내 프로젝트를 건드리지 않고** 검증할 수 있다.
- 결과는 로그의 `LogPython` 카테고리에서 grep.

### 실측으로 확인된 동작 (2026-08-14, UE 5.7.4)

- 활성화된 플러그인의 `Content/Python` 이 `sys.path` 에 올라가고 그 안의 `init_unreal.py` 가 자동 실행된다.
- `.uplugin` 에 `"EnabledByDefault": true` 를 넣으면 **`.uproject` 에 등록하지 않아도** 자동 마운트된다.
- `unreal.ToolMenus.get()` 은 커맨드렛에서도 살아 있어 **메뉴 등록 코드까지** 검증된다.
- `unreal.EditorDialog` = `UEditorDialogLibrary` (**EditorScriptingUtilities 플러그인** 필요).
  `-unattended` 면 다이얼로그가 **4번째 인자(기본값)를 즉시 반환**해서 헤드리스가 멈추지 않는다.
- **`UE_ADDITIONAL_PLUGIN_PATHS`** 환경변수(구분자 `;`, 에디터 전용)에 플러그인 **상위 폴더**를 넣으면
  프로젝트 `Plugins/` 가 비어 있어도 로드된다 → `Mounting External plugin`.
  프로젝트 파일을 안 건드리므로 **툴 배포는 복사 말고 이 방식.** 시작 시 1회만 읽으므로 재시작 필요.

## 3. 함정

- **`sys.path` 충돌** — 모든 플러그인의 `Content/Python` 이 **같은 `sys.path`** 에 올라간다.
  최상위 패키지에 `tools` / `app` / `utils` 같은 일반 명사를 두지 말 것. (그래서 `jun_tools`)
- **파이썬 클래스가 없는 UObject** — `unreal.find_object(None, "/Script/<Module>.Default__<Class>")` 로
  CDO 를 잡는다. 단 그때는 프로퍼티 이름이 snake_case 가 아니라 **C++ 원본 이름**이고 `save_config` 가 없다
  (= 세션 한정).
- **리플렉션이 없는 멤버는 파이썬에서 아예 못 건드린다.** 예: `FAnimationViewportClient::BoneDrawSize` 는
  `UPROPERTY` 도 `UFUNCTION` 도 아닌 평범한 C++ 멤버라 접근 방법이 없다. C++ 에디터 모듈이어야 가능.
- **C++ 없이 입력 위젯** — `@unreal.uenum()` + `unreal.uvalue()` → 드롭다운,
  `unreal.uproperty(bool)` → 체크박스로 놓고 `unreal.EditorDialog.show_object_details_view()` 로 띄운다.
  모달이고 **디테일 뷰라 실시간 반영은 불가** → OK 에 일괄 적용. 오브젝트는 GC 되지 않게 참조를 붙잡을 것.
- **uclass 재등록 ensure** — DEV_MODE 리로드마다 `@unreal.uclass()` 를 다시 만들면 살아 있는 이전 인스턴스가
  재인스턴싱되며 `PySelf->ob_type == PyType` ensure 가 뜬다. 타입 · 오브젝트는 jun_tools **밖**의 세션 모듈
  (`sys.modules["_jun_tools_session"]`)에 두어 세션당 1회만 등록하고, 메서드 · 이벤트는 최신 모듈로 디스패치한다
  (A00530 `ui._session()` / `_ui()` 참고). `Reload JUN Tools` 도 견딘다.

## 4. 작성 규칙

- **툴 UI 문자열은 영어** — 버튼 · 로그 · 다이얼로그 · 윈도우 타이틀. 한국어는 주석과 독스트링에만.
  (전역 규칙 6장)
- 툴을 추가/수정하면 `Docs/Tools/A00NNN_<Name>.md` 가이드와 `Docs/WORKLOG.md`, `CHANGELOG.md` 를 함께 갱신한다.

## 5. 동기화

메모리는 `.claude/memory/` 가 원본이고 `~/.claude/projects/<슬러그>/memory` 가 정크션으로 연결돼 있다.
**메모리를 고쳤으면 커밋해야 다른 PC 로 전달된다.** 셋업은 `JUN_Claude/setup.ps1`.

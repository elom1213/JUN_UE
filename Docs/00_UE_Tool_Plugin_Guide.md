# 언리얼 툴 플러그인 설계 가이드

> 이 저장소(`JUN_UE`)를 시작하면서 정리한 판단 근거와 규칙.
> 마야 툴 모음(`Maya_Python/JUN_All`)과 같은 발상을 언리얼로 옮길 때 무엇이 같고 무엇이 다른지가 핵심이다.

- **작성일**: 2026-08-14
- **대상 엔진**: UE 5.7 이상
- **검증 환경**: `MANU_Engine_Prebuilt` (5.7.4, Installed Build, `manu-main` 브랜치 사내 빌드)

---

## 1. 결론 요약

| 질문 | 결론 |
|------|------|
| 플러그인으로 툴을 묶어 프로젝트마다 이식하는 발상 | **맞다.** 언리얼의 정석이고 사내 `MANUEditor` 플러그인도 같은 구조다 |
| 어떻게 시작할 것인가 | **C++ 아닌 Python 콘텐츠 플러그인으로.** 컴파일 없이 어디에나 드롭 가능 |
| 플러그인 개수 | **1개 + 내부 툴 레지스트리.** 툴 하나당 플러그인 하나로 가지 않는다 |
| 저장소 | **마야 저장소와 분리한 새 저장소.** 저장소 루트 = 플러그인 루트 |

---

## 2. 왜 플러그인인가 — 마야와의 대응

발상 자체는 마야에서 하던 것과 1:1로 대응된다.

| 마야 (`JUN_All`) | 언리얼 (`JUN_UE`) |
|------------------|-------------------|
| `__dragDrop_A000XX.py` 드롭 → 셸프 버튼 설치 | 플러그인 폴더 배치 → `init_unreal.py` 자동 실행 |
| 셸프 버튼 → `tools.A000XX.run(True)` | 메뉴 항목 → `jun_tools.run("A00NNN_xxx")` |
| `Framework/` 공용 인프라 | `jun_tools/` 공용 패키지 (menu / registry / config) |
| `app/core` vs `app/ui` 분리 | `tools/A00NNN_xxx/core.py` vs `ui.py` |
| `config.DEV_MODE` + `reloader_v02` | `config.DEV_MODE` + `Tools > JUN > Reload JUN Tools` |
| `undo_chunk()` | `unreal.ScopedEditorTransaction` |
| `mayapy` + `maya.standalone` 헤드리스 검증 | `UnrealEditor-Cmd.exe -run=pythonscript` |

즉 "새 발상"이 아니라 **이미 검증된 작업 방식의 이식**이다. 그래서 방향은 옳다.

---

## 3. 마야와 결정적으로 다른 5가지

### ① C++ 플러그인은 "드롭하면 끝"이 아니다 — 엔진 빌드에 묶인다

마야 툴은 `.py`라서 어느 마야에나 떨어뜨리면 돈다. **C++ Editor 모듈은 다르다.**

- 엔진 버전마다 **재컴파일** 필요
- 컴파일된 바이너리는 **그 엔진 빌드 전용**
- 블루프린트 전용 프로젝트에 소스 플러그인을 넣으면 그 프로젝트가 C++ 프로젝트가 되고 **Visual Studio가 필요**해진다

> ⚠️ 현재 회사 엔진은 사내 소스 빌드(`manu-main`)다. 여기서 빌드한 플러그인 바이너리는
> 스톡 5.7 런처 엔진 프로젝트에서 **모듈 로드에 실패**할 수 있다. "여러 프로젝트에 이식"이라는
> 목표와 C++ 우선 전략은 정면으로 충돌한다.

참고로 `PoseDriverConnect_5.7`이 폴더명에 엔진 버전을 달고 있는 이유가 바로 이것이다.

### ② 그래서 Python 콘텐츠 플러그인으로 시작한다

언리얼은 **활성화된 플러그인의 `Content/Python` 폴더를 `sys.path`에 추가하고, 그 안의 `init_unreal.py`를 에디터 시작 시 자동 실행**한다. 이것만으로:

- C++ 모듈 0개 → **컴파일 불필요**, 어떤 엔진 버전/어떤 프로젝트에도 폴더 복사만으로 이식
- `unreal.ToolMenus`로 Tools 메뉴에 항목 등록 가능
- 코드 수정 → 리로드 → 즉시 반영 (**마야 개발 사이클과 거의 동일**)

C++는 Python API로 막히는 지점이 나왔을 때 **같은 플러그인에 Editor 모듈을 추가**한다. 하이브리드는 정식 지원 구성이며, 그 시점부터는 "C++ 쓰는 프로젝트에서만 전체 기능" / "그 외에는 Python 기능만"으로 갈라도 된다.

**Python으로 안 되는 것 (그때 C++로 간다)**
- 커스텀 도킹 탭 / Slate 위젯 (에디터 도크에 붙는 비모달 창)
- 애님그래프 노드, 커스텀 에셋 타입, 디테일 커스터마이제이션
- 런타임(패키징된 게임) 코드 — Python은 **에디터 전용**
- 그 외 `UFUNCTION`으로 노출되지 않은 엔진 기능 전반

> 언리얼 Python API는 `maya.cmds`보다 **훨씬 좁다**. 리깅/애님 쪽은 특히 그렇다.
> 막히면 C++로 `UFUNCTION(BlueprintCallable)` 하나만 뚫고 Python에서 부르는 패턴이 표준이다.

### ③ 플러그인 이름은 나중에 못 바꾼다

마야 컨벤션처럼 폴더명에 버전을 박는 습관(`_creator_V02`)은 여기서 위험하다.

- 플러그인 식별자 = **`.uplugin` 파일 이름** (폴더 이름이 아니다)
- 이게 곧 에셋 마운트 경로 `/JUNTools/...`가 된다 → 바꾸면 참조가 전부 깨진다
- **버전은 `.uplugin`의 `VersionName` + `CHANGELOG.md`로 관리한다**
- 폴더명에 `_5.7`을 붙이는 건 무방하다 (Epic도 그렇게 한다). `.uplugin` 이름만 고정이면 된다

이 저장소에서 확정한 이름: **`JUNTools`** (폴더는 `JUN_UE`, 파일은 `JUNTools.uplugin`)

### ④ 플러그인을 툴 개수만큼 만들지 않는다

`A000XX` 하나당 플러그인 하나로 가면 이식할 때마다 N개를 관리해야 한다.
**플러그인 1개 + 내부 툴 레지스트리**로 간다.

```
JUN_UE/                          ← 이식 단위는 이것 하나
├─ JUNTools.uplugin
└─ Content/Python/
   ├─ init_unreal.py             ← 부팅 훅 (메뉴 등록만)
   └─ jun_tools/
      ├─ registry.py             ← 툴 목록. 새 툴 추가 시 손대는 유일한 공용 파일
      ├─ menu.py                 ← Tools > JUN 메뉴를 registry 대로 그림
      ├─ config.py               ← DEV_MODE
      └─ tools/A00NNN_<name>/
         ├─ core.py              ← 로직 (UI 무의존)
         └─ ui.py                ← 다이얼로그
```

메뉴는 `Tools` 아래에 **"JUN" 하위 메뉴 하나**만 만들고 그 안에서 섹션으로 나눈다.
툴이 10개가 되면 Tools 메뉴가 난장판이 되기 때문이다.

> 메뉴 등록은 `UToolMenus` / `unreal.ToolMenus`를 쓴다. `FExtender`는 구식이다.
> 등록/해제는 **owner 이름으로 묶어서** 처리해야 리로드 시 항목이 중복되지 않는다.

### ⑤ 이식성은 "프로젝트 의존을 설정으로 빼는 것"에서 나온다

툴이 특정 프로젝트의 폴더 구조·네이밍을 하드코딩하는 순간 이식성은 끝난다.

- 경로/규칙은 `UDeveloperSettings`(C++) 또는 플러그인 config ini / json으로
- Python 단계에서는 `Config/` 아래 json을 읽는 정도로 충분하다
- 프로젝트마다 다른 값은 **코드가 아니라 데이터**로 존재해야 한다

---

## 4. 마야에서 지키던 규칙은 그대로 가져온다

- **core / ui 분리**: 로직은 UI 없이 호출 가능하게. 커맨드렛·배치에서 재사용되고 헤드리스 검증이 가능해진다
- **Undo**: 에셋/액터를 건드리는 툴은 `unreal.ScopedEditorTransaction`으로 묶는다 (마야 `undo_chunk` 대응). 안 묶으면 Ctrl+Z가 엉뚱한 걸 되돌린다
- **UI 문자열은 영어**, 한국어는 주석/문서에만
- **패키지 이름 충돌 주의**: 여러 플러그인의 `Content/Python`이 **같은 `sys.path`에 올라간다**.
  `tools`, `app`, `utils` 같은 일반 명사를 최상위 패키지로 쓰면 다른 플러그인과 충돌한다.
  → 최상위는 반드시 고유하게 (`jun_tools`). 마야 쪽에서 겪은 것과 같은 함정이다
- **추측하지 말고 확인**: `UnrealEditor-Cmd.exe <uproject> -run=pythonscript -script=<파일>` 로
  헤드리스 실행해 API 존재 여부를 확인한다 (`mayapy` 검증의 언리얼 판)

---

## 5. 저장소 판단 — 왜 `JUN_All`에 넣지 않았나

| 항목 | `JUN_All` (마야) | 언리얼 플러그인 |
|------|------------------|-----------------|
| 배치 제약 | `tools/A000XX_*` 어디든 | `<Project>/Plugins/<Name>/` **고정 레이아웃** |
| 툴체인 | 없음 (순수 py) | UBT / VS / 엔진 버전 매트릭스 |
| 산출물 | `0020_out/` 정도 | `Binaries/`, `Intermediate/`, `.uasset` 바이너리 |
| 이식 방법 | 파일 드롭 | **submodule / junction 단위** |
| 버전 축 | 툴 버전 | 툴 버전 **×** 엔진 버전 |

결정적인 이유는 **이식 단위**다. 저장소 루트 = 플러그인 루트로 두면 어떤 프로젝트에서든

```bash
git submodule add https://github.com/elom1213/JUN_UE.git Plugins/JUNTools
```

한 줄로 끝난다. `JUN_All/tools/` 밑에 있으면 이게 불가능하다.
그리고 엔진 버전별 브랜치(`5.7`, `5.8`)가 필요한데, 이 축은 마야 툴 히스토리와 **절대 섞이면 안 된다**.

**대신 문서로 연결한다**: 가이드는 이 저장소 `Docs/`에 두고, `JUN_All/docs/`에는 포인터 한 줄만 남긴다.
포트폴리오(EN/KR)는 기존대로 양쪽 동기 갱신한다.

---

## 6. 프로젝트에 붙이는 방법

**플러그인은 프로젝트의 `Plugins/` 폴더 안에 있어야만 하는 것이 아니다.**
프로젝트마다 사본을 만들면 고칠 때마다 N군데를 다시 복사해야 하고, 어느 사본이 최신인지
알 수 없게 된다. 아래 순서대로 검토한다.

### 방법 A — `UE_ADDITIONAL_PLUGIN_PATHS` 환경변수 (개인 작업, **최선**)

PC에 **한 번만** 설정하면 그 PC의 **모든 프로젝트**가 자동으로 플러그인을 인식한다.
프로젝트 파일을 하나도 건드리지 않으므로, 회사 프로젝트에 개인 툴의 흔적이 남지 않는다.

```powershell
# 1) 플러그인을 모아둘 전용 폴더를 만들고 저장소를 junction 으로 건다
New-Item -ItemType Directory -Force "C:\UE_Plugins"
cmd /c mklink /J "C:\UE_Plugins\JUNTools" "C:\Users\USER\Desktop\JP\0030_maya_python_JUN\JUN_UE"

# 2) 사용자 환경변수로 등록 (한 번만). 여러 경로는 세미콜론으로 구분
setx UE_ADDITIONAL_PLUGIN_PATHS "C:\UE_Plugins"
```

에디터를 새로 켜면 로그에 `LogPluginManager: Mounting External plugin JUNTools` 가 찍힌다.

- 엔진 소스의 설명 그대로 **"DCC 파이프라인에서 플러그인을 스테이징하는 용도"** 로 만들어진 기능이다
- **에디터 전용**(`WITH_EDITOR`)이라 패키징된 게임에는 아무 영향이 없다
- 환경변수는 **에디터 시작 시 한 번** 읽는다 → 값을 바꿨으면 에디터를 재시작한다
- 지정한 경로는 **플러그인들을 담는 상위 폴더**다. 큰 트리를 가리키면 스캔 비용이 커지므로
  전용 폴더를 따로 파는 편이 좋다
- 프로젝트별 스위치가 필요하면 커맨드라인 `-PLUGIN=<경로>` 도 같은 일을 한다

### 방법 B — junction (그 프로젝트에서만 쓰고 싶을 때)

```powershell
cmd /c mklink /J "<Project>\Plugins\JUNTools" "C:\Users\USER\Desktop\JP\0030_maya_python_JUN\JUN_UE"
```

원본이 하나이므로 사본이 갈라지지는 않지만, 프로젝트마다 걸어줘야 하고
**버전 관리 대상 폴더 안에 들어간다**는 부담이 있다.

### 방법 C — git submodule (팀과 함께 쓰는 플러그인이 됐을 때)

```bash
git submodule add https://github.com/elom1213/JUN_UE.git Plugins/JUNTools
```

### 방법 D — 복사·붙여넣기 ❌

첫 동작 확인용으로는 괜찮지만 상시 방식으로는 쓰지 않는다.
고칠 때마다 프로젝트 수만큼 다시 복사해야 하고, 사본이 원본보다 앞서거나 뒤처져도 알 수가 없다.

### ⚠️ 같은 플러그인이 두 곳에서 발견되면

`Plugins/` 안의 사본과 환경변수 경로에 **같은 이름의 플러그인이 동시에 존재하면**
엔진은 그중 하나만 채택한다. 어느 쪽이 살아 있는지 알기 어려워지므로,
방법 A로 옮길 때는 **프로젝트 안의 사본을 먼저 지운다.**

### ⚠️ MANUProject에 붙일 때

- `MANUProject`는 **SVN(전체) + Git(Source/Config/Plugins) 이중 관리**다
- `Plugins/` 아래에 개인 플러그인을 두면(사본이든 junction이든) **버전 관리에 딸려 올라갈 위험**이 있다
- 그래서 이 프로젝트에서는 **방법 A(환경변수)가 특히 유리하다** — `Plugins/`를 아예 건드리지 않는다
- 굳이 `Plugins/` 안에 둔다면 **먼저** `svn:ignore` / `.gitignore`에 등록할 것
- 사내 프로젝트에 개인 저장소를 얹는 것은 정책 확인이 필요한 사안이기도 하다

### 폴더 이름

플러그인 식별자는 **`.uplugin` 파일 이름**이므로 담는 폴더 이름은 `JUN`이든 뭐든 동작한다.
다만 나중에 헷갈리므로 폴더도 `JUNTools`로 맞춰 두는 편이 좋다.

### 활성화

`.uplugin`에 `"EnabledByDefault": true`를 넣어 두었으므로 대부분 자동으로 켜진다.
안 보이면 **Edit > Plugins**에서 `JUN Tools`를 찾아 체크하고 에디터를 재시작한다.
`PythonScriptPlugin` / `EditorScriptingUtilities`는 `.uplugin`의 의존성으로 걸어 두었으므로 함께 켜진다.

---

## 7. 엔진 버전 전략

- `main` = 현재 주력 엔진(5.7) 기준
- 엔진이 올라가서 API가 깨지면 **브랜치를 판다** (`5.7`, `5.8` …). Epic이 `PoseDriverConnect_5.7`로 하는 방식과 같다
- Python만 쓰는 동안에는 대부분 문제가 없다. C++ 모듈을 추가한 시점부터 이 전략이 필요해진다
- `.uplugin`에 `"EngineVersion"`을 **넣지 않는다** — 넣는 순간 그 버전에 고정된다

---

## 8. 개발 워크플로

1. 코드 수정
2. **Tools > JUN > Reload JUN Tools** → 에디터 재시작 없이 반영
   (`config.DEV_MODE = True`면 툴 실행 시에도 해당 툴 패키지를 매번 새로 읽는다)
3. 로그는 **Output Log**의 `LogPython` 카테고리에서 확인
4. API가 있는지 모르겠으면 헤드리스로 확인:

```bash
UnrealEditor-Cmd.exe <Project>.uproject -run=pythonscript -script="<verify.py>" -unattended -nosplash -nullrhi
```

`register()`는 owner 단위로 먼저 해제하고 다시 등록하므로 몇 번을 호출해도 메뉴가 중복되지 않는다.

---

## 9. 새 툴 추가 체크리스트

1. `Content/Python/jun_tools/tools/A00NNN_<name>/` 폴더 생성 (`__init__.py`, `core.py`, `ui.py`)
2. `core.py`에 로직 — **`unreal` 외의 UI 의존 없이**, 함수로 호출 가능하게
3. `ui.py`에 `show()` — 물어보고 core를 부르는 얇은 껍데기
4. `registry.py`의 `TOOLS`에 `ToolSpec` 한 줄 추가
5. 씬/에셋을 바꾸는 툴이면 `unreal.ScopedEditorTransaction`으로 감쌀 것
6. `Docs/Tools/A00NNN_<name>.md` 작성, `CHANGELOG.md`와 `version.py` 갱신

---

## 10. 함정 모음

| 함정 | 내용 |
|------|------|
| 플러그인 이름 변경 | `.uplugin` 이름 = 마운트 경로. 바꾸면 에셋 참조가 깨진다. **처음에 확정** |
| 최상위 패키지 이름 | 모든 플러그인의 `Content/Python`이 같은 `sys.path`에 올라간다. 일반 명사 금지 |
| C++ 모듈 추가 | 그 순간부터 엔진 빌드마다 재컴파일. 이식성이 급격히 떨어진다 |
| `Binaries/`, `Intermediate/` 커밋 | 절대 금지. `.gitignore`에 등록됨 |
| `.uasset` | `Content/`에 바이너리 에셋이 생기면 Git LFS를 검토할 것 |
| 부팅 중 예외 | `init_unreal.py`에서 예외가 나면 메뉴가 통째로 안 생긴다. 반드시 try/except로 감싸고 로그를 남긴다 |
| Python은 에디터 전용 | 패키징된 게임에서는 실행되지 않는다. 런타임 기능은 C++/BP로 |
| 모달 다이얼로그 | `unreal.EditorDialog.*`는 **모달**이다. 창을 띄운 채 뷰포트를 조작하는 툴은 Editor Utility Widget이나 Slate(C++)로 가야 한다 |

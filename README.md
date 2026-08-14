# JUN Tools — Unreal Engine Editor Tool Plugin

Unreal Engine 5.7+ 에디터 툴 모음 플러그인. **이 저장소의 루트가 곧 플러그인 폴더다.**

- **Author**: Ji Hun Park (Junny / `Dnable_JunnyPark`)
- **Plugin name**: `JUNTools` (`JUNTools.uplugin`)
- **Version**: v01.00
- **Engine**: UE 5.7 이상 / 검증 빌드 `MANU_Engine_Prebuilt` 5.7.4
- **C++ 컴파일 불필요** — Python 콘텐츠 플러그인

> 마야 툴 모음(`Maya_Python/JUN_All`)과 같은 발상을 언리얼로 옮긴 것이다.
> 설계 판단과 규칙은 **[Docs/00_UE_Tool_Plugin_Guide.md](Docs/00_UE_Tool_Plugin_Guide.md)** 참고.

---

## 설치

프로젝트의 `Plugins/` 아래에 `JUNTools`라는 이름으로 배치한다.

**junction (개인 작업, 권장)**
```powershell
cmd /c mklink /J "<Project>\Plugins\JUNTools" "C:\Users\USER\Desktop\JP\0030_maya_python_JUN\JUN_UE"
```

**git submodule (팀 공유 프로젝트)**
```bash
git submodule add https://github.com/elom1213/JUN_UE.git Plugins/JUNTools
```

에디터를 켜면 자동으로 마운트된다(`"EnabledByDefault": true`).
안 보이면 **Edit > Plugins**에서 `JUN Tools`를 체크하고 재시작한다.
의존 플러그인(`PythonScriptPlugin`, `EditorScriptingUtilities`)은 함께 켜진다.

> ⚠️ SVN/Perforce로 관리되는 프로젝트에 junction을 걸 때는 **먼저** `svn:ignore` / `.gitignore`에
> `JUNTools`를 등록할 것. 안 그러면 개인 플러그인이 통째로 커밋될 수 있다.

---

## 사용

상단 메뉴 **Tools > JUN**

| 섹션 | 항목 | 설명 |
|------|------|------|
| Test | Hello Tool | 팝업을 띄우고 OK를 누르면 Output Log에 `Hello`를 출력 ([문서](Docs/Tools/A00500_HelloTool.md)) |
| Developer | Reload JUN Tools | 에디터 재시작 없이 전체 파이썬 모듈 재로드 |

로그는 **Output Log**의 `LogPython` 카테고리에서 확인한다.

---

## 구조

```
JUN_UE/
├─ JUNTools.uplugin              # 플러그인 식별자 (이름 변경 금지)
├─ Docs/
│  ├─ 00_UE_Tool_Plugin_Guide.md # 설계 가이드 · 판단 근거 · 함정
│  └─ Tools/                     # 툴별 문서
└─ Content/Python/
   ├─ init_unreal.py             # 에디터 부팅 훅 (자동 실행)
   └─ jun_tools/
      ├─ __init__.py             # run() / reload_all()
      ├─ config.py               # DEV_MODE
      ├─ version.py
      ├─ registry.py             # 툴 목록 — 새 툴은 여기 한 줄
      ├─ menu.py                 # Tools > JUN 메뉴
      └─ tools/A00NNN_<name>/
         ├─ core.py              # 로직 (UI 무의존)
         └─ ui.py                # 다이얼로그
```

## 새 툴 추가

1. `Content/Python/jun_tools/tools/A00NNN_<name>/` 생성 (`__init__.py` / `core.py` / `ui.py`)
2. `registry.py`의 `TOOLS`에 `ToolSpec` 한 줄 추가
3. `Docs/Tools/A00NNN_<name>.md` + `CHANGELOG.md` + `version.py` 갱신

## 개발

`config.DEV_MODE = True`면 툴 실행 시마다 해당 툴 패키지를 다시 읽는다.
공용 코드(`menu.py`, `registry.py`)를 고쳤을 때는 **Tools > JUN > Reload JUN Tools**.

API 확인은 추측하지 말고 헤드리스로:
```bash
UnrealEditor-Cmd.exe <Project>.uproject -run=pythonscript -script="<verify.py>" -unattended -nosplash -nullrhi
```

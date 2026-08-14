# A00500 — Hello Tool

플러그인 배선이 제대로 연결됐는지 확인하는 **테스트 툴**이자, 새 툴을 만들 때 복제할 **최소 템플릿**.

- **버전**: v01.00 (2026-08-14)
- **메뉴**: `Tools > JUN > Test > Hello Tool`
- **모듈**: `jun_tools/tools/A00500_hello/`

---

## 동작

1. 메뉴를 누르면 모달 팝업이 뜬다 — `"Press OK to print 'Hello' to the Output Log."`
2. **OK** → Output Log(`LogPython`)에 `Hello` 출력
3. **Cancel** → `[JUNTools] Hello Tool cancelled.` 만 남기고 종료

이 한 번의 클릭으로 아래가 전부 검증된다.

| 확인되는 것 | 실패 시 증상 |
|-------------|--------------|
| 플러그인이 마운트됐다 | Plugins 목록에 `JUN Tools`가 없다 |
| `init_unreal.py`가 실행됐다 | `Tools > JUN` 메뉴 자체가 없다 |
| `ToolMenus` 등록이 됐다 | JUN 메뉴는 있는데 항목이 비어 있다 |
| Python → core 호출 경로가 살아 있다 | 팝업은 뜨는데 로그에 `Hello`가 안 찍힌다 |
| `EditorScriptingUtilities`가 켜져 있다 | `unreal.EditorDialog` AttributeError |

---

## 구조 — 새 툴의 템플릿

```
A00500_hello/
├─ __init__.py
├─ core.py    # say_hello(message="Hello") → 로그 출력 후 값 반환
└─ ui.py      # show() → 팝업을 띄우고 OK일 때만 core 호출
```

**core는 UI를 모른다.** 다이얼로그 없이 파이썬 콘솔이나 커맨드렛에서 바로 부를 수 있다.

```python
# Output Log > Cmd 창에서 (Python 모드)
import jun_tools.tools.A00500_hello.core as core
core.say_hello("Hello")
```

메뉴를 거치는 정식 경로는 이렇게 통일돼 있다.

```python
import jun_tools
jun_tools.run("A00500_hello")
```

---

## 다이얼로그에 대해

`unreal.EditorDialog.show_message()`는 `EditorScriptingUtilities` 플러그인의
`UEditorDialogLibrary`를 파이썬에서 부르는 것이다. **C++ 컴파일 없이 쓸 수 있는 모달 팝업**이다.

- 반환값은 `unreal.AppReturnType` (OK / CANCEL / YES / NO …)
- `-unattended`로 실행하면 사용자를 기다리지 않고 **네 번째 인자(기본값)를 즉시 반환**한다.
  그래서 헤드리스 검증이 멈추지 않는다 — 이 툴은 기본값을 `CANCEL`로 두었다

### 입력 필드가 필요해지면

`show_message`는 버튼만 있다. 값을 받아야 하는 툴은 같은 라이브러리의
`unreal.EditorDialog.show_object_details_view(title, obj, options)`로 확장한다.
파이썬 `unreal.Object` 서브클래스에 `uproperty`를 달면 디테일 패널 형태의 입력 창이 된다.

### 모달의 한계

`EditorDialog.*`는 전부 **모달**이다. 창을 띄워둔 채 뷰포트를 조작해야 하는 툴
(선택을 바꿔가며 값을 보는 종류)은 Editor Utility Widget 또는 Slate(C++)로 가야 한다.
자세한 건 [설계 가이드](../00_UE_Tool_Plugin_Guide.md) 3장 참고.

---

## 검증 기록

`MANU_Engine_Prebuilt` 5.7.4에서 헤드리스 실행 (2026-08-14) — 15/15 통과.

```
LogPluginManager: Mounting Project plugin JUNTools
LogPython: Running start-up script .../Plugins/JUNTools/Content/Python/init_unreal.py... took 32.043 ms
LogPython: [JUNTools] v01.00 loaded. See Tools > JUN.
LogPython: JUNVERIFY ===== 15 pass / 0 fail =====
```

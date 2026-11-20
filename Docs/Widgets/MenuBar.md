---
title: 공용 메뉴 바 (MenuBar) 사용법
aliases: [MenuBar, 메뉴 바, menu_bar, tool_menu, Copy Tool Name]
tags: [unreal-python, widget, euw, shared]
updated: 2026-11-20
---

# 공용 메뉴 바 `MenuBar`

`Content/Python/jun_tools/widgets/menu_bar.py` (화면) + `widgets/tool_menu.py` (공통 항목 · 툴 이름 · 클립보드).
마야 `JUN_mod_menuBar_qt_v01` + `Framework/core/tool_menu.py` 의 언리얼 대응이다. **같은 항목 · 같은 문자열 형식.**

- 처음 쓰는 곳: A00530 JUN Renamer (v01.08)

---

## 1. 화면

```
[Help ▾]  [Copy Tool Name] Copied to clipboard : A00530_jun_renamer    ← 오른쪽 = 마지막 결과
┌───────────────────────┐
│ Copy Tool Name        │   누르면 그 아래에 뜨고 툴 화면을 덮는다
│ Copy Tool Name + Tabs │   항목을 고르거나 제목을 다시 누르면 닫힌다
└───────────────────────┘
```

| 항목 | 클립보드에 들어가는 것 |
|------|------------------------|
| **Help > Copy Tool Name** | 툴 폴더 이름 — `A00530_jun_renamer` |
| **Help > Copy Tool Name + Tabs** | 툴 폴더 이름 + 지금 보이는 탭(모드) — `A00530_jun_renamer / Copy Name` |

결과는 Output Log 와 메뉴 바 오른쪽 글자에 남는다.

---

## 2. 쓰는 법

```python
from jun_tools.widgets import menu_bar, tool_menu, umg

body = unreal.new_object(unreal.VerticalBox)       # 툴 화면을 여기에 조립
...
bar = menu_bar.MenuBar(
    keep,                                           # 콜백 위젯을 붙잡을 리스트 (AssetList 와 같은 규칙)
    tool_menu.tool_name_from_module(__name__),      # jun_tools.tools.<툴 폴더>.xxx → 툴 폴더 이름
    tab_path=lambda: ["Copy Name"],                 # 지금 보이는 탭 · 모드 라벨 (없으면 생략)
    menus=None,                                     # 툴 전용 메뉴 [(제목, [tool_menu.MenuItemSpec])]
)
umg.add(root, bar.wrap(body), weight=1.0, padding=(0, 0, 0, 0))   # Root 에는 이 Overlay 하나
```

- **모든 툴 공통 항목 추가** — `tool_menu.py` 의 `COMMON_MENUS` 에 한 줄, 또는
  `tool_menu.register_common_item("Help", tool_menu.MenuItemSpec(label, callback(ctx), tooltip))`.
  `ctx` = `MenuContext(tool_name, log, tab_path)`.
- 툴 전용 메뉴가 공통 메뉴와 제목이 같으면 툴 항목 뒤에 공통 항목이 붙는다.
- `bar.run(title, label)` = 항목 실행 (검증 스크립트용), `bar.open(title)` / `bar.close()`.

---

## 3. 구현 메모 · 한계

- **UMG 에는 메뉴 바가 없고**, 팝업(`MenuAnchor`)은 내용으로 쓸 위젯 블루프린트 **에셋**이 필요하다(5.4 · 5.7 확인).
  그래서 `Overlay` 에 [메뉴 바 + 툴 화면] 과 드롭다운(평소 Collapsed)을 겹쳐 놓고, 제목 버튼을 누르면 드롭다운 위치를
  제목 버튼 아래로 맞춰(실행 중 지오메트리) 보이게 한다.
- **드롭다운 밖을 눌러도 닫히지 않는다** — 제목을 다시 누르거나 항목을 고르면 닫힌다.
- **클립보드** — 언리얼 파이썬 API 에는 클립보드 함수가 없다. `ctypes` 로 Windows 클립보드(`CF_UNICODETEXT`)를 직접 쓴다.
  Windows 전용 (다른 OS 에서는 `Could not access the clipboard.`). 쓰고 나서 다시 읽어 같은지 확인한다.
- 검증: `Docs/verify/verify_a00530_renamer.py` 가 클립보드 내용을 실제로 읽어 확인하고, 끝나면 원래 내용을 되돌린다.

---
title: 공용 리스트 위젯 (AssetList) 사용법
aliases: [AssetList, 공용 리스트, TSL 대응, asset_list]
tags: [unreal-python, widget, euw, shared]
updated: 2026-11-20
---

# 공용 리스트 위젯 `AssetList`

`Content/Python/jun_tools/widgets/asset_list.py` — **EUW 탭을 파이썬으로 조립하는 툴이 함께 쓰는 에셋 리스트.**
마야 `Framework/qt/MOD_tsl_qt_v01.py`(`JUN_mod_tsl_qt_v01`, 문서 `Framework_MOD_tsl_qt.md`)의 언리얼 대응이다.

- 처음 쓰는 곳: A00530 JUN Renamer 의 Copy Name 모드 (Base / Targets)
- 함께 쓰는 헬퍼: `jun_tools/widgets/umg.py` (에디터 스타일 위젯 · GC 에 안전한 콜백 · 박스 배치)

> **용어** — "TSL" 은 마야 `textScrollList` 의 줄임말이라 언리얼 용어가 아니다. UMG 의 같은 역할은 **`ListView`** 다.
> 다만 `ListView` 는 행 위젯 블루프린트(`UserObjectListEntry` 구현)가 에셋으로 하나 더 필요해서,
> 이 위젯은 에셋 없이 `ScrollBox` 에 행 버튼을 쌓는다. 그래서 이름을 **AssetList** 로 했다.

---

## 1. 화면

```
Base                         Number: 2      ← 제목(bold) + 개수
┌──────────────────────────────┐
│ SK_Hero                      │   행을 누르면 선택(파랗게) + 콘텐츠 브라우저에서 그 에셋을 찾는다
│ (None)                       │   지워진 에셋은 빨간 (None)
└──────────────────────────────┘
[ Load Selected ]                           ← show_load
[Add][Del][Up][Down][Sort]                  ← show_add / show_del / show_up / show_down / show_sort
                                               Reverse · Clear 는 기본 꺼짐
```

| 버튼 | 동작 | 마야 TSL |
|------|------|----------|
| **Load Selected** | 콘텐츠 브라우저 선택으로 리스트를 **교체** | Select Objects (언리얼에서 "Select" 는 다른 뜻이라 Load) |
| **Add** | 선택을 **중복 없이 추가** (중복 수는 Output Log 에) | Add |
| **Del / Up / Down** | 고른 행 삭제 / 한 칸 위 · 아래 | 같음 |
| **Sort / Reverse** | 이름 오름차순 / 순서 뒤집기 | 같음 |
| **Clear** | 전부 비움 | (없음) |

선택은 **한 행**이다 (마야는 다중 선택 — 버튼 클릭으로는 Ctrl 을 읽을 수 없어 단일로 시작했다).

---

## 2. 쓰는 법

```python
from jun_tools.widgets import asset_list, umg

keep = []                                   # 툴이 세션 동안 쥐고 있을 리스트 (아래 3장)
base = asset_list.AssetList(
    keep, "Base",
    items=[...],                            # 처음 항목 (UObject)
    on_changed=lambda items: ...,           # 버튼으로 항목이 바뀌면 불린다
    show_load=True, show_add=True, show_del=True, show_up=True, show_down=True,
    show_sort=True, show_reverse=False, show_clear=False,
    load_label="Load Selected", sort_label="Sort Base",
    get_selection=None,                     # 기본: 콘텐츠 브라우저 선택 에셋
    on_row_clicked=None,                    # 기본: 콘텐츠 브라우저를 그 에셋으로
    label=None, tooltip=None,               # 기본: 에셋 이름 / 경로
)
umg.add(parent_box, base.widget, weight=1.0)

base.items()                # 현재 항목 (사본)
base.set_items([...])       # 바깥에서 맞춘다 (on_changed 는 부르지 않음, notify=True 면 부름)
base.append_unique([...])   # 중복 없이 붙임 → 붙인 개수
base.selected_index         # 고른 행 (-1 = 없음)
base.buttons["sort"]        # 버튼 위젯 (load / add / del / up / down / sort / reverse / clear)
```

---

## 3. 꼭 지킬 것

- **`keep` 리스트를 툴이 계속 쥐고 있어야 한다.** 버튼 콜백(`add_callable`)의 중계 오브젝트는 파이썬이 참조를 쥔
  위젯의 델리게이트를 통해서만 GC 에서 지켜진다. 놓치면 에디터 주기 GC(약 60 초) 뒤 버튼이 소리 없이 죽는다
  (A00530 v01.03 에서 실제로 겪었다 — `umg.py` 머리말).
- 콜백은 UI 문자열과 마찬가지로 **영어 로그**만 남긴다.
- 헤드리스(커맨드렛)에서는 콘텐츠 브라우저가 없어서 기본 `on_row_clicked`(콘텐츠 브라우저 이동)가 Slate assert 를 낸다.
  검증 스크립트에서는 `on_row_clicked` 를 바꿔 끼운다.
- 코드를 고치면 DEV_MODE 에서 툴을 다시 열 때 반영된다 — `jun_tools.run()` 이 툴 패키지와 함께 `jun_tools.widgets` 도 비운다.

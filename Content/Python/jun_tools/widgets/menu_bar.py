# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-11-20
#
# 공용 - EUW 탭 맨 위 메뉴 바 (`Help ▾` ...). 마야 `JUN_mod_menuBar_qt_v01` 의 언리얼 대응.
#
# UMG 에는 메뉴 바 위젯이 없고, 팝업 메뉴(`MenuAnchor`)는 내용 위젯 블루프린트(에셋)가 있어야 한다.
# 그래서 에셋 없이 **Overlay** 로 만든다:
#
#   Overlay
#   ├ VerticalBox (frame) : [메뉴 바 줄][툴 화면(body)]
#   └ 메뉴마다 드롭다운 Border (평소 Collapsed) - 제목 버튼을 누르면 그 아래에 떠서 툴 화면을 덮는다
#
# 공통 항목은 `tool_menu.COMMON_MENUS`(Help > Copy Tool Name · Copy Tool Name + Tabs). 툴 전용 메뉴는
# `menus=[(제목, [MenuItemSpec])]` 로 더한다(같은 제목이면 툴 항목 뒤에 공통 항목).
#
# 한계: 드롭다운 밖을 눌러도 닫히지 않는다 - 제목을 다시 누르거나 항목을 고르면 닫힌다.
# UI 문자열은 영어만.

import unreal

from . import tool_menu, umg

ARROW = u" ▾"               # ▾
FALLBACK_BAR_HEIGHT = 24.0
COLOR_DROPDOWN = unreal.LinearColor(0.02, 0.02, 0.02, 1.0)


def merge_menus(menus):
    """툴 메뉴 + 공통 메뉴 → [(제목, [MenuItemSpec])]. 툴 메뉴 순서 먼저, 공통 메뉴는 뒤."""
    merged = [(title, list(items)) for title, items in (menus or [])]
    for title, items in tool_menu.common_menus():
        for existing_title, existing_items in merged:
            if existing_title == title:
                labels = set(item.label for item in existing_items)
                existing_items.extend(item for item in items if item.label not in labels)
                break
        else:
            merged.append((title, items))
    return merged


def _local_size(widget):
    try:
        return unreal.SlateBlueprintLibrary.get_local_size(widget.get_cached_geometry())
    except Exception:
        return None


class MenuBar(object):
    """툴 화면 위에 메뉴 바를 얹는다.

        bar = menu_bar.MenuBar(keep, tool_menu.tool_name_from_module(__name__),
                               tab_path=lambda: ["Copy Name"])
        umg.add(root, bar.wrap(body), weight=1.0, padding=(0, 0, 0, 0))

    keep      : 콜백 위젯을 붙잡아 둘 리스트 (umg.connect 참고 - 놓치면 GC 뒤 버튼이 죽는다)
    tool_name : 툴 폴더 이름 (Copy Tool Name 이 복사하는 값)
    tab_path  : 지금 보이는 탭(모드) 라벨 리스트, 또는 그걸 돌려주는 함수
    menus     : 툴 전용 메뉴 [(제목, [tool_menu.MenuItemSpec])]
    """

    def __init__(self, keep, tool_name, tab_path=None, menus=None):
        self.keep = keep
        self.tool_name = tool_name
        self.tab_path = tab_path
        self.menus = merge_menus(menus)
        self.titles = {}          # 제목 → 제목 버튼
        self.dropdowns = {}       # 제목 → 드롭다운 Border
        self.slots = {}           # 제목 → OverlaySlot
        self.items = {}           # (제목, 항목 라벨) → 항목 버튼
        self.open_title = None
        self.widget = None        # wrap() 이 만든 Overlay

        cells = []
        for title, _items in self.menus:
            button = umg.button(keep, title + ARROW, umg.bind(self._on_title, title), title)
            self.titles[title] = button
            cells.append(umg.fixed(button, padding=(0, 0, 2, 0)))
        self.message = umg.text("", umg.COLOR_DIM)
        cells.append(umg.stretch(self.message, padding=(8, 0, 4, 0)))
        self.bar = umg.row(*cells)

    # ── 조립 ──────────────────────────────────────────────────────────────
    def wrap(self, body):
        """메뉴 바 + body 를 담은 Overlay 를 돌려준다 (self.widget)."""
        frame = unreal.new_object(unreal.VerticalBox)
        umg.add(frame, self.bar, padding=(4, 3, 4, 1))
        umg.add(frame, body, weight=1.0, padding=(0, 0, 0, 0))

        overlay = unreal.new_object(unreal.Overlay)
        slot = overlay.add_child(frame)
        slot.set_horizontal_alignment(unreal.HorizontalAlignment.H_ALIGN_FILL)
        slot.set_vertical_alignment(unreal.VerticalAlignment.V_ALIGN_FILL)

        for title, items in self.menus:
            dropdown = self._build_dropdown(title, items)
            slot = overlay.add_child(dropdown)
            slot.set_horizontal_alignment(unreal.HorizontalAlignment.H_ALIGN_LEFT)
            slot.set_vertical_alignment(unreal.VerticalAlignment.V_ALIGN_TOP)
            self.dropdowns[title] = dropdown
            self.slots[title] = slot
        self.widget = overlay
        self.close()
        return overlay

    def _build_dropdown(self, title, items):
        box = unreal.new_object(unreal.VerticalBox)
        for spec in items:
            button = umg.button(self.keep, spec.label, umg.bind(self.run, title, spec.label),
                                spec.tooltip, align="left")
            self.items[(title, spec.label)] = button
            umg.add(box, button, padding=(0, 0, 0, 1))
        return umg.panel(box, COLOR_DROPDOWN, padding=3.0)

    # ── 동작 ──────────────────────────────────────────────────────────────
    def _on_title(self, title):
        if self.open_title == title:
            self.close()
        else:
            self.open(title)

    def open(self, title):
        """그 메뉴의 드롭다운을 제목 버튼 바로 아래에 연다 (다른 메뉴는 닫는다)."""
        self.close()
        left = 4.0
        for other, _items in self.menus:            # 앞쪽 제목 버튼 폭만큼 오른쪽으로
            if other == title:
                break
            size = _local_size(self.titles[other])
            left += (size.x if size else 0.0) + 2.0
        size = _local_size(self.bar)
        top = 3.0 + (size.y if size and size.y > 0 else FALLBACK_BAR_HEIGHT)
        self.slots[title].set_padding(unreal.Margin(left, top, 0.0, 0.0))
        self.dropdowns[title].set_visibility(unreal.SlateVisibility.VISIBLE)
        self.open_title = title

    def close(self):
        for dropdown in self.dropdowns.values():
            dropdown.set_visibility(unreal.SlateVisibility.COLLAPSED)
        self.open_title = None

    def log(self, message):
        """Output Log + 메뉴 바 오른쪽 글자."""
        unreal.log(message)
        self.message.set_text(message)

    def context(self):
        return tool_menu.MenuContext(self.tool_name, self.log, self.tab_path)

    def run(self, title, label):
        """메뉴 항목 실행 (드롭다운을 닫고 콜백). 반환: 콜백 결과."""
        self.close()
        for menu_title, items in self.menus:
            if menu_title != title:
                continue
            for spec in items:
                if spec.label == label:
                    try:
                        return spec.callback(self.context())
                    except Exception as error:
                        self.log("[{0}] Failed : {1}".format(label, error))
                        return False
        return None

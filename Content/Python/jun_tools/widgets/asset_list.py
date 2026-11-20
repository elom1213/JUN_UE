# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-11-20
#
# 공용 리스트 위젯 `AssetList` - 마야 `JUN_mod_tsl_qt_v01`(TSL) 의 언리얼 대응.
#
# TSL 은 마야 textScrollList 의 줄임말이라 언리얼 용어가 아니다. UMG 의 같은 역할은 `ListView` 인데,
# ListView 는 행 위젯 블루프린트(UserObjectListEntry 구현)가 에셋으로 하나 더 필요하다.
# 이 위젯은 에셋 없이 쓰려고 `ScrollBox` 에 행 버튼을 직접 쌓는다.
#
#   Base                         Number: 2      ← 제목(bold) + 개수
#   ┌──────────────────────────────┐
#   │ SK_Hero                      │   행을 누르면 선택(강조) + 콘텐츠 브라우저에서 그 에셋을 찾는다
#   │ (None)                       │   지워진 에셋은 빨간 (None)
#   └──────────────────────────────┘
#   [ Load Selected ]                           ← 마야 "Select Objects" (UE 의 Select 는 다른 뜻이라 Load)
#   [Add][Del][Up][Down][Sort]                  ← show_* 로 켜고 끈다. Reverse · Clear 는 기본 꺼짐
#
# 쓰는 법:
#   from jun_tools.widgets import asset_list
#   base = asset_list.AssetList(keep, "Base", on_changed=lambda items: ...)
#   umg.add(parent, base.widget, weight=1.0)
#   base.set_items([...]) / base.items() / base.append_unique([...])
#
# keep : 콜백을 단 위젯을 붙잡아 둘 리스트 (umg.connect 참고). 툴이 세션 동안 쥐고 있어야 한다.
# UI 문자열은 영어만.

import unreal

from . import umg

NULL_TEXT = "(None)"


def _default_selection():
    """콘텐츠 브라우저에서 선택한 에셋 (UObject 목록)."""
    try:
        return [a for a in unreal.EditorUtilityLibrary.get_selected_assets() or []]
    except Exception:
        return []


def _default_show(asset):
    """행을 누르면 콘텐츠 브라우저를 그 에셋으로 옮긴다."""
    try:
        unreal.EditorAssetLibrary.sync_browser_to_objects([asset.get_path_name()])
    except Exception:
        pass


def _default_label(asset):
    return asset.get_name()


def _default_tooltip(asset):
    return asset.get_path_name()


def _log(message):
    unreal.log("[JUNTools] {}".format(message))


class AssetList(object):
    """제목 + 개수 + 행 목록 + 버튼. 항목은 UObject(에셋)."""

    def __init__(self, keep, title="Assets", items=None, on_changed=None,
                 show_load=True, show_add=True, show_del=True, show_up=True, show_down=True,
                 show_sort=True, show_reverse=False, show_clear=False,
                 load_label="Load Selected", sort_label="Sort",
                 get_selection=None, on_row_clicked=None, label=None, tooltip=None):
        self.keep = keep
        self.title = title
        self.on_changed = on_changed
        self.get_selection = get_selection or _default_selection
        self.on_row_clicked = on_row_clicked or _default_show
        self.label = label or _default_label
        self.tooltip = tooltip or _default_tooltip
        self.selected_index = -1
        self._items = list(items or [])
        self._row_keep = []           # 행 버튼 - 다시 그릴 때마다 갈아 끼운다

        self.count = umg.text("Number: 0", umg.COLOR_DIM)
        self.rows = unreal.new_object(unreal.EditorUtilityScrollBox)
        self.buttons = {}

        header = umg.row(umg.stretch(umg.text(title, bold=True)), umg.fixed(self.count))
        body = umg.column(umg.fixed(header),
                          umg.stretch(umg.panel(self.rows, umg.COLOR_LIST, 2.0)))

        if show_load:
            self.buttons["load"] = umg.button(keep, load_label, umg.bind(self.load_selection),
                                              "Replace the list with the Content Browser selection.")
            umg.add(body, self.buttons["load"])

        small = []
        for key, shown, caption, handler, tip in (
                ("add", show_add, "Add", self.add_selection, "Add the Content Browser selection (no duplicates)."),
                ("del", show_del, "Del", self.remove_selected, "Remove the selected row."),
                ("up", show_up, "Up", self.move_up, "Move the selected row up."),
                ("down", show_down, "Down", self.move_down, "Move the selected row down."),
                ("sort", show_sort, sort_label, self.sort, "Sort by name."),
                ("reverse", show_reverse, "Reverse", self.reverse, "Reverse the order."),
                ("clear", show_clear, "Clear", self.clear, "Remove every row.")):
            if shown:
                self.buttons[key] = umg.button(keep, caption, umg.bind(handler), tip)
                small.append(umg.stretch(self.buttons[key]))
        if small:
            umg.add(body, umg.row(*small))

        self.widget = body
        keep.append(self.rows)
        self.refresh()

    # ── 항목 ────────────────────────────────────────────────────────────
    def items(self):
        return list(self._items)

    def set_items(self, items, notify=False):
        """항목을 바꾼다. notify=True 면 on_changed 를 부른다 (기본: 바깥에서 맞출 때라 부르지 않는다)."""
        self._items = list(items or [])
        if self.selected_index >= len(self._items):
            self.selected_index = len(self._items) - 1
        self.refresh()
        if notify:
            self._changed()

    def append_unique(self, items):
        """중복 없이 뒤에 붙인다. 반환: 붙인 개수."""
        known = {self._key(item) for item in self._items}
        added = 0
        for item in items or []:
            key = self._key(item)
            if key in known:
                continue
            known.add(key)
            self._items.append(item)
            added += 1
        return added

    @staticmethod
    def _key(item):
        return item.get_path_name() if item is not None else None

    # ── 버튼 동작 (마야 TSL 과 같은 이름) ──────────────────────────────
    def load_selection(self):
        selection = self.get_selection()
        if not selection:
            unreal.log_warning("[JUNTools] {}: nothing selected in the Content Browser.".format(self.title))
            return
        self._items = list(selection)
        self.selected_index = -1
        _log("{} <- {} selected asset(s).".format(self.title, len(selection)))
        self._update()

    def add_selection(self):
        selection = self.get_selection()
        if not selection:
            unreal.log_warning("[JUNTools] {}: nothing selected in the Content Browser.".format(self.title))
            return
        added = self.append_unique(selection)
        skipped = len(selection) - added
        _log("{}: {} added{}.".format(self.title, added,
                                      ", {} already in the list".format(skipped) if skipped else ""))
        self._update()

    def remove_selected(self):
        if not 0 <= self.selected_index < len(self._items):
            return
        del self._items[self.selected_index]
        self.selected_index = min(self.selected_index, len(self._items) - 1)
        self._update()

    def move_up(self):
        index = self.selected_index
        if 0 < index < len(self._items):
            self._items[index - 1], self._items[index] = self._items[index], self._items[index - 1]
            self.selected_index = index - 1
            self._update()

    def move_down(self):
        index = self.selected_index
        if 0 <= index < len(self._items) - 1:
            self._items[index + 1], self._items[index] = self._items[index], self._items[index + 1]
            self.selected_index = index + 1
            self._update()

    def sort(self):
        self._items.sort(key=lambda item: item.get_name().lower() if item is not None else "")
        self.selected_index = -1
        self._update()

    def reverse(self):
        self._items.reverse()
        self.selected_index = -1
        self._update()

    def clear(self):
        self._items = []
        self.selected_index = -1
        self._update()

    def select(self, index):
        """행 클릭: 그 행을 고르고(강조) on_row_clicked 를 부른다."""
        if not 0 <= index < len(self._items):
            return
        self.selected_index = index
        self.refresh()
        item = self._items[index]
        if item is not None:
            self.on_row_clicked(item)

    # ── 그리기 ──────────────────────────────────────────────────────────
    def _update(self):
        self.refresh()
        self._changed()

    def _changed(self):
        if self.on_changed is not None:
            self.on_changed(self.items())

    def refresh(self):
        self.rows.clear_children()
        self._row_keep = []
        for index, item in enumerate(self._items):
            if item is None:
                label = umg.text(NULL_TEXT, umg.COLOR_ERROR)
                tip = "This asset no longer exists."
            else:
                label = umg.text(self.label(item))
                tip = self.tooltip(item)
            holder = unreal.new_object(unreal.EditorUtilityButton)
            base_tint = umg.COLOR_SELECTED if index == self.selected_index else umg.COLOR_CLEAR
            holder.set_background_color(base_tint)
            slot = holder.add_child(label)
            slot.set_horizontal_alignment(unreal.HorizontalAlignment.H_ALIGN_LEFT)
            slot.set_padding(unreal.Margin(2, 0, 2, 0))
            holder.set_tool_tip_text(tip)
            holder.on_clicked.add_callable(umg.bind(self.select, index))
            if index != self.selected_index:
                holder.on_hovered.add_callable(_tint(holder, umg.COLOR_HOVER))
                holder.on_unhovered.add_callable(_tint(holder, umg.COLOR_CLEAR))
            self._row_keep.append(holder)
            self.rows.add_child(holder)
        self.count.set_text("Number: {}".format(len(self._items)))


def _tint(widget, tint):
    def _apply():
        widget.set_background_color(tint)
    return _apply

# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-11-20
#
# A00530 JUN_Renamer - EUW 탭 안의 화면을 파이썬으로 조립한다 (스파이크, v01.02).
#
# EUW `EUW_JUNRenamer` 의 루트는 변수로 노출된 `VerticalBox`(이름 `Root`) 하나뿐이다.
# 파이썬은 위젯 트리(WidgetTree)를 고칠 수 없지만, **실행 중에** `unreal.new_object()` 로 위젯을 만들어
# `PanelWidget.add_child()` 로 끼울 수는 있다 (5.4 헤드리스 실측). 그래서 화면 구성은 전부 코드에 둔다.
#   - 에셋과 코드의 약속은 `Root` 하나뿐 → 화면을 고칠 때 에셋(5.4 저장)을 건드리지 않는다.
#   - 코드라서 git diff 로 변경이 보인다.
#
# ── 스파이크의 목적 ──────────────────────────────────────────────────────────
# "파이썬이 만든 위젯이 탭 안에 실제로 그려지는가" 는 헤드리스로 볼 수 없다(커맨드렛은 탭을 만들지 않는다).
# 그래서 원본 Asset Renamer 모양의 일부(필터 줄 · Search/Replace 줄 · 열 제목 · 색 있는 목록)를 먼저 만들어
# 눈으로 확인한다. 아래쪽에는 기존 설정 패널(DetailsView, 역시 파이썬으로 생성)을 그대로 붙여
# 스파이크 중에도 툴의 모든 기능을 쓸 수 있게 했다. 두 화면은 **같은 설정 오브젝트**를 읽고 쓴다.
#
# UI 문자열은 전부 영어 (원본 Asset Renamer 는 한국어였다 - 전역 규칙 6장).

import importlib

import unreal

from . import core, naming

UI_MODULE = "jun_tools.tools.A00530_jun_renamer.ui"

# 원본 SHeaderRow 비율: Type 1 · Current 3 · Arrow 고정 · New 3 · Status 2
COLUMNS = [("Type", 1.0), ("Current Name", 3.0), ("", 0.0), ("New Name", 3.0), ("Status", 2.0)]

MATCH_OPTIONS = ["Anywhere", "Prefix Only", "Suffix Only"]   # naming.MATCH_* 순서

COLOR_TYPE = unreal.LinearColor(0.7, 0.7, 1.0, 1.0)     # 원본 타입 열 색
COLOR_READY = unreal.LinearColor(0.0, 1.0, 0.0, 1.0)     # 원본 Ready 초록
COLOR_DIM = unreal.LinearColor(0.5, 0.5, 0.5, 1.0)       # 원본 비활성 회색
COLOR_TEXT = unreal.LinearColor(1.0, 1.0, 1.0, 1.0)

# 이름 필터는 원본처럼 2 글자부터 거른다 (비우면 전부).
NAME_FILTER_MIN = 2


def _ui():
    return importlib.import_module(UI_MODULE)


# ---------------------------------------------------------------------------
# 위젯 헬퍼
# ---------------------------------------------------------------------------

def _color(linear):
    return unreal.SlateColor(specified_color=linear)


def text(label, color=None):
    widget = unreal.new_object(unreal.TextBlock)
    widget.set_text(label)
    if color is not None:
        widget.set_color_and_opacity(_color(color))
    return widget


def button(label, callback, tooltip=""):
    widget = unreal.new_object(unreal.Button)
    widget.add_child(text(label))
    if tooltip:
        widget.set_tool_tip_text(tooltip)
    widget.on_clicked.add_callable(callback)
    return widget


def text_box(hint="", value=""):
    widget = unreal.new_object(unreal.EditableTextBox)
    if hint:
        widget.set_hint_text(hint)
    if value:
        widget.set_text(value)
    return widget


def fill(slot, weight=1.0):
    """박스 슬롯을 남는 공간을 weight 비율로 채우게 한다."""
    size = unreal.SlateChildSize()
    size.set_editor_property("value", weight)
    size.set_editor_property("size_rule", unreal.SlateSizeRule.FILL)
    slot.set_size(size)
    return slot


def pad(slot, left=4.0, top=2.0, right=4.0, bottom=2.0):
    slot.set_padding(unreal.Margin(left, top, right, bottom))
    return slot


def middle(slot):
    slot.set_vertical_alignment(unreal.VerticalAlignment.V_ALIGN_CENTER)
    return slot


def row_box(*children):
    """(widget, weight) 들을 가로로 놓는다. weight 0 = 내용 크기만큼."""
    box = unreal.new_object(unreal.HorizontalBox)
    for widget, weight in children:
        slot = middle(pad(box.add_child(widget)))
        if weight:
            fill(slot, weight)
    return box


# ---------------------------------------------------------------------------
# 조립
# ---------------------------------------------------------------------------

class TabView(object):
    """탭 안의 위젯 참조 모음. 세션 저장소(_state["tab"])에 붙잡아 둔다."""

    def __init__(self, settings):
        self.settings = settings
        self.root = None
        self.name_filter = None
        self.match_count = None
        self.search = None
        self.replace = None
        self.match_mode = None
        self.rows = None
        self.status = None
        self.details_view = None


def build(root, settings):
    """root(VerticalBox) 를 비우고 화면을 조립한다. 반환: TabView."""
    view = TabView(settings)
    view.root = root
    root.clear_children()

    pad(root.add_child(text("UI test (spike) - Python-built widgets. The panel below is the full tool.",
                            COLOR_DIM)), 6, 4, 6, 4)

    # ── 이름 필터 줄 (원본 "Name Filter" 줄) ──────────────────────────────
    view.name_filter = text_box("Search asset names (e.g. SK_, MT_, Character)...",
                                settings.get_editor_property("name_filter"))
    view.name_filter.on_text_changed.add_callable(lambda value: _ui_tab().on_name_filter(value))
    view.match_count = text("0/0 matched")
    load_selected = button("Load Selected", lambda: _ui().load_selected(_ui().settings()),
                           "Load the assets selected in the Content Browser.")
    root.add_child(row_box((text("Name Filter:"), 0), (view.name_filter, 1.0),
                           (view.match_count, 0), (load_selected, 0)))

    # ── Search / Replace 줄 (원본 "Search / Replace / match mode" 줄) ──────
    view.search = text_box("Text to find", settings.get_editor_property("search"))
    view.replace = text_box("Text to replace", settings.get_editor_property("replace"))
    view.search.on_text_committed.add_callable(
        lambda value, method: _ui_tab().on_field("search", value))
    view.replace.on_text_committed.add_callable(
        lambda value, method: _ui_tab().on_field("replace", value))
    view.match_mode = unreal.new_object(unreal.ComboBoxString)
    for option in MATCH_OPTIONS:
        view.match_mode.add_option(option)
    view.match_mode.set_selected_index(
        int(getattr(settings.get_editor_property("match_mode"), "value",
                    settings.get_editor_property("match_mode"))))
    view.match_mode.on_selection_changed.add_callable(
        lambda item, how: _ui_tab().on_match_mode(item))
    root.add_child(row_box((text("Search:"), 0), (view.search, 1.0),
                           (text("Replace:"), 0), (view.replace, 1.0), (view.match_mode, 0)))

    # ── 상태 줄 + 열 제목 + 목록 ──────────────────────────────────────────
    view.status = text("Ready")
    pad(root.add_child(view.status), 6, 4, 6, 2)
    root.add_child(row_box(*[(text(label, COLOR_DIM), weight) for label, weight in COLUMNS]))
    view.rows = unreal.new_object(unreal.ScrollBox)
    fill(pad(root.add_child(view.rows)), 0.45)

    # ── 기존 설정 패널 (툴 전체 기능) ─────────────────────────────────────
    view.details_view = unreal.new_object(unreal.DetailsView)
    fill(root.add_child(view.details_view), 0.55)
    view.details_view.set_object(settings)
    return view


def _ui_tab():
    return importlib.import_module(__name__)


def _view():
    return _ui()._state.get("tab")


# ---------------------------------------------------------------------------
# 이벤트 → 설정 오브젝트 → 미리보기
# ---------------------------------------------------------------------------

def on_name_filter(value):
    value = str(value)
    if value and len(value) < NAME_FILTER_MIN:
        return
    ui = _ui()
    ui.settings().set_editor_property("name_filter", value)
    ui.preview_rename(ui.settings())


def on_field(name, value):
    ui = _ui()
    ui.settings().set_editor_property(name, str(value))
    ui.preview_rename(ui.settings())


def on_match_mode(item):
    ui = _ui()
    index = MATCH_OPTIONS.index(str(item)) if str(item) in MATCH_OPTIONS else naming.MATCH_ANYWHERE
    ui.settings().set_editor_property("match_mode", ui._to_match_enum(index))
    ui.preview_rename(ui.settings())


def sync_fields(view):
    """설정 패널에서 바뀐 값을 위쪽 입력칸에도 맞춘다 (같은 오브젝트를 두 화면이 쓴다)."""
    settings = view.settings
    for widget, name in ((view.name_filter, "name_filter"), (view.search, "search"),
                         (view.replace, "replace")):
        current = str(settings.get_editor_property(name))
        if str(widget.get_text()) != current:
            widget.set_text(current)
    index = int(getattr(settings.get_editor_property("match_mode"), "value",
                        settings.get_editor_property("match_mode")))
    if view.match_mode.get_selected_index() != index:
        view.match_mode.set_selected_index(index)


def _show_in_browser(package):
    """행 클릭 콜백. 언리얼 델리게이트는 기본값 인자까지 인자 수로 세므로(`lambda p=...` 는 거부된다)
    클로저로 package 를 묶는다."""
    def _click():
        core.sync_browser(package)
    return _click


def show_rows(rows, shown, total):
    """미리보기 행을 목록에 그린다. ui.preview_rename() 이 부른다."""
    view = _view()
    if view is None:
        return
    view.rows.clear_children()
    for row in rows:
        ready = row.ready
        name_color = COLOR_READY if ready else COLOR_DIM
        line = row_box(
            (text(row.type_name, COLOR_TYPE), 1.0),
            (text(row.old_name, COLOR_TEXT), 3.0),
            (text("->", COLOR_READY if ready else COLOR_DIM), 0),
            (text(row.new_name or "?", name_color), 3.0),
            (text(row.status, COLOR_TEXT if ready else COLOR_DIM), 2.0),
        )
        # 원본은 행을 더블클릭하면 콘텐츠 브라우저에서 그 에셋을 찾는다. 스파이크는 행 버튼 클릭으로.
        holder = unreal.new_object(unreal.Button)
        holder.add_child(line)
        holder.set_tool_tip_text("Click to show {} in the Content Browser.".format(row.old_package))
        holder.on_clicked.add_callable(_show_in_browser(row.old_package))
        view.rows.add_child(holder)

    ready_count = sum(1 for row in rows if row.ready)
    view.match_count.set_text("{}/{} matched".format(shown, total))
    view.status.set_text("{} assets loaded, {} will be renamed".format(len(rows), ready_count))
    sync_fields(view)

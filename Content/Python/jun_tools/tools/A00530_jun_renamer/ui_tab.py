# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-11-20
#
# A00530 JUN_Renamer - EUW 탭 안의 화면을 파이썬으로 조립한다 (스파이크, v01.03).
#
# EUW `EUW_JUNRenamer` 의 루트는 변수로 노출된 `VerticalBox`(이름 `Root`) 하나뿐이다.
# 파이썬은 위젯 트리(WidgetTree)를 고칠 수 없지만, **실행 중에** `unreal.new_object()` 로 위젯을 만들어
# `PanelWidget.add_child()` 로 끼울 수는 있다 (5.4 헤드리스 실측). 그래서 화면 구성은 전부 코드에 둔다.
#   - 에셋과 코드의 약속은 `Root` 하나뿐 → 화면을 고칠 때 에셋(5.4 저장)을 건드리지 않는다.
#   - 코드라서 git diff 로 변경이 보인다.
#
# ── v01.03 에서 고친 두 가지 (사용자 스크린샷 .ref/renamer_01~02.png) ─────────────
# 1) 글자가 아주 컸다 — `unreal.TextBlock / Button / EditableTextBox` 는 **게임용 기본 스타일**(글꼴 24,
#    밝은 입력칸, 흰 버튼)을 쓴다. 엔진에 에디터 스타일을 입힌 같은 위젯이 따로 있다(Blutility
#    `EditorUtilityButton` · `EditorUtilityEditableTextBox` · `EditorUtilityComboBoxString` · `EditorUtilityScrollBox`,
#    생성자에서 `FDefaultStyleCache::GetEditor()` 스타일을 입힌다). 그것들로 바꿨다.
#    TextBlock 은 에디터 판이 없어서, 에디터 입력칸 스타일의 글꼴을 가져와 입힌다(`editor_font()`).
# 2) 새 Load Selected 버튼이 동작하지 않았다 — `add_callable` 이 만드는 중계 오브젝트
#    (UPythonCallableForDelegate)는 **파이썬이 참조를 쥔 위젯의 델리게이트를 통해서만** GC 에서 지켜진다
#    (`FPyReferenceCollector::AddReferencedObjectsFromMulticastDelegate`). 스파이크는 그 버튼을 지역 변수로 만들고
#    버려서, 에디터의 주기 GC 뒤 연결이 소리 없이 끊겼다(헤드리스 `obj gc` 로 재현 · 확인).
#    → 콜백을 단 위젯은 전부 `TabView.keep` 에 넣어 세션 동안 붙잡는다(`connect()`).
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
COLOR_TEXT = unreal.LinearColor(0.85, 0.85, 0.85, 1.0)
COLOR_PANEL = unreal.LinearColor(0.012, 0.012, 0.012, 1.0)   # 원본 "ToolPanel.GroupBorder" 비슷한 어두운 박스
COLOR_ROW_HOVER = unreal.LinearColor(1.0, 1.0, 1.0, 0.06)
COLOR_CLEAR = unreal.LinearColor(1.0, 1.0, 1.0, 0.0)

# 에디터 기본 글자 크기. 에디터 입력칸 스타일에서 못 읽으면 이 값을 쓴다.
FALLBACK_FONT_SIZE = 9

# 이름 필터는 원본처럼 2 글자부터 거른다 (비우면 전부).
NAME_FILTER_MIN = 2


def _ui():
    return importlib.import_module(UI_MODULE)


def _ui_tab():
    return importlib.import_module(__name__)


def _view():
    return _ui()._state.get("tab")


# ---------------------------------------------------------------------------
# 에디터 글꼴
# ---------------------------------------------------------------------------

_FONT = {}


def editor_font(bold=False):
    """에디터 기본 글꼴(SlateFontInfo). 에디터 입력칸 스타일의 글꼴을 빌려 온다."""
    key = "bold" if bold else "regular"
    if key in _FONT:
        return _FONT[key]

    font = None
    try:
        style = unreal.new_object(unreal.EditorUtilityEditableTextBox).get_editor_property("widget_style")
        for path in (("text_style", "font"), ("font",)):
            try:
                value = style
                for name in path:
                    value = value.get_editor_property(name)
                if value.get_editor_property("font_object") is not None:
                    font = value
                    break
            except Exception:
                continue
    except Exception:
        font = None

    if font is None:
        font = unreal.new_object(unreal.TextBlock).get_editor_property("font")
        font.set_editor_property("size", FALLBACK_FONT_SIZE)

    # get_editor_property 는 구조체 사본을 돌려준다 - 고쳐도 원본 스타일은 그대로다.
    if bold:
        font.set_editor_property("typeface_font_name", "Bold")
    _FONT[key] = font
    return font


# ---------------------------------------------------------------------------
# 위젯 헬퍼 - 콜백은 전부 connect() 로 단다 (위젯을 붙잡아 GC 에서 지킨다)
# ---------------------------------------------------------------------------

def connect(view, widget, delegate_name, callback):
    """widget.<delegate_name> 에 callback 을 달고 widget 을 view.keep 에 넣는다."""
    getattr(widget, delegate_name).add_callable(callback)
    view.keep.append(widget)
    return widget


def _color(linear):
    return unreal.SlateColor(specified_color=linear)


def text(label, color=None, bold=False):
    widget = unreal.new_object(unreal.TextBlock)
    widget.set_font(editor_font(bold))
    widget.set_text(label)
    widget.set_color_and_opacity(_color(color or COLOR_TEXT))
    return widget


def button(view, label, callback, tooltip=""):
    widget = unreal.new_object(unreal.EditorUtilityButton)
    middle(widget.add_child(text(label)))
    if tooltip:
        widget.set_tool_tip_text(tooltip)
    return connect(view, widget, "on_clicked", callback)


def text_box(hint="", value=""):
    widget = unreal.new_object(unreal.EditorUtilityEditableTextBox)
    if hint:
        widget.set_hint_text(hint)
    if value:
        widget.set_text(value)
    return widget


def combo(options, index=0):
    widget = unreal.new_object(unreal.EditorUtilityComboBoxString)
    try:
        widget.set_editor_property("font", editor_font())
    except Exception:
        pass
    for option in options:
        widget.add_option(option)
    widget.set_selected_index(index)
    return widget


def fill(slot, weight=1.0):
    """박스 슬롯을 남는 공간을 weight 비율로 채우게 한다."""
    size = unreal.SlateChildSize()
    size.set_editor_property("value", weight)
    size.set_editor_property("size_rule", unreal.SlateSizeRule.FILL)
    slot.set_size(size)
    return slot


def pad(slot, left=2.0, top=1.0, right=2.0, bottom=1.0):
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


def group(*rows):
    """원본 SBorder("ToolPanel.GroupBorder") 처럼 어두운 박스에 줄들을 담는다."""
    border = unreal.new_object(unreal.Border)
    border.set_brush_color(COLOR_PANEL)
    border.set_padding(unreal.Margin(5, 5, 5, 5))
    column = unreal.new_object(unreal.VerticalBox)
    for row in rows:
        pad(column.add_child(row), 0, 2, 0, 2)
    border.set_content(column)
    return border


# ---------------------------------------------------------------------------
# 조립
# ---------------------------------------------------------------------------

class TabView(object):
    """탭 안의 위젯 참조 모음. 세션 저장소(_state["tab"])에 붙잡아 둔다."""

    def __init__(self, settings):
        self.settings = settings
        self.keep = []          # 콜백을 단 위젯 - 파이썬이 쥐고 있어야 GC 뒤에도 콜백이 산다
        self.row_keep = []      # 목록 행 버튼 (목록을 다시 그릴 때마다 갈아 끼운다)
        self.root = None
        self.name_filter = None
        self.match_count = None
        self.search = None
        self.replace = None
        self.match_mode = None
        self.load_selected = None
        self.rows = None
        self.status = None
        self.details_view = None


def build(root, settings):
    """root(VerticalBox) 를 비우고 화면을 조립한다. 반환: TabView."""
    view = TabView(settings)
    view.root = root
    root.clear_children()

    # ── 필터 박스 (원본 첫 번째 SBorder) ──────────────────────────────────
    view.name_filter = text_box("Search asset names (e.g. SK_, MT_, Character)...",
                                settings.get_editor_property("name_filter"))
    connect(view, view.name_filter, "on_text_changed", lambda value: _ui_tab().on_name_filter(value))
    view.match_count = text("0/0 matched")
    view.load_selected = button(view, "Load Selected",
                                lambda: _ui().load_selected(_ui().settings()),
                                "Load the assets selected in the Content Browser.")
    filters = row_box((text("Name Filter:", bold=True), 0), (view.name_filter, 1.0),
                      (view.match_count, 0), (view.load_selected, 0))

    # ── 옵션 박스 (원본 두 번째 SBorder) ──────────────────────────────────
    view.search = text_box("Text to find", settings.get_editor_property("search"))
    view.replace = text_box("Text to replace", settings.get_editor_property("replace"))
    connect(view, view.search, "on_text_committed",
            lambda value, method: _ui_tab().on_field("search", value))
    connect(view, view.replace, "on_text_committed",
            lambda value, method: _ui_tab().on_field("replace", value))
    view.match_mode = combo(MATCH_OPTIONS, _match_index(settings))
    connect(view, view.match_mode, "on_selection_changed",
            lambda item, how: _ui_tab().on_match_mode(item))
    options = row_box((text("Search:"), 0), (view.search, 1.0),
                      (text("Replace:"), 0), (view.replace, 1.0), (view.match_mode, 0))

    pad(root.add_child(group(filters)), 5, 5, 5, 2)
    pad(root.add_child(group(options)), 5, 2, 5, 2)

    # ── 상태 줄 + 열 제목 + 목록 ──────────────────────────────────────────
    view.status = text("Ready")
    pad(root.add_child(view.status), 7, 2, 7, 2)
    header = row_box(*[(text(label, COLOR_DIM, bold=True), weight) for label, weight in COLUMNS])
    pad(root.add_child(header), 5, 0, 5, 0)
    view.rows = unreal.new_object(unreal.EditorUtilityScrollBox)
    fill(pad(root.add_child(view.rows), 5, 0, 5, 2), 0.45)

    # ── 기존 설정 패널 (툴 전체 기능) ─────────────────────────────────────
    view.details_view = unreal.new_object(unreal.DetailsView)
    fill(root.add_child(view.details_view), 0.55)
    view.details_view.set_object(settings)
    view.keep.append(view.details_view)
    return view


def _match_index(settings):
    value = settings.get_editor_property("match_mode")
    return int(getattr(value, "value", value))


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
    index = _match_index(settings)
    if view.match_mode.get_selected_index() != index:
        view.match_mode.set_selected_index(index)


def _show_in_browser(package):
    """행 클릭 콜백. 언리얼 델리게이트는 기본값 인자까지 인자 수로 세므로(`lambda p=...` 는 거부된다)
    클로저로 package 를 묶는다."""
    def _click():
        core.sync_browser(package)
    return _click


def _tint(widget, color):
    def _apply():
        widget.set_background_color(color)
    return _apply


def show_rows(rows, shown, total):
    """미리보기 행을 목록에 그린다. ui.preview_rename() 이 부른다."""
    view = _view()
    if view is None:
        return
    view.rows.clear_children()
    view.row_keep = []
    for row in rows:
        ready = row.ready
        line = row_box(
            (text(row.type_name, COLOR_TYPE), 1.0),
            (text(row.old_name), 3.0),
            (text("->", COLOR_READY if ready else COLOR_DIM), 0),
            (text(row.new_name or "?", COLOR_READY if ready else COLOR_DIM), 3.0),
            (text(row.status, COLOR_TEXT if ready else COLOR_DIM), 2.0),
        )
        # 행 = 투명한 버튼. 마우스를 올리면 살짝 밝아지고, 누르면 콘텐츠 브라우저에서 그 에셋을 찾는다.
        # (원본은 더블클릭. 버튼은 한 번 클릭만 받는다.)
        holder = unreal.new_object(unreal.EditorUtilityButton)
        holder.set_background_color(COLOR_CLEAR)
        slot = holder.add_child(line)
        slot.set_horizontal_alignment(unreal.HorizontalAlignment.H_ALIGN_FILL)
        slot.set_padding(unreal.Margin(0, 0, 0, 0))
        holder.set_tool_tip_text("Click to show {} in the Content Browser.".format(row.old_package))
        holder.on_clicked.add_callable(_show_in_browser(row.old_package))
        holder.on_hovered.add_callable(_tint(holder, COLOR_ROW_HOVER))
        holder.on_unhovered.add_callable(_tint(holder, COLOR_CLEAR))
        view.row_keep.append(holder)
        view.rows.add_child(holder)

    ready_count = sum(1 for row in rows if row.ready)
    view.match_count.set_text("{}/{} matched".format(shown, total))
    view.status.set_text("{} assets loaded, {} will be renamed".format(len(rows), ready_count))
    sync_fields(view)

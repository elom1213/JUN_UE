# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-11-20
#
# A00530 JUN_Renamer - EUW 탭 안의 화면을 파이썬으로 조립한다 (v01.04).
#
# EUW `EUW_JUNRenamer` 의 루트는 변수로 노출된 `VerticalBox`(이름 `Root`) 하나뿐이다. 화면은 실행 중에
# 공용 헬퍼 `jun_tools.widgets.umg` 로 만든다 (에디터 스타일 위젯 · GC 에 안전한 콜백 - 그 모듈 머리말 참고).
#
#   Help v                         ← 공용 메뉴 바 (Copy Tool Name · Copy Tool Name + Tabs, v01.08)
#   Mode: [Default v]
#   ├ Default   : 원본 Asset Renamer 모양(필터 · Search/Replace · 목록) + 설정 패널(Assets · Rename 섹션만)
#   └ Copy Name : Base / Targets 리스트(공용 AssetList) + Prefix · Suffix · Search · Replace · Case Sensitive
#                 + 미리보기 + Copy Name 버튼                                   ← v01.04, 계획서 CopyNameMode_Plan
#
# 값의 정본은 설정 오브젝트(ui.settings())다. 입력칸 · 리스트 → 설정 → ui.preview_rename / preview_copy →
# show_rows / show_copy_rows 가 다시 그린다. 설정 패널에서 바뀐 값도 같은 길로 입력칸에 돌아온다.
#
# UI 문자열은 전부 영어.

import importlib

import unreal

from jun_tools.widgets import asset_list, menu_bar, tool_menu, umg

from . import naming

UI_MODULE = "jun_tools.tools.A00530_jun_renamer.ui"

MODES = ["Default", "Copy Name"]
MODE_DEFAULT, MODE_COPY = 0, 1

# 원본 SHeaderRow 비율: Type 1 · Current 3 · Arrow 고정 · New 3 · Status 2
COLUMNS = [("Type", 1.0), ("Current Name", 3.0), ("", 0.0), ("New Name", 3.0), ("Status", 2.0)]
COPY_COLUMNS = [("Base", 3.0), ("Target", 3.0), ("", 0.0), ("New Name", 3.0), ("Status", 2.0)]

MATCH_OPTIONS = ["Anywhere", "Prefix Only", "Suffix Only"]   # naming.MATCH_* 순서

COLOR_TYPE = unreal.LinearColor(0.7, 0.7, 1.0, 1.0)     # 원본 타입 열 색
COLOR_READY = unreal.LinearColor(0.0, 1.0, 0.0, 1.0)     # 원본 Ready 초록
COLOR_WARN = unreal.LinearColor(1.0, 0.8, 0.2, 1.0)

# 설정 패널에 보일 섹션. Copy Name 은 Copy Name 모드 화면으로 옮겨서 뺀다.
PANEL_CATEGORIES = ["Assets", "Rename"]

# 이름 필터는 원본처럼 2 글자부터 거른다 (비우면 전부).
NAME_FILTER_MIN = 2


def _ui():
    return importlib.import_module(UI_MODULE)


def _ui_tab():
    return importlib.import_module(__name__)


def _view():
    return _ui()._state.get("tab")


def _callback(name, *args):
    """이 모듈의 함수를 **부를 때 다시 찾는** 콜백 (DEV_MODE 리로드 뒤에도 최신 코드). 인자 없는 이벤트용."""
    def _call():
        return getattr(_ui_tab(), name)(*args)
    return _call


# ---------------------------------------------------------------------------
# 조립
# ---------------------------------------------------------------------------

class TabView(object):
    """탭 안의 위젯 참조 모음. 세션 저장소(_state["tab"])에 붙잡아 둔다."""

    def __init__(self, settings):
        self.settings = settings
        self.keep = []          # 콜백을 단 위젯 - 파이썬이 쥐고 있어야 GC 뒤에도 콜백이 산다
        self.row_keep = []      # Default 목록 행
        self.copy_row_keep = [] # Copy Name 미리보기 행
        self.root = None
        self.menu_bar = None    # 공용 MenuBar (Help 메뉴)
        self.mode = None
        self.pages = None
        # Default
        self.name_filter = None
        self.match_count = None
        self.search = None
        self.replace = None
        self.match_mode = None
        self.load_selected = None
        self.rows = None
        self.status = None
        self.details_view = None
        # Copy Name
        self.base_list = None
        self.targets_list = None
        self.copy_fields = {}
        self.copy_case = None
        self.copy_status = None
        self.copy_rows = None
        self.copy_button = None
        self.rename_button = None   # Default 페이지 아래 오른쪽 (Copy Name 버튼과 같은 자리)


def build(root, settings):
    """root(VerticalBox) 를 비우고 화면을 조립한다. 반환: TabView."""
    view = TabView(settings)
    view.root = root
    root.clear_children()
    body = unreal.new_object(unreal.VerticalBox)

    # ── 모드 ──────────────────────────────────────────────────────────────
    view.mode = umg.combo(MODES, _ui()._state.get("mode", MODE_DEFAULT))
    umg.connect(view.keep, view.mode, "on_selection_changed",
                lambda item, how: _ui_tab().on_mode(item))
    umg.add(body, umg.row(umg.fixed(umg.text("Mode:", bold=True)), umg.fixed(view.mode)),
            padding=(5, 4, 5, 2))

    view.pages = unreal.new_object(unreal.WidgetSwitcher)
    for page in (_build_default(view, settings), _build_copy(view, settings)):
        slot = view.pages.add_child(page)
        slot.set_horizontal_alignment(unreal.HorizontalAlignment.H_ALIGN_FILL)
        slot.set_vertical_alignment(unreal.VerticalAlignment.V_ALIGN_FILL)
    umg.add(body, view.pages, weight=1.0, padding=(0, 0, 0, 0))
    view.pages.set_active_widget_index(view.mode.get_selected_index())

    # ── 메뉴 바 (공용) - 모드를 마야의 "탭" 처럼 Copy Tool Name + Tabs 에 넣는다 ──
    view.menu_bar = menu_bar.MenuBar(view.keep, tool_menu.tool_name_from_module(__name__),
                                     tab_path=lambda: [str(view.mode.get_selected_option())])
    umg.add(root, view.menu_bar.wrap(body), weight=1.0, padding=(0, 0, 0, 0))
    return view


def _build_default(view, settings):
    page = unreal.new_object(unreal.VerticalBox)

    # 필터 박스 (원본 첫 번째 SBorder)
    view.name_filter = umg.text_box("Search asset names (e.g. SK_, MT_, Character)...",
                                    settings.get_editor_property("name_filter"))
    umg.connect(view.keep, view.name_filter, "on_text_changed",
                lambda value: _ui_tab().on_name_filter(value))
    view.match_count = umg.text("0/0 matched")
    view.load_selected = umg.button(view.keep, "Load Selected", _callback("on_load_selected"),
                                    "Load the assets selected in the Content Browser.")
    filters = umg.row(umg.fixed(umg.text("Name Filter:", bold=True)), umg.stretch(view.name_filter),
                      umg.fixed(view.match_count), umg.fixed(view.load_selected))

    # 옵션 박스 (원본 두 번째 SBorder)
    view.search = umg.text_box("Text to find", settings.get_editor_property("search"))
    view.replace = umg.text_box("Text to replace", settings.get_editor_property("replace"))
    umg.connect(view.keep, view.search, "on_text_committed",
                lambda value, method: _ui_tab().on_field("search", value))
    umg.connect(view.keep, view.replace, "on_text_committed",
                lambda value, method: _ui_tab().on_field("replace", value))
    view.match_mode = umg.combo(MATCH_OPTIONS, _match_index(settings))
    umg.connect(view.keep, view.match_mode, "on_selection_changed",
                lambda item, how: _ui_tab().on_match_mode(item))
    options = umg.row(umg.fixed(umg.text("Search:")), umg.stretch(view.search),
                      umg.fixed(umg.text("Replace:")), umg.stretch(view.replace),
                      umg.fixed(view.match_mode))

    umg.add(page, umg.panel(filters), padding=(5, 2, 5, 2))
    umg.add(page, umg.panel(options), padding=(5, 2, 5, 2))

    # 상태 줄 + 열 제목 + 목록
    view.status = umg.text("Ready")
    umg.add(page, view.status, padding=(7, 2, 7, 2))
    umg.add(page, _header(COLUMNS), padding=(5, 0, 5, 0))
    view.rows = unreal.new_object(unreal.EditorUtilityScrollBox)
    view.keep.append(view.rows)
    umg.add(page, view.rows, weight=0.45, padding=(5, 0, 5, 2))

    # 설정 패널 - Assets · Rename 섹션만 (Copy Name 은 Copy Name 모드 화면에 있다)
    view.details_view = unreal.new_object(unreal.DetailsView)
    view.details_view.set_editor_property("categories_to_show", PANEL_CATEGORIES)
    view.details_view.set_object(settings)
    view.keep.append(view.details_view)
    umg.add(page, view.details_view, weight=0.55, padding=(0, 0, 0, 0))

    # 실행 - Copy Name 모드의 Copy Name 버튼과 같은 자리 (페이지 맨 아래 오른쪽)
    view.rename_button = umg.button(view.keep, "Rename", _callback("on_rename"),
                                    "Rename every Ready row and save. Asks first.")
    umg.add(page, umg.row(umg.stretch(umg.text("")), umg.fixed(view.rename_button)),
            padding=(5, 2, 5, 5))
    return page


def _build_copy(view, settings):
    page = unreal.new_object(unreal.VerticalBox)

    # Base / Targets 리스트 (공용 AssetList - 마야 TSL 대응)
    view.base_list = asset_list.AssetList(
        view.keep, "Base", items=list(settings.get_editor_property("base")),
        on_changed=lambda items: _ui_tab().on_list_changed("base", items))
    view.targets_list = asset_list.AssetList(
        view.keep, "Targets", items=list(settings.get_editor_property("targets")),
        on_changed=lambda items: _ui_tab().on_list_changed("targets", items))
    lists = umg.row(umg.stretch(view.base_list.widget), umg.stretch(view.targets_list.widget))
    umg.add(page, umg.panel(lists), weight=0.45, padding=(5, 2, 5, 2))

    # 이름 칸
    for name, hint in (("copy_prefix", "Added in front"), ("copy_suffix", "Added at the end"),
                       ("copy_search", "Text to find in the Base name"),
                       ("copy_replace", "Text to replace")):
        box = umg.text_box(hint, settings.get_editor_property(name))
        umg.connect(view.keep, box, "on_text_committed",
                    _commit_handler(name))
        view.copy_fields[name] = box
    case_row, view.copy_case = umg.check_box("Case Sensitive",
                                             settings.get_editor_property("copy_case_sensitive"))
    umg.connect(view.keep, view.copy_case, "on_check_state_changed",
                lambda checked: _ui_tab().on_copy_case(checked))
    fields = umg.column(
        umg.fixed(umg.row(umg.fixed(umg.text("Prefix:")), umg.stretch(view.copy_fields["copy_prefix"]),
                          umg.fixed(umg.text("Suffix:")), umg.stretch(view.copy_fields["copy_suffix"]))),
        umg.fixed(umg.row(umg.fixed(umg.text("Search:")), umg.stretch(view.copy_fields["copy_search"]),
                          umg.fixed(umg.text("Replace:")), umg.stretch(view.copy_fields["copy_replace"]),
                          umg.fixed(case_row))))
    umg.add(page, umg.panel(fields), padding=(5, 2, 5, 2))

    # 상태 줄 + 열 제목 + 미리보기
    view.copy_status = umg.text("Load Base and Targets.")
    umg.add(page, view.copy_status, padding=(7, 2, 7, 2))
    umg.add(page, _header(COPY_COLUMNS), padding=(5, 0, 5, 0))
    view.copy_rows = unreal.new_object(unreal.EditorUtilityScrollBox)
    view.keep.append(view.copy_rows)
    umg.add(page, view.copy_rows, weight=0.55, padding=(5, 0, 5, 2))

    # 실행
    view.copy_button = umg.button(view.keep, "Copy Name", _callback("on_copy_name"),
                                  "Rename Targets[i] to Prefix + Base[i] + Suffix and save. Asks first.")
    umg.add(page, umg.row(umg.stretch(umg.text("")), umg.fixed(view.copy_button)),
            padding=(5, 2, 5, 5))
    return page


def _header(columns):
    return umg.row(*[(umg.text(label, umg.COLOR_DIM, bold=True), weight) for label, weight in columns])


def _commit_handler(name):
    def _commit(value, method):
        _ui_tab().on_copy_field(name, value)
    return _commit


def _match_index(settings):
    value = settings.get_editor_property("match_mode")
    return int(getattr(value, "value", value))


# ---------------------------------------------------------------------------
# 이벤트 → 설정 오브젝트 → 미리보기
# ---------------------------------------------------------------------------

def on_mode(item):
    index = MODES.index(str(item)) if str(item) in MODES else MODE_DEFAULT
    ui = _ui()
    ui._state["mode"] = index
    view = _view()
    if view is not None:
        view.pages.set_active_widget_index(index)
    if index == MODE_COPY:
        ui.preview_copy(ui.settings())
    else:
        ui.preview_rename(ui.settings())


def on_load_selected():
    ui = _ui()
    ui.load_selected(ui.settings())


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


def on_list_changed(name, items):
    ui = _ui()
    ui.settings().set_editor_property(name, items)
    ui.preview_copy(ui.settings())


def on_copy_field(name, value):
    ui = _ui()
    ui.settings().set_editor_property(name, str(value))
    ui.preview_copy(ui.settings())


def on_copy_case(checked):
    ui = _ui()
    ui.settings().set_editor_property("copy_case_sensitive", bool(checked))
    ui.preview_copy(ui.settings())


def on_rename():
    ui = _ui()
    ui.execute_rename(ui.settings())


def on_copy_name():
    ui = _ui()
    ui.execute_copy(ui.settings())


# ---------------------------------------------------------------------------
# 그리기
# ---------------------------------------------------------------------------

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
    """행 클릭 콜백 (인자 없는 이벤트라 package 를 클로저로 묶는다)."""
    def _click():
        _ui().core.sync_browser(package)
    return _click


def _tint(widget, tint):
    def _apply():
        widget.set_background_color(tint)
    return _apply


def _row_button(line, package, keep):
    """행 = 투명한 버튼. 마우스를 올리면 살짝 밝아지고, 누르면 콘텐츠 브라우저에서 그 에셋을 찾는다."""
    holder = unreal.new_object(unreal.EditorUtilityButton)
    holder.set_background_color(umg.COLOR_CLEAR)
    slot = holder.add_child(line)
    slot.set_horizontal_alignment(unreal.HorizontalAlignment.H_ALIGN_FILL)
    slot.set_padding(unreal.Margin(0, 0, 0, 0))
    holder.set_tool_tip_text("Click to show {} in the Content Browser.".format(package))
    holder.on_clicked.add_callable(_show_in_browser(package))
    holder.on_hovered.add_callable(_tint(holder, umg.COLOR_HOVER))
    holder.on_unhovered.add_callable(_tint(holder, umg.COLOR_CLEAR))
    keep.append(holder)
    return holder


def _name_cells(row):
    ready = row.ready
    return [
        (umg.text(row.old_name), 3.0),
        (umg.text("->", COLOR_READY if ready else umg.COLOR_DIM), 0),
        (umg.text(row.new_name or "?", COLOR_READY if ready else umg.COLOR_DIM), 3.0),
        (umg.text(row.status, umg.COLOR_TEXT if ready else umg.COLOR_DIM), 2.0),
    ]


def show_rows(rows, shown, total):
    """Default 모드 미리보기를 그린다. ui.preview_rename() 이 부른다."""
    view = _view()
    if view is None:
        return
    view.rows.clear_children()
    view.row_keep = []
    for row in rows:
        line = umg.row((umg.text(row.type_name, COLOR_TYPE), 1.0), *_name_cells(row))
        view.rows.add_child(_row_button(line, row.old_package, view.row_keep))

    ready_count = sum(1 for row in rows if row.ready)
    view.match_count.set_text("{}/{} matched".format(shown, total))
    view.status.set_text("{} assets loaded, {} will be renamed".format(len(rows), ready_count))
    view.rename_button.set_is_enabled(ready_count > 0)
    sync_fields(view)


def show_copy_rows(rows, warnings):
    """Copy Name 모드 미리보기를 그린다. ui.preview_copy() 가 부른다."""
    view = _view()
    if view is None:
        return
    settings = view.settings

    # 설정 쪽 목록이 바뀌었으면(이름 변경 뒤 · 설정 패널 · 모달 창) 리스트를 맞춘다. 이름이 바뀌었을 수 있어 항상 다시 그린다.
    view.base_list.set_items(list(settings.get_editor_property("base")))
    view.targets_list.set_items(list(settings.get_editor_property("targets")))

    view.copy_rows.clear_children()
    view.copy_row_keep = []
    for text in warnings:
        view.copy_rows.add_child(umg.text("[WARN] " + text, COLOR_WARN))
    for row in rows:
        line = umg.row((umg.text(getattr(row, "base_name", "")), 3.0), *_name_cells(row))
        view.copy_rows.add_child(_row_button(line, row.old_package, view.copy_row_keep))

    ready_count = sum(1 for row in rows if row.ready)
    if not rows and not warnings:
        view.copy_status.set_text("Load Base and Targets.")
    else:
        view.copy_status.set_text("{} pair(s), {} will be renamed".format(len(rows), ready_count))
    view.copy_button.set_is_enabled(ready_count > 0)

    for name, box in view.copy_fields.items():
        current = str(settings.get_editor_property(name))
        if str(box.get_text()) != current:
            box.set_text(current)
    case = bool(settings.get_editor_property("copy_case_sensitive"))
    if bool(view.copy_case.is_checked()) != case:
        view.copy_case.set_is_checked(case)

# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-11-20
#
# A00530 JUN_Renamer - UI.
#
# MANUEditor 의 Asset Renamer(C++ Slate 탭)를 파이썬으로 옮겼다.
# JUN_UE 는 C++ 모듈이 없는 콘텐츠 플러그인이라 Slate 위젯을 만들 수 없다. 대신
#   - 화면 = 파이썬 uclass(JUNRenamerSettings) 를 디테일 패널로 그린 것
#   - 실행 = `CallInEditor` 메타를 단 인자 없는 UFUNCTION → 디테일 패널이 버튼으로 그린다
#
# ── 창: EUW 탭 (v01.01) ──────────────────────────────────────────────────────
# v01.00 은 `EditorDialog.show_object_details_view()`(모달)로 띄워서, 창이 떠 있는 동안
# 콘텐츠 브라우저를 누를 수 없었다. v01.01 부터는 Editor Utility Widget
# `/JUNTools/A00530_jun_renamer/EUW_JUNRenamer` 를 **도킹 탭**으로 띄우고, 그 안의 `DetailsView`
# 위젯에 같은 설정 오브젝트를 `set_object()` 로 꽂는다. 탭은 모달이 아니다.
#   - EUW 는 UE 5.4 로 저장돼 있다. 5.5+ 에디터에서 다시 저장하면 5.4 에서 못 연다.
#   - EUW 를 못 찾거나 탭을 못 띄우면(헤드리스 등) 예전 모달 창(show_modal)으로 대신 연다.
#   - 계획서: Docs/Plans/A00530_JUNRenamer_EUW_Tab_Plan.md
#
# ── 세 섹션 ──────────────────────────────────────────────────────────────────
#   Assets    : 대상 에셋 불러오기 (선택 · 선택 폴더 · /Game 전체) + 경로/이름 필터   ← 원본
#   Rename    : Search/Replace · Prefix · Suffix · 네이밍 규칙 · 텍스트 정리           ← 원본
#               + Trim Front / Trim Rear 와 `-1 Front` / `-1 Rear` 버튼                ← A00330 Quick Rename
#   Copy Name : Base 이름을 Targets 로 복사 (Prefix · Suffix · Search · Replace)        ← A00330 Copy Name
#
# ── 미리보기 ──────────────────────────────────────────────────────────────────
# 탭에서는 칸 편집이 끝날 때(Enter · 포커스 이동 · 체크) `DetailsView.on_property_changed` 가 와서
# 미리보기를 저절로 다시 계산한다. 모달 대체 창에서는 이 이벤트가 없어 버튼(Preview ...)으로 계산한다.
# Rename / Copy Name 은 어느 쪽이든 **실행 직전에 항상 다시 계산**한다.
# 배열이 바뀐 것은 디테일 패널이 다음 틱에 스스로 다시 그린다(FPropertyNode::EnsureDataIsValid).

import importlib
import sys
import types

import unreal

from . import core, naming

TITLE = "JUN Renamer"

# 탭으로 띄울 Editor Utility Widget. 루트 위젯이 변수로 노출된 `DetailsView` 하나다.
EUW_PATH = "/JUNTools/A00530_jun_renamer/EUW_JUNRenamer"
EUW_DETAILS_VIEW = "DetailsView"

# ── 세션 저장소 ───────────────────────────────────────────────────────────────
# uclass · 설정 오브젝트 · 불러온 에셋 목록을 **jun_tools 밖의 모듈**에 둔다.
#   - DEV_MODE 리로드(이 툴 패키지만 비움)와 `Reload JUN Tools`(jun_tools 전체를 비움) 둘 다 살아남는다.
#   - uclass 를 다시 등록하면 탭이 붙잡고 있는 이전 인스턴스를 엔진이 재인스턴싱하며 PythonScriptPlugin
#     ensure(`PySelf->ob_type == PyType`)가 뜬다 (실측 2026-11-20). 그래서 클래스는 세션당 1 회만 만든다.
#   - 버튼 · 이벤트는 `_ui()` 로 지금 sys.modules 의 ui 모듈 함수를 부르므로 코드 수정은 리로드로 반영된다.
#     프로퍼티 · 버튼 **구성**을 바꿨을 때만 에디터 재시작이 필요하다.
_SESSION_MODULE = "_jun_tools_session"


def _session():
    module = sys.modules.get(_SESSION_MODULE)
    if module is None:
        module = types.ModuleType(_SESSION_MODULE)
        sys.modules[_SESSION_MODULE] = module
    return module.__dict__.setdefault("A00530", {
        "types": None,       # (JUNRenamerSettings, JUNRenamerMatchMode)
        "settings": None,    # 세션에 하나뿐인 설정 오브젝트 (탭과 모달 창이 같이 쓴다)
        "assets": [],        # 불러온 에셋 (unreal.AssetData)
        "callback": None,    # DetailsView.on_property_changed 에 묶는 함수 (중복 연결 방지용으로 고정)
    })


_state = _session()


def _ui():
    """현재 로드된 ui 모듈. 클래스가 이전 모듈에서 만들어졌어도 최신 함수를 부른다."""
    return importlib.import_module(__name__)


# 처음 만들 때의 기본값 (uproperty 기본값과 다른 것만)
DEFAULTS = {
    "copy_case_sensitive": True,   # A00330 Copy Name 기본값
}

# on_property_changed 로 어떤 미리보기를 다시 계산할지. 이름은 밑줄 · 대소문자를 무시하고 비교한다.
COPY_PROPERTIES = {"base", "targets", "copyprefix", "copysuffix", "copysearch", "copyreplace",
                   "copycasesensitive"}
IGNORED_PROPERTIES = {"renamepreview", "copypreview", "assetsinfo"}


def _button(category, label, tooltip):
    """CallInEditor 메타 - 인자 없는 UFUNCTION 을 디테일 뷰가 버튼으로 그린다."""
    return unreal.ufunction(meta=dict(
        CallInEditor="true", Category=category, DisplayName=label, ToolTip=tooltip))


def _prop(kind, category, label, tooltip, **extra):
    meta = dict(Category=category, DisplayName=label, ToolTip=tooltip)
    meta.update(extra)
    return unreal.uproperty(kind, meta=meta)


def _build_types():
    @unreal.uenum()
    class JUNRenamerMatchMode(unreal.EnumBase):
        ANYWHERE = unreal.uvalue(naming.MATCH_ANYWHERE, meta=dict(DisplayName="Anywhere"))
        PREFIX_ONLY = unreal.uvalue(naming.MATCH_PREFIX, meta=dict(DisplayName="Prefix Only"))
        SUFFIX_ONLY = unreal.uvalue(naming.MATCH_SUFFIX, meta=dict(DisplayName="Suffix Only"))

    A, R, C = "Assets", "Rename", "Copy Name"

    @unreal.uclass()
    class JUNRenamerSettings(unreal.Object):
        # ── Assets ────────────────────────────────────────────────────────
        assets_info = _prop(str, A, "Loaded", "How many assets are loaded. Display only.")
        use_path_filter = _prop(bool, A, "Use Path Filter",
                                "Only show assets whose path starts with Path Filter.")
        path_filter = _prop(str, A, "Path Filter", "e.g. /Game/MANU/CH/")
        name_filter = _prop(str, A, "Name Filter",
                            "Only show assets whose name, type or path contains this text "
                            "(ignores case). e.g. SK_, MT_, Character")

        # ── Rename ────────────────────────────────────────────────────────
        search = _prop(str, R, "Search", "Text to find. Literal text, not a regular expression.")
        replace = _prop(str, R, "Replace", "Text to put in its place. May be empty.")
        match_mode = _prop(JUNRenamerMatchMode, R, "Match",
                           "Anywhere = every occurrence. Prefix / Suffix Only = only at the "
                           "start / end of the name.")
        case_sensitive = _prop(bool, R, "Case Sensitive",
                               "Applies to Search, Prefix and Suffix. Off = ignore case.")
        prefix = _prop(str, R, "Prefix", "Added to the front unless the name already starts with it.")
        suffix = _prop(str, R, "Suffix", "Added to the end unless the name already ends with it.")
        trim_front = _prop(int, R, "Trim Front",
                           "Characters removed from the front of the current name. "
                           "-1 Front adds one.", ClampMin="0", UIMin="0")
        trim_rear = _prop(int, R, "Trim Rear",
                          "Characters removed from the end of the current name. "
                          "-1 Rear adds one.", ClampMin="0", UIMin="0")
        use_naming_convention = _prop(
            bool, R, "Use Naming Convention",
            "Apply the per-type rules in Config/jun_asset_rename_rules.csv. Only used when "
            "Search, Prefix, Suffix and Trim are all empty.")
        remove_spaces = _prop(bool, R, "Remove Spaces", "Remove every space.")
        collapse_double_underscores = _prop(bool, R, "Collapse Double Underscores",
                                            "Turn __ into _.")
        capitalize_words = _prop(bool, R, "Capitalize Words",
                                 "Split by _ and write each word as Xxxx.")
        rename_preview = _prop(unreal.Array(str), R, "Rename Preview",
                               "Result of Preview. Display only - editing it changes nothing.")

        # ── Copy Name ─────────────────────────────────────────────────────
        base = _prop(unreal.Array(unreal.Object), C, "Base",
                     "Names are copied from these assets, in this order. Drag to reorder.")
        targets = _prop(unreal.Array(unreal.Object), C, "Targets",
                        "These assets are renamed, in this order. Targets[i] gets Base[i]'s name.")
        copy_prefix = _prop(str, C, "Prefix", "Added in front of the copied name.")
        copy_suffix = _prop(str, C, "Suffix",
                            "Added after the copied name. Needed when a target sits in the same "
                            "folder as its base - two assets cannot share a name in one folder.")
        copy_search = _prop(str, C, "Search", "Replaced inside the Base name only (not in Prefix / Suffix).")
        copy_replace = _prop(str, C, "Replace", "Text to put in its place. May be empty.")
        copy_case_sensitive = _prop(bool, C, "Case Sensitive", "Applies to Search.")
        copy_preview = _prop(unreal.Array(str), C, "Copy Preview",
                             "Result of Preview Copy. Display only - editing it changes nothing.")

        # ── Assets 버튼 ───────────────────────────────────────────────────
        @_button(A, "Load Selected", "Load the assets selected in the Content Browser.")
        def load_selected(self):
            _ui().load_selected(self)

        @_button(A, "Load Folder", "Load every asset under the folder selected in the "
                                   "Content Browser, including sub folders.")
        def load_folder(self):
            _ui().load_folder(self)

        @_button(A, "Load All /Game", "Load every asset in the project (redirectors and levels excluded).")
        def load_all(self):
            _ui().load_all(self)

        @_button(A, "Clear", "Unload every asset from the list.")
        def clear_assets(self):
            _ui().clear_assets(self)

        # ── Rename 버튼 ───────────────────────────────────────────────────
        @_button(R, "-1 Front", "Remove one more character from the front, then preview.")
        def trim_front_one(self):
            _ui().bump_trim(self, "trim_front")

        @_button(R, "-1 Rear", "Remove one more character from the end, then preview.")
        def trim_rear_one(self):
            _ui().bump_trim(self, "trim_rear")

        @_button(R, "Reset Trim", "Set Trim Front and Trim Rear back to 0, then preview.")
        def reset_trim(self):
            _ui().reset_trim(self)

        @_button(R, "Preview", "Recalculate Rename Preview. Nothing is renamed.")
        def preview_rename(self):
            _ui().preview_rename(self)

        @_button(R, "Rename", "Rename every Ready row and save. Asks first.")
        def execute_rename(self):
            _ui().execute_rename(self)

        # ── Copy Name 버튼 ────────────────────────────────────────────────
        @_button(C, "Base <- Selection", "Replace Base with the Content Browser selection.")
        def base_from_selection(self):
            _ui().list_from_selection(self, "base")

        @_button(C, "Targets <- Selection", "Replace Targets with the Content Browser selection.")
        def targets_from_selection(self):
            _ui().list_from_selection(self, "targets")

        @_button(C, "Sort Base", "Sort Base by name.")
        def sort_base(self):
            _ui().sort_list(self, "base")

        @_button(C, "Sort Targets", "Sort Targets by name.")
        def sort_targets(self):
            _ui().sort_list(self, "targets")

        @_button(C, "Preview Copy", "Recalculate Copy Preview. Nothing is renamed.")
        def preview_copy(self):
            _ui().preview_copy(self)

        @_button(C, "Copy Name", "Rename Targets[i] to Prefix + Base[i] + Suffix and save. Asks first.")
        def execute_copy(self):
            _ui().execute_copy(self)

    return JUNRenamerSettings, JUNRenamerMatchMode


def _types():
    if _state["types"] is None:
        _state["types"] = _build_types()
    return _state["types"]


# ---------------------------------------------------------------------------
# 상태 ↔ 오브젝트
# ---------------------------------------------------------------------------

def _get(settings, name):
    return settings.get_editor_property(name)


def _set(settings, name, value):
    settings.set_editor_property(name, value)


def _to_int(value):
    return int(getattr(value, "value", value))


def _to_match_enum(value):
    enum_cls = _types()[1]
    value = int(value)
    for member_name in ("ANYWHERE", "PREFIX_ONLY", "SUFFIX_ONLY"):
        member = getattr(enum_cls, member_name)
        if _to_int(member) == value:
            return member
    return enum_cls.ANYWHERE


def _rename_options(settings):
    return naming.RenameOptions(
        search=_get(settings, "search"),
        replace=_get(settings, "replace"),
        match_mode=_to_int(_get(settings, "match_mode")),
        case_sensitive=_get(settings, "case_sensitive"),
        prefix=_get(settings, "prefix"),
        suffix=_get(settings, "suffix"),
        trim_front=_get(settings, "trim_front"),
        trim_rear=_get(settings, "trim_rear"),
        use_naming_convention=_get(settings, "use_naming_convention"),
        remove_spaces=_get(settings, "remove_spaces"),
        collapse_underscores=_get(settings, "collapse_double_underscores"),
        capitalize_words=_get(settings, "capitalize_words"),
    )


def _filters(settings):
    path = _get(settings, "path_filter") if _get(settings, "use_path_filter") else ""
    return path.strip(), _get(settings, "name_filter").strip()


def _update_info(settings, rows=None, shown=None):
    total = len(_state["assets"])
    text = "{} asset(s)".format(total)
    if rows is not None:
        ready = sum(1 for row in rows if row.ready)
        text += " | {} shown | {} will be renamed".format(shown if shown is not None else len(rows), ready)
    _set(settings, "assets_info", text)


def _confirm(message):
    """예/아니오. 헤드리스(-unattended)에서는 기본값 NO 가 즉시 돌아온다."""
    answer = unreal.EditorDialog.show_message(
        TITLE, message, unreal.AppMsgType.YES_NO, unreal.AppReturnType.NO)
    return answer == unreal.AppReturnType.YES


def _notify(message):
    unreal.EditorDialog.show_message(TITLE, message, unreal.AppMsgType.OK, unreal.AppReturnType.OK)


# ---------------------------------------------------------------------------
# Assets
# ---------------------------------------------------------------------------

def _set_assets(settings, assets, source):
    _state["assets"] = list(assets)
    core.log("{} asset(s) loaded ({}).".format(len(assets), source))
    preview_rename(settings)


def load_selected(settings):
    assets = core.selected_asset_data()
    if not assets:
        core.warn("no assets selected in the Content Browser. Select assets first.")
        return
    _set_assets(settings, assets, "Content Browser selection")


def load_folder(settings):
    folders = core.selected_folders()
    if not folders:
        core.warn("no folder selected in the Content Browser. Select a folder first.")
        return
    _set_assets(settings, core.assets_in_folders(folders), ", ".join(folders))


def load_all(settings):
    assets = core.all_project_assets()
    if len(assets) > core.LOAD_ALL_CONFIRM and not _confirm(
            "Found {} assets. Previewing them may take a while. Continue?".format(len(assets))):
        core.log("Load All cancelled.")
        return
    _set_assets(settings, assets, "/Game")


def clear_assets(settings):
    _state["assets"] = []
    _set(settings, "rename_preview", [])
    _update_info(settings)
    core.log("asset list cleared.")


# ---------------------------------------------------------------------------
# Rename
# ---------------------------------------------------------------------------

def bump_trim(settings, name):
    _set(settings, name, int(_get(settings, name)) + 1)
    preview_rename(settings)


def reset_trim(settings):
    _set(settings, "trim_front", 0)
    _set(settings, "trim_rear", 0)
    preview_rename(settings)


def preview_rename(settings):
    """미리보기를 다시 계산해 Rename Preview 에 쓴다. 반환: rows."""
    path_filter, name_filter = _filters(settings)
    rows, shown = core.rename_preview(_state["assets"], _rename_options(settings),
                                      path_filter, name_filter)
    _set(settings, "rename_preview", [row.line() for row in rows])
    _update_info(settings, rows, shown)
    if shown > len(rows):
        core.log("showing the first {} of {} assets. Use a filter to narrow the list."
                 .format(len(rows), shown))
    return rows


def _refresh_renamed(rows):
    """이름이 바뀐 에셋의 AssetData 를 새 경로 것으로 갈아 끼운다."""
    by_old = {row.old_package.lower(): row for row in rows}
    fresh = []
    registry = unreal.AssetRegistryHelpers.get_asset_registry()
    for data in _state["assets"]:
        row = by_old.get(core.package_name(data).lower())
        if row is None:
            fresh.append(data)
            continue
        found = registry.get_assets_by_package_name(row.new_package) or []
        fresh.extend(found[:1])
    _state["assets"] = fresh


def _report(renamed, failed, label):
    for row in renamed:
        core.log("{}  ->  {}".format(row.old_package, row.new_name))
    for row in failed:
        core.warn("failed: {}  ->  {}".format(row.old_package, row.new_name))
    message = "{}: {} asset(s) renamed and saved.".format(label, len(renamed))
    if failed:
        message += " {} failed - see the Output Log.".format(len(failed))
    core.log(message)
    return message


def execute_rename(settings, confirm=True):
    rows = preview_rename(settings)
    ready = [row for row in rows if row.ready]
    if not ready:
        _notify("Nothing to rename. Check Rename Preview.")
        return [], []

    if confirm and not _confirm(
            "Rename {} asset(s)?\n\nThey are renamed and saved. Assets that reference them are "
            "updated by the engine; a redirector is left only where a reference cannot be "
            "fixed (Fix Up Redirectors cleans those up).".format(len(ready))):
        core.log("Rename cancelled.")
        return [], []

    renamed, failed = core.execute(rows)
    _refresh_renamed(renamed)

    # Trim 은 다시 누르면 또 지운다 - 실행 뒤에는 0 으로 돌린다.
    _set(settings, "trim_front", 0)
    _set(settings, "trim_rear", 0)
    preview_rename(settings)
    _notify(_report(renamed, failed, "Rename"))
    return renamed, failed


# ---------------------------------------------------------------------------
# Copy Name
# ---------------------------------------------------------------------------

def list_from_selection(settings, name):
    assets = core.selected_assets()
    if not assets:
        core.warn("no assets selected in the Content Browser. Select assets first.")
        return
    _set(settings, name, assets)
    core.log("{} <- {} selected asset(s).".format(name.capitalize(), len(assets)))
    preview_copy(settings)


def sort_list(settings, name):
    items = [obj for obj in _get(settings, name)]
    items.sort(key=lambda obj: obj.get_name().lower() if obj is not None else "")
    _set(settings, name, items)
    preview_copy(settings)


def _copy_rows(settings):
    rows, warnings = core.copy_preview(
        [obj for obj in _get(settings, "base")],
        [obj for obj in _get(settings, "targets")],
        prefix=_get(settings, "copy_prefix"),
        suffix=_get(settings, "copy_suffix"),
        search=_get(settings, "copy_search"),
        replace=_get(settings, "copy_replace"),
        case_sensitive=_get(settings, "copy_case_sensitive"),
    )
    return rows, warnings


def preview_copy(settings):
    rows, warnings = _copy_rows(settings)
    lines = ["[WARN] " + text for text in warnings] + [row.line() for row in rows]
    _set(settings, "copy_preview", lines)
    for text in warnings:
        core.warn(text)
    return rows


def execute_copy(settings, confirm=True):
    rows = preview_copy(settings)
    ready = [row for row in rows if row.ready]
    if not ready:
        _notify("Nothing to rename. Check Copy Preview.")
        return [], []

    if confirm and not _confirm(
            "Rename {} target asset(s) from Base names?\n\nThis will rename them and save them."
            .format(len(ready))):
        core.log("Copy Name cancelled.")
        return [], []

    renamed, failed = core.execute(rows)
    preview_copy(settings)
    # Targets 에 같은 에셋이 Assets 목록에도 있으면 그쪽 경로도 맞춘다.
    _refresh_renamed(renamed)
    preview_rename(settings)
    _notify(_report(renamed, failed, "Copy Name"))
    return renamed, failed


# ---------------------------------------------------------------------------
# 진입점
# ---------------------------------------------------------------------------

def settings():
    """세션에 하나뿐인 설정 오브젝트. 없으면 만든다."""
    if _state["settings"] is None:
        settings_cls, _ = _types()
        obj = settings_cls()
        for name, value in DEFAULTS.items():
            _set(obj, name, value)
        _update_info(obj)
        _state["settings"] = obj
    return _state["settings"]


# 검증 스크립트 · 이전 버전과의 호환용 이름
make_settings = settings


def on_property_changed(property_name):
    """DetailsView 에서 칸 편집이 끝났을 때. 바뀐 칸에 맞는 미리보기를 다시 계산한다."""
    key = str(property_name).replace("_", "").lower()
    if key in IGNORED_PROPERTIES:
        return
    obj = settings()
    try:
        if key in COPY_PROPERTIES:
            preview_copy(obj)
        else:
            preview_rename(obj)
    except Exception as error:
        core.warn("preview failed: {}".format(error))


def _callback():
    """on_property_changed 에 묶는 함수. 세션에 하나로 고정해야 중복 연결을 막을 수 있다."""
    if _state["callback"] is None:
        def _dispatch(property_name):
            _ui().on_property_changed(property_name)
        _state["callback"] = _dispatch
    return _state["callback"]


def bind(details_view):
    """DetailsView 의 칸 편집 이벤트에 미리보기 갱신을 연결한다. 이미 연결돼 있으면 그대로."""
    delegate = details_view.get_editor_property("on_property_changed")
    callback = _callback()
    try:
        if delegate.contains_callable(callback):
            return False
    except Exception:
        pass
    delegate.add_callable(callback)
    return True


def _details_view_in_tab():
    """EUW 탭을 띄우고(이미 있으면 앞으로) 그 안의 DetailsView 를 돌려준다. 못 띄우면 None."""
    blueprint = unreal.load_asset(EUW_PATH)
    if blueprint is None:
        core.warn("{} not found - opening the dialog window instead.".format(EUW_PATH))
        return None

    subsystem = unreal.get_editor_subsystem(unreal.EditorUtilitySubsystem)
    # 같은 에셋이면 탭 ID 가 같아(`<경로>_ActiveTab`) 새 탭을 만들지 않고 기존 탭을 띄운다.
    widget = subsystem.spawn_and_register_tab(blueprint)
    if widget is None:
        widget = subsystem.find_utility_widget_from_blueprint(blueprint)
    if widget is None:
        # 커맨드렛(헤드리스)은 탭을 등록하지 않는다.
        return None

    try:
        details_view = widget.get_editor_property(EUW_DETAILS_VIEW)
    except Exception:
        details_view = None
    if details_view is None:
        core.warn("{} has no '{}' widget variable - opening the dialog window instead."
                  .format(EUW_PATH, EUW_DETAILS_VIEW))
    return details_view


def show():
    """JUN Renamer 를 도킹 탭으로 연다. 탭을 못 띄우면 모달 창으로 연다. 반환: "tab" / "modal"."""
    obj = settings()

    # 목록이 비어 있을 때만 지금 콘텐츠 브라우저 선택을 불러온다 (이미 불러온 목록은 덮지 않는다).
    if not _state["assets"] and core.selected_asset_data():
        load_selected(obj)
    else:
        preview_rename(obj)
    preview_copy(obj)

    details_view = _details_view_in_tab()
    if details_view is not None:
        details_view.set_object(obj)
        bind(details_view)
        core.log("opened. Preview updates when you finish editing a field.")
        return "tab"

    show_modal(obj)
    return "modal"


def show_modal(obj=None):
    """v01.00 의 모달 창. EUW 를 쓸 수 없을 때의 대체 경로."""
    obj = obj or settings()

    options = unreal.EditorDialogLibraryObjectDetailsViewOptions()
    options.set_editor_property("show_object_name", False)
    options.set_editor_property("allow_search", False)
    options.set_editor_property("allow_resizing", True)
    options.set_editor_property("min_width", 760)
    options.set_editor_property("min_height", 720)

    core.log("dialog window: preview recalculates when you press a button. Rename / Copy Name "
             "always recalculate first.")
    # OK / Cancel 모두 아무것도 실행하지 않는다. 입력값은 세션 오브젝트에 그대로 남는다.
    unreal.EditorDialog.show_object_details_view(TITLE, obj, options)

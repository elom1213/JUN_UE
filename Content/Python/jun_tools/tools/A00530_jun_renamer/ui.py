# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-11-20
#
# A00530 JUN_Renamer - UI.
#
# MANUEditor 의 Asset Renamer(C++ Slate 탭)를 파이썬 디테일 뷰 다이얼로그로 옮겼다.
# JUN_UE 는 C++ 모듈이 없는 콘텐츠 플러그인이라 Slate 위젯을 만들 수 없다. 대신 A00510 과 같은
# 방식 - 파이썬 uclass 를 `unreal.EditorDialog.show_object_details_view()` 로 띄우고,
# `CallInEditor` 버튼으로 창을 닫지 않고 동작을 실행한다.
#
# ── 세 섹션 ──────────────────────────────────────────────────────────────────
#   Assets    : 대상 에셋 불러오기 (선택 · 선택 폴더 · /Game 전체) + 경로/이름 필터   ← 원본
#   Rename    : Search/Replace · Prefix · Suffix · 네이밍 규칙 · 텍스트 정리           ← 원본
#               + Trim Front / Trim Rear 와 `-1 Front` / `-1 Rear` 버튼                ← A00330 Quick Rename
#   Copy Name : Base 이름을 Targets 로 복사 (Prefix · Suffix · Search · Replace)        ← A00330 Copy Name
#
# ── 모달 창의 제약과 대응 ─────────────────────────────────────────────────────
# 1) 창이 떠 있는 동안 콘텐츠 브라우저를 클릭할 수 없다(모달). 그래서
#    - 창을 열 때 콘텐츠 브라우저 선택이 있으면 바로 Assets 로 불러온다.
#    - 입력값과 목록은 창을 닫아도 남는다(_state). "Base 고르고 열기 → Base <- Selection → 닫기 →
#      Targets 고르고 열기 → Targets <- Selection → Copy Name" 순서로 쓸 수 있다.
#    - Base / Targets 는 에셋 선택 칸 배열이라 창 안에서 직접 고르고 끌어서 순서를 바꿀 수도 있다.
# 2) 값을 고치는 순간을 파이썬이 알 수 없다(PostEditChangeProperty 를 못 잡는다). 그래서
#    미리보기는 버튼(Preview / -1 Front ...)을 누를 때 다시 계산한다. Rename / Copy Name 은
#    **실행 직전에 항상 다시 계산**하므로 오래된 미리보기로 바뀌는 일은 없다.
#    배열이 바뀐 것은 디테일 뷰가 다음 틱에 스스로 다시 그린다(FPropertyNode::EnsureDataIsValid).

import importlib

import unreal

from . import core, naming

TITLE = "JUN Renamer"

# 상태(입력값 · 불러온 에셋 목록)를 DEV_MODE 리로드 뒤에도 남기기 위해 이 툴 패키지 밖에 둔다.
# jun_tools.run() 은 DEV_MODE 에서 `jun_tools.tools.A00530_jun_renamer` 만 비운다.
import jun_tools.tools as _host  # noqa: E402

_state = _host.__dict__.setdefault("_A00530_STATE", {
    "values": {},       # 프로퍼티 이름 → 값 (창을 다시 열 때 채운다)
    "assets": [],       # 불러온 에셋 (unreal.AssetData)
})

# 다이얼로그가 떠 있는 동안 설정 오브젝트가 GC 되지 않도록 붙잡아 둔다.
_ALIVE = []

# uclass / uenum 은 **에디터 세션당 한 번만** 등록한다 - 그래서 _host 에 둔다.
# DEV_MODE 리로드마다 다시 등록하면 아직 GC 되지 않은 이전 인스턴스를 엔진이 재인스턴싱하면서
# PythonScriptPlugin 의 ensure(`PySelf->ob_type == PyType`, PyWrapperObject.cpp)가 뜬다 (실측 2026-11-20).
# 버튼은 `_ui()` 로 **지금 sys.modules 에 있는 ui 모듈**의 함수를 부르므로, 리로드한 코드가 그대로 쓰인다.
# 프로퍼티 · 버튼 구성 자체를 바꿨을 때만 `Reload JUN Tools`(패키지 전체 리로드) 또는 에디터 재시작.
_TYPES_KEY = "_A00530_TYPES"


def _ui():
    """현재 로드된 ui 모듈. 클래스가 이전 모듈에서 만들어졌어도 최신 함수를 부른다."""
    return importlib.import_module(__name__)

# 저장/복원하는 프로퍼티. 미리보기 배열은 매번 다시 계산하므로 뺀다.
PERSISTENT = [
    "use_path_filter", "path_filter", "name_filter",
    "search", "replace", "match_mode", "case_sensitive", "prefix", "suffix",
    "trim_front", "trim_rear", "use_naming_convention",
    "remove_spaces", "collapse_double_underscores", "capitalize_words",
    "base", "targets", "copy_prefix", "copy_suffix", "copy_search", "copy_replace",
    "copy_case_sensitive",
]

DEFAULTS = {
    "copy_case_sensitive": True,   # A00330 Copy Name 기본값
}


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
        @_button(A, "Load Selected", "Load the assets selected in the Content Browser "
                                     "(the selection made before this window opened).")
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
    types = _host.__dict__.get(_TYPES_KEY)
    if types is None:
        types = _build_types()
        _host.__dict__[_TYPES_KEY] = types
    return types


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


def _save_state(settings):
    values = _state["values"]
    for name in PERSISTENT:
        value = _get(settings, name)
        if name in ("base", "targets"):
            value = [obj for obj in value]
        elif name == "match_mode":
            value = _to_int(value)
        values[name] = value


def _restore_state(settings):
    values = dict(DEFAULTS)
    values.update(_state["values"])
    for name, value in values.items():
        try:
            if name == "match_mode":
                value = _to_match_enum(value)
            elif name in ("base", "targets"):
                # 지운 에셋은 None 으로 남는다 - 빈 칸으로 보여 준다.
                value = [obj for obj in value]
            _set(settings, name, value)
        except Exception as error:
            core.warn("could not restore {}: {}".format(name, error))
    _update_info(settings)


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
        core.warn("no assets selected in the Content Browser. Close this window, select assets, "
                  "then open it again.")
        return
    _set_assets(settings, assets, "Content Browser selection")


def load_folder(settings):
    folders = core.selected_folders()
    if not folders:
        core.warn("no folder selected in the Content Browser. Close this window, select a folder, "
                  "then open it again.")
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
    _save_state(settings)
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
        core.warn("no assets selected in the Content Browser. Close this window, select assets, "
                  "then open it again.")
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
    _save_state(settings)
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

def make_settings():
    """상태를 채운 설정 오브젝트를 만든다 (show() 와 검증 스크립트가 함께 쓴다)."""
    settings_cls, _ = _types()
    settings = settings_cls()
    _restore_state(settings)
    return settings


def show():
    """JUN Renamer 창을 띄운다."""
    settings = make_settings()
    _ALIVE.append(settings)

    try:
        # 창이 떠 있는 동안은 콘텐츠 브라우저를 고를 수 없으니, 지금 선택을 바로 불러온다.
        if core.selected_asset_data():
            load_selected(settings)
        else:
            preview_rename(settings)
        preview_copy(settings)

        options = unreal.EditorDialogLibraryObjectDetailsViewOptions()
        options.set_editor_property("show_object_name", False)
        options.set_editor_property("allow_search", False)
        options.set_editor_property("allow_resizing", True)
        options.set_editor_property("min_width", 760)
        options.set_editor_property("min_height", 720)

        core.log("Preview recalculates when you press a button. Rename / Copy Name always "
                 "recalculate first.")
        unreal.EditorDialog.show_object_details_view(TITLE, settings, options)

        # OK / Cancel 모두 입력값은 남긴다. 실행은 창 안의 버튼으로만 한다.
        _save_state(settings)
    finally:
        _ALIVE.remove(settings)

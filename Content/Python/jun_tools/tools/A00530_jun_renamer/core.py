# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-11-20
#
# A00530 JUN_Renamer - 에셋 수집 · 미리보기 · 이름 변경 (unreal 의존).
#
# 이름 규칙 자체는 naming.py / convention.py 가 갖고 있고, 여기서는
#   1) 에셋 목록을 모은다      (콘텐츠 브라우저 선택 / 선택 폴더 / /Game 전체)
#   2) 행마다 새 이름과 상태를 계산한다 (미리보기 - 아무것도 바꾸지 않는다)
#   3) 준비된 행만 실제로 이름을 바꾸고 저장한다
# 를 한다. UI(ui.py)는 이 함수들을 부르기만 한다.
#
# 원본: MANUEditor `SMANUAssetRenamerWidget` 의 OnLoadSelectedAssets / OnLoadAllAssetsInFolder /
#       OnScanAllProjectAssets / RefreshPreview / OnExecuteRename.

import os

import unreal

from . import convention, naming

LOG_PREFIX = "[JUNTools] Renamer:"

# 미리보기 행 수 상한 (원본과 같다). 필터가 켜져 있으면 상한 없이 전부 보여 준다.
PREVIEW_LIMIT = 500

# 이보다 많이 불러오면 한 번 확인한다 (원본과 같다).
LOAD_ALL_CONFIRM = 1000

# 상태 문자열 (UI 에 그대로 나간다 - 영어)
STATUS_READY = "Ready"
STATUS_NO_CHANGE = "No change"
STATUS_TAKEN = "Name taken"
STATUS_MISSING = "Missing"

RULES_FILE = "jun_asset_rename_rules.csv"


def log(message):
    unreal.log("{} {}".format(LOG_PREFIX, message))


def warn(message):
    unreal.log_warning("{} {}".format(LOG_PREFIX, message))


# ---------------------------------------------------------------------------
# 네이밍 규칙 CSV
# ---------------------------------------------------------------------------

def rules_path():
    """<플러그인>/Config/jun_asset_rename_rules.csv

    이 파일 기준: <플러그인>/Content/Python/jun_tools/tools/A00530_jun_renamer/core.py
    """
    here = os.path.dirname(os.path.abspath(__file__))
    plugin_root = os.path.normpath(os.path.join(here, "..", "..", "..", "..", ".."))
    return os.path.join(plugin_root, "Config", RULES_FILE)


_RULES_CACHE = {}


def load_rules():
    """CSV 를 읽는다. 파일 수정 시각이 바뀌면 다시 읽는다 (에디터 재시작 없이 규칙 수정)."""
    path = rules_path()
    try:
        stamp = os.path.getmtime(path)
    except OSError:
        warn("naming rules not found: {}".format(path))
        return []

    cached = _RULES_CACHE.get(path)
    if cached and cached[0] == stamp:
        return cached[1]

    rules, skipped = convention.load_rules(path)
    for line in skipped:
        if line.strip("-, "):
            warn("skipped malformed rule line: {}".format(line))
    log("{} naming rule(s) loaded from {}".format(len(rules), path))
    _RULES_CACHE[path] = (stamp, rules)
    return rules


# ---------------------------------------------------------------------------
# 에셋 레지스트리 헬퍼
# ---------------------------------------------------------------------------

def _registry():
    return unreal.AssetRegistryHelpers.get_asset_registry()


def _class_path(asset_data):
    return asset_data.get_editor_property("asset_class_path")


def class_name(asset_data):
    try:
        return str(_class_path(asset_data).get_editor_property("asset_name"))
    except Exception:
        return "Unknown"


_ANCESTORS = {}


def class_chain(asset_data):
    """에셋 클래스 이름 + 조상 클래스 이름들. 로드하지 않고 레지스트리로만 구한다."""
    name = class_name(asset_data)
    if name in _ANCESTORS:
        return _ANCESTORS[name]

    chain = [name]
    try:
        for path in _registry().get_ancestor_class_names(_class_path(asset_data)) or []:
            chain.append(str(path.get_editor_property("asset_name")))
    except Exception:
        pass
    _ANCESTORS[name] = chain
    return chain


def asset_name(asset_data):
    return str(asset_data.get_editor_property("asset_name"))


def package_name(asset_data):
    return str(asset_data.get_editor_property("package_name"))


def folder_of(asset_data):
    return str(asset_data.get_editor_property("package_path"))


def asset_exists(package):
    """패키지 경로(/Game/Foo/Bar)에 에셋이 있는지. 리디렉터도 '있음' 으로 친다."""
    try:
        return bool(_registry().get_assets_by_package_name(package, include_only_on_disk_assets=False))
    except TypeError:
        return bool(_registry().get_assets_by_package_name(package))


def normalise_content_path(path):
    """'/All/Game/Foo' 같은 콘텐츠 브라우저 표시 경로를 '/Game/Foo' 로."""
    text = str(path or "").rstrip("/")
    if text.startswith("/All/"):
        text = text[len("/All"):]
    return text


def _is_renameable(asset_data):
    """원본 OnScanAllProjectAssets 의 걸러내기: 리디렉터 · 월드(레벨)는 제외."""
    name = class_name(asset_data)
    return "Redirector" not in name and "World" not in name


# ---------------------------------------------------------------------------
# 1) 에셋 모으기
# ---------------------------------------------------------------------------

def selected_asset_data():
    """콘텐츠 브라우저에서 선택한 에셋 (AssetData 목록)."""
    try:
        return [a for a in unreal.EditorUtilityLibrary.get_selected_asset_data() or []]
    except Exception:
        return []


def selected_assets():
    """콘텐츠 브라우저에서 선택한 에셋 (UObject 목록 - 로드된다)."""
    try:
        return [a for a in unreal.EditorUtilityLibrary.get_selected_assets() or []]
    except Exception:
        return []


def selected_folders():
    try:
        folders = unreal.EditorUtilityLibrary.get_selected_folder_paths() or []
    except Exception:
        folders = []
    return [normalise_content_path(f) for f in folders if f]


def assets_in_folders(folders):
    """폴더들 아래(하위 폴더 포함)의 에셋."""
    found = []
    seen = set()
    for folder in folders:
        for data in _registry().get_assets_by_path(folder, recursive=True) or []:
            key = package_name(data)
            if key in seen or not _is_renameable(data):
                continue
            seen.add(key)
            found.append(data)
    return found


def all_project_assets(root="/Game"):
    return assets_in_folders([root])


# ---------------------------------------------------------------------------
# 2) 미리보기
# ---------------------------------------------------------------------------

class Row(object):
    """미리보기 한 행 = 이름을 바꿀 에셋 하나."""

    def __init__(self, old_name, folder, type_name, new_name, source):
        self.old_name = old_name
        self.folder = folder
        self.type_name = type_name
        self.new_name = new_name
        self.source = source        # AssetData 또는 UObject - 실행할 때 UObject 로 바꾼다
        self.status = STATUS_READY

    @property
    def ready(self):
        return self.status == STATUS_READY

    @property
    def old_package(self):
        return "{}/{}".format(self.folder, self.old_name)

    @property
    def new_package(self):
        return "{}/{}".format(self.folder, self.new_name)

    def line(self):
        """디테일 뷰 미리보기 배열에 들어가는 한 줄."""
        return "{:<10} {}  ->  {}    ({}, {})".format(
            self.status, self.old_name, self.new_name or "?", self.type_name, self.folder)

    def asset_object(self):
        if isinstance(self.source, unreal.AssetData):
            return self.source.get_asset()
        return self.source


def judge(rows):
    """행마다 상태를 매긴다 (제자리에서 고친다).

    - 이름이 그대로        → No change
    - 쓸 수 없는 이름      → invalid ... / empty name
    - 이미 그 이름의 에셋이 있다 → Name taken
        단, 그 에셋이 이번에 다른 이름으로 비켜 줄 행이면 괜찮다.
        같은 폴더에서 두 행이 같은 새 이름을 원하면 두 번째부터 Name taken.
    언리얼 패키지 이름은 대소문자를 가리지 않으므로 비교도 소문자로 한다.
    """
    for row in rows:
        reason = naming.invalid_reason(row.new_name)
        if row.new_name == row.old_name:
            row.status = STATUS_NO_CHANGE
        elif reason:
            row.status = reason
        else:
            row.status = STATUS_READY

    leaving = {row.old_package.lower() for row in rows if row.ready}
    claimed = set()
    for row in rows:
        if not row.ready:
            continue
        target = row.new_package.lower()
        case_only = target == row.old_package.lower()
        if target in claimed:
            row.status = STATUS_TAKEN
        elif not case_only and target not in leaving and asset_exists(row.new_package):
            row.status = STATUS_TAKEN
        else:
            claimed.add(target)
    return rows


def filter_assets(assets, path_filter="", name_filter=""):
    """원본 RefreshPreview 의 필터: 경로는 앞부분 일치, 이름은 이름 · 타입 · 경로 어디든.

    둘 다 대소문자 무시 (원본 FString::StartsWith / Contains 의 기본값).
    """
    path_filter = normalise_content_path(path_filter).lower() if path_filter else ""
    name_filter = (name_filter or "").lower()
    result = []
    for data in assets:
        package = package_name(data).lower()
        if path_filter and not package.startswith(path_filter):
            continue
        if name_filter:
            if (name_filter not in asset_name(data).lower()
                    and name_filter not in class_name(data).lower()
                    and name_filter not in package):
                continue
        result.append(data)
    return result


def rename_preview(assets, options, path_filter="", name_filter=""):
    """Rename 섹션 미리보기. 반환: (rows, total_after_filter)."""
    filtered = filter_assets(assets, path_filter, name_filter)
    limited = filtered
    if not path_filter and not name_filter and len(filtered) > PREVIEW_LIMIT:
        limited = filtered[:PREVIEW_LIMIT]

    rules = load_rules() if (options.use_naming_convention
                              and not options.has_manual_operation()) else []

    rows = []
    for data in limited:
        old = asset_name(data)
        chain = class_chain(data)

        def _convention(name, _chain=chain):
            return convention.apply(name, _chain, rules)

        new = naming.build_new_name(old, options, _convention)
        rows.append(Row(old, folder_of(data), chain[0], new, data))

    return judge(rows), len(filtered)


def copy_preview(bases, targets, prefix="", suffix="", search="", replace="",
                 case_sensitive=True):
    """Copy Name 미리보기. Targets[i] ← Prefix + Base[i] 이름(치환) + Suffix.

    반환: (rows, warnings)
    """
    warnings = []
    if len(bases) != len(targets):
        warnings.append("Base ({}) and Targets ({}) counts differ; only the first {} pair(s) "
                        "are used.".format(len(bases), len(targets), min(len(bases), len(targets))))

    rows = []
    for index, (base, target) in enumerate(zip(bases, targets)):
        if base is None or target is None:
            warnings.append("Pair {} has an empty slot; skipped.".format(index))
            continue
        new = naming.copy_name(base.get_name(), prefix, suffix, search, replace, case_sensitive)
        folder = target.get_outermost().get_name().rsplit("/", 1)[0]
        row = Row(target.get_name(), folder, target.get_class().get_name(), new, target)
        rows.append(row)

    return judge(rows), warnings


# ---------------------------------------------------------------------------
# 3) 실행
# ---------------------------------------------------------------------------

def execute(rows, save=True):
    """Ready 행만 이름을 바꾸고 저장한다. 반환: (renamed_rows, failed_rows).

    - AssetTools.rename_assets 한 번에 묶어서 보낸다 (원본과 같다). 엔진(FAssetRenameManager)이
      참조하는 에셋을 불러와 경로를 고치고 저장까지 한다 - 헤드리스 실측(2026-11-20): MI 의 부모
      머티리얼 이름을 바꾸면 MI 가 새 이름을 가리키고, 더티 패키지 0 개, 옛 자리 리디렉터 없음.
      고칠 수 없는 참조(체크아웃 실패 등)가 있을 때만 리디렉터가 남는다 - 그때는 콘텐츠 브라우저
      폴더 우클릭 > Fix Up Redirectors. (FixupReferencers 는 파이썬에 노출돼 있지 않다.)
    - 저장은 **이번에 바꾼 에셋과 그 리디렉터만** 한다. 원본은 SaveDirtyPackages 로 에디터의
      더티 패키지를 전부 저장했는데, 이름 변경과 무관한 작업까지 저장되는 것을 막았다.
    """
    ready = [row for row in rows if row.ready]
    if not ready:
        return [], []

    requests = []
    for row in ready:
        asset = row.asset_object()
        if asset is None:
            row.status = STATUS_MISSING
            continue
        data = unreal.AssetRenameData()
        data.set_editor_property("asset", asset)
        data.set_editor_property("new_package_path", row.folder)
        data.set_editor_property("new_name", row.new_name)
        requests.append((row, data))

    if not requests:
        return [], ready

    tools = unreal.AssetToolsHelpers.get_asset_tools()
    tools.rename_assets([data for _, data in requests])

    renamed, failed = [], []
    for row, _ in requests:
        if asset_exists(row.new_package):
            renamed.append(row)
        else:
            failed.append(row)

    if save:
        for row in renamed:
            _save(row.new_package)
            # 참조가 있던 에셋은 옛 자리에 리디렉터가 생긴다. 저장해 두지 않으면 디스크에
            # 옛 .uasset 이 그대로 남아 다음 실행 때 같은 에셋이 둘이 된다.
            if row.old_package.lower() != row.new_package.lower() and asset_exists(row.old_package):
                _save(row.old_package)

    return renamed, failed


def _save(package):
    try:
        unreal.EditorAssetLibrary.save_asset(package, only_if_is_dirty=False)
    except Exception as error:
        warn("could not save {}: {}".format(package, error))

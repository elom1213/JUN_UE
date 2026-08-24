# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-24
#
# A00520 - 기존 씬 구조 검사. **아무것도 쓰지 않는다.**
#
# 이 모드의 1차 목적은 실존하는 사고를 잡는 것이다. 조사 단계에서 발견된 것:
#   Teaser/CT01/S02 폴더 안의 마스터 이름이 `MSEQ_MANU_PreDebut_CT01_S01`
#   → `TSR` 누락 + 씬 번호가 S01 로 오기. 같은 폴더의 SSEQ 7개도 전부 `_S01_`.
#
# stem 은 사용자가 정하는 값이므로(계획서 §5.2) **정답 stem 을 강요하지 않는다.**
# 대신 "이 씬 안에서 stem 이 하나로 일관된가"를 본다. 그것만으로 위 사고가 잡힌다.

import os

import unreal

from . import naming
from . import spec as spec_module

ERROR = "ERROR"
WARNING = "WARNING"
INFO = "INFO"

PREFIX_MASTER = "MSEQ"
PREFIX_CUT = "CSEQ"
PREFIX_SUB = "SSEQ"


class Issue(object):
    def __init__(self, severity, category, target, message):
        self.severity = severity
        self.category = category
        self.target = target
        self.message = message

    def as_line(self):
        return "{:<7} {:<18} {}  --  {}".format(
            self.severity, self.category, self.target, self.message
        )

    def as_row(self):
        return [self.severity, self.category, self.target, self.message]


class ValidateReport(object):
    def __init__(self, scene_path, scene_token):
        self.scene_path = scene_path
        self.scene_token = scene_token
        self.issues = []
        self.stems = {}          # stem -> [에셋 이름]
        self.cut_tokens = []

    def add(self, severity, category, target, message):
        self.issues.append(Issue(severity, category, target, message))

    def count(self, severity):
        return len([issue for issue in self.issues if issue.severity == severity])

    def summary_line(self):
        return "{} errors, {} warnings, {} notes".format(
            self.count(ERROR), self.count(WARNING), self.count(INFO)
        )


# ---------------------------------------------------------------------------

def _package_paths(directory_path, recursive):
    """디렉토리 아래 에셋의 패키지 경로 목록. '/Game/A/B.B' → '/Game/A/B'."""
    try:
        listed = unreal.EditorAssetLibrary.list_assets(
            directory_path, recursive=recursive, include_folder=False
        )
    except Exception:
        return []

    paths = []
    for entry in listed or []:
        paths.append(entry.split(".")[0])
    return sorted(set(paths))


def _name_of(package_path):
    return package_path.rsplit("/", 1)[-1]


def _child_directories(directory_path):
    try:
        listed = unreal.EditorAssetLibrary.list_assets(
            directory_path, recursive=False, include_folder=True
        )
    except Exception:
        return []

    directories = []
    for entry in listed or []:
        if entry.endswith("/"):
            directories.append(entry.rstrip("/"))
    return sorted(set(directories))


def _linked_child_names(sequence):
    """이 시퀀스가 서브/샷으로 물고 있는 자식 시퀀스 이름 집합."""
    from . import compat

    names = set()
    for track in compat.get_sequence_tracks(sequence):
        for section in compat.get_track_sections(track):
            child = compat.get_section_sequence(section)
            if child is None:
                continue
            try:
                names.add(child.get_name())
            except Exception:
                continue
    return names


def _load_sequence(package_path):
    try:
        asset = unreal.EditorAssetLibrary.load_asset(package_path)
        return asset if isinstance(asset, unreal.LevelSequence) else None
    except Exception:
        return None


def _match_sub_type(asset_name, sub_types):
    """이름 끝의 `_<TYPE>` 을 알려진 7종에서 찾는다. 긴 것부터 본다."""
    for sub_type in sorted(sub_types, key=len, reverse=True):
        if asset_name.endswith("_" + sub_type):
            return sub_type
    return None


# ---------------------------------------------------------------------------

def validate_scene(scene_path, config):
    """씬 폴더 하나를 SOP 규격과 대조한다. 쓰기 없음."""
    scene_path = scene_path.rstrip("/")
    scene_token = _name_of(scene_path)
    report = ValidateReport(scene_path, scene_token)

    sub_types = spec_module.sub_type_keys(config)
    folders = config["folders"]
    subsequence_folder = folders["scene_sub"]

    if not unreal.EditorAssetLibrary.does_directory_exist(scene_path):
        report.add(ERROR, "path", scene_path, "Directory does not exist.")
        return report

    def remember_stem(stem, asset_name):
        report.stems.setdefault(stem, []).append(asset_name)

    # --- 마스터 -------------------------------------------------------------
    root_assets = _package_paths(scene_path, recursive=False)
    masters = [path for path in root_assets if _name_of(path).startswith(PREFIX_MASTER + "_")]

    if not masters:
        report.add(ERROR, "master", scene_path, "No MSEQ master sequence in the scene folder.")
    elif len(masters) > 1:
        report.add(
            WARNING,
            "master",
            scene_path,
            "{} master sequences in one scene folder: {}".format(
                len(masters), ", ".join(_name_of(path) for path in masters)
            ),
        )

    # 마스터가 여러 개면 그 전부를 본다. 첫 번째만 보면 "다른 마스터에는 물려 있는" 컷을
    # 미결선으로 오보한다.
    master_sequences = []
    for path in masters:
        asset_name = _name_of(path)
        stem = naming.parse_stem(asset_name, PREFIX_MASTER, [scene_token])
        if stem is None:
            report.add(
                ERROR,
                "scene-token",
                asset_name,
                "Name does not end with '_{}' - it does not match the folder it lives in.".format(
                    scene_token
                ),
            )
        else:
            remember_stem(stem, asset_name)

        loaded = _load_sequence(path)
        if loaded is not None:
            master_sequences.append(loaded)

    for path in root_assets:
        asset_name = _name_of(path)
        if asset_name.startswith(PREFIX_MASTER + "_"):
            continue
        report.add(
            INFO, "leftover", asset_name, "Asset in the scene root that is not a master sequence."
        )

    # --- 씬 레벨 SSEQ --------------------------------------------------------
    scene_sub_path = naming.join_path(scene_path, subsequence_folder)
    scene_sub_names = []
    if unreal.EditorAssetLibrary.does_directory_exist(scene_sub_path):
        for path in _package_paths(scene_sub_path, recursive=False):
            asset_name = _name_of(path)
            scene_sub_names.append(asset_name)

            sub_type = _match_sub_type(asset_name, sub_types)
            if sub_type is None:
                report.add(
                    WARNING, "sub-type", asset_name, "Does not end with one of the 7 SOP sub types."
                )
                continue

            stem = naming.parse_stem(asset_name, PREFIX_SUB, [scene_token, sub_type])
            if stem is None:
                report.add(
                    ERROR,
                    "scene-token",
                    asset_name,
                    "Name does not contain '_{}_{}' - wrong scene number or prefix.".format(
                        scene_token, sub_type
                    ),
                )
            else:
                remember_stem(stem, asset_name)

        present = {
            _match_sub_type(name, sub_types) for name in scene_sub_names
        }
        for sub_type in sub_types:
            if sub_type not in present:
                report.add(
                    WARNING, "missing-sub", scene_sub_path, "Scene subsequence '{}' is missing.".format(sub_type)
                )
    else:
        report.add(WARNING, "missing-sub", scene_path, "No '{}' folder at scene level.".format(subsequence_folder))

    # --- 컷 -----------------------------------------------------------------
    master_children = set()
    for sequence in master_sequences:
        master_children |= _linked_child_names(sequence)

    for directory in _child_directories(scene_path):
        cut_token = _name_of(directory)
        if cut_token in (subsequence_folder, folders["map"], folders["animation"], folders["vfx"]):
            continue
        report.cut_tokens.append(cut_token)

        cut_assets = _package_paths(directory, recursive=False)
        cut_sequences = [
            path for path in cut_assets if _name_of(path).startswith(PREFIX_CUT + "_")
        ]

        if not cut_sequences:
            report.add(WARNING, "missing-cut", directory, "No CSEQ cut sequence in this cut folder.")
            continue

        cut_sequence = _load_sequence(cut_sequences[0])
        cut_sequence_name = _name_of(cut_sequences[0])

        stem = naming.parse_stem(cut_sequence_name, PREFIX_CUT, [scene_token, cut_token])
        if stem is None:
            report.add(
                ERROR,
                "scene-token",
                cut_sequence_name,
                "Name does not end with '_{}_{}' - wrong scene number or cut number.".format(
                    scene_token, cut_token
                ),
            )
        else:
            remember_stem(stem, cut_sequence_name)

        if master_sequences and cut_sequence_name not in master_children:
            report.add(
                ERROR,
                "not-linked",
                cut_sequence_name,
                "Exists on disk but is not placed in the master sequence.",
            )

        # 컷 서브
        cut_sub_path = naming.join_path(directory, folders["cut_sub"])
        cut_sub_names = []
        if unreal.EditorAssetLibrary.does_directory_exist(cut_sub_path):
            for path in _package_paths(cut_sub_path, recursive=False):
                asset_name = _name_of(path)
                cut_sub_names.append(asset_name)

                sub_type = _match_sub_type(asset_name, sub_types)
                if sub_type is None:
                    report.add(
                        WARNING, "sub-type", asset_name, "Does not end with one of the 7 SOP sub types."
                    )
                    continue

                sub_stem = naming.parse_stem(
                    asset_name, PREFIX_SUB, [scene_token, cut_token, sub_type]
                )
                if sub_stem is None:
                    report.add(
                        ERROR,
                        "scene-token",
                        asset_name,
                        "Name does not contain '_{}_{}_{}'.".format(scene_token, cut_token, sub_type),
                    )
                else:
                    remember_stem(sub_stem, asset_name)

            present = {_match_sub_type(name, sub_types) for name in cut_sub_names}
            for sub_type in sub_types:
                if sub_type not in present:
                    report.add(
                        WARNING,
                        "missing-sub",
                        cut_sub_path,
                        "Cut subsequence '{}' is missing.".format(sub_type),
                    )

            if cut_sequence is not None:
                linked = _linked_child_names(cut_sequence)
                for asset_name in cut_sub_names:
                    if asset_name not in linked:
                        report.add(
                            ERROR,
                            "not-linked",
                            asset_name,
                            "Exists on disk but is not placed in {}.".format(cut_sequence_name),
                        )
        else:
            report.add(
                WARNING, "missing-sub", directory, "No '{}' folder in this cut.".format(folders["cut_sub"])
            )

    # --- stem 일관성 (핵심 검사) ----------------------------------------------
    if len(report.stems) > 1:
        ordered = sorted(report.stems.items(), key=lambda pair: len(pair[1]), reverse=True)
        majority = ordered[0][0]
        report.add(
            ERROR,
            "stem-mismatch",
            scene_path,
            "{} different name stems in one scene. Majority is '{}'. Others: {}".format(
                len(ordered),
                majority,
                "; ".join(
                    "'{}' ({} assets, e.g. {})".format(stem, len(names), names[0])
                    for stem, names in ordered[1:]
                ),
            ),
        )
    elif len(report.stems) == 1:
        report.add(INFO, "stem", scene_path, "Name stem is consistent: '{}'".format(
            list(report.stems.keys())[0]
        ))

    return report


# ---------------------------------------------------------------------------

def write_csv(report, directory=None):
    """리포트를 CSV 로 남긴다. 실패하면 None."""
    import csv

    try:
        target_directory = directory or os.path.join(
            unreal.Paths.project_saved_dir(), "JUNTools"
        )
        if not os.path.isdir(target_directory):
            os.makedirs(target_directory)

        file_path = os.path.join(
            target_directory, "cinematic_validate_{}.csv".format(report.scene_token)
        )
        with open(file_path, "w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(["Severity", "Category", "Target", "Message"])
            for issue in report.issues:
                writer.writerow(issue.as_row())
        return file_path
    except Exception:
        return None

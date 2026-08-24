# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-24
#
# A00520 - 설정 로드 + 입력 사양(Spec) + 검증.
#
# 설정은 코드가 아니라 데이터로 존재한다(설계 가이드 §3⑤).
# 우선순위:  <Project>/Config/jun_cinematic_sop.json  >  <Plugin>/Config/jun_cinematic_sop.json
#            > 이 파일 안의 DEFAULT_CONFIG
# 최상위 키 단위로 얕게 덮어쓴다. 프로젝트 쪽에 `sub_types` 만 넣으면 그 키만 갈린다.

import json
import os

from . import naming

CONFIG_FILE_NAME = "jun_cinematic_sop.json"

# 설정 파일이 통째로 사라져도 툴이 동작하도록 두는 최후의 기본값.
# JSON 쪽과 값이 같아야 한다 — 둘이 갈리면 JSON 이 정본이다.
DEFAULT_CONFIG = {
    "version": 2,
    "name_templates": {
        "master": "MSEQ_{stem}_{scene}",
        "cut": "CSEQ_{stem}_{scene}_{cut}",
        "scene_sub": "SSEQ_{stem}_{scene}_{type}",
        "cut_sub": "SSEQ_{stem}_{scene}_{cut}_{type}",
        "main_level": "ML_{stem}_{scene}",
        "sub_level": "SL_{stem}_{scene}_{type}",
        "camera_binding": "{stem}_{scene}_{cut}_camera",
        "shot_display": "{cut}",
    },
    "scene_format": "S{:02d}",
    "cut_format": "C{:04d}",
    "folders": {
        "scene_sub": "Subsequence",
        "cut_sub": "Subsequence",
        "map": "Map",
        "animation": "Animation",
        "vfx": "VFX",
    },
    "sub_types": [
        {"key": "ANIM", "folder_color": "#FF604F", "track_color": "#77474B"},
        {"key": "CAM", "folder_color": "#4DA1FB", "track_color": "#606E94"},
        {"key": "LGT", "folder_color": "#FFED49", "track_color": "#9C946E"},
        {"key": "VFX", "folder_color": "#FF9E3B", "track_color": "#997E6D"},
        {"key": "Sound", "folder_color": "#A14FFF", "track_color": "#745380"},
        {"key": "Media", "folder_color": "#009416", "track_color": "#6E7F5C"},
        {"key": "LayoutAdjust", "folder_color": "#00BFBA", "track_color": "#498583"},
    ],
    "camera": {
        "float_tracks": [
            {"name": "CurrentFocalLength", "path": "CurrentFocalLength"},
            {"name": "CurrentAperture", "path": "CurrentAperture"},
            {"name": "ManualFocusDistance", "path": "FocusSettings.ManualFocusDistance"},
        ]
    },
    "sequence": {"display_rate": 30, "tick_resolution": 24000, "default_cut_frames": 120},
    "content_types": {},
}


# ---------------------------------------------------------------------------
# 설정 로드
# ---------------------------------------------------------------------------

def plugin_config_path():
    """<Plugin>/Config/jun_cinematic_sop.json

    이 파일은 <Plugin>/Content/Python/jun_tools/tools/A00520_.../spec.py 에 있으므로
    플러그인 루트는 다섯 단계 위다. `unreal.Paths` 를 쓰지 않는 이유는, 이 플러그인이
    프로젝트 `Plugins/` 밖(UE_ADDITIONAL_PLUGIN_PATHS)에 있을 수 있기 때문이다.
    """
    here = os.path.dirname(os.path.abspath(__file__))
    plugin_root = os.path.abspath(os.path.join(here, "..", "..", "..", "..", ".."))
    return os.path.join(plugin_root, "Config", CONFIG_FILE_NAME)


def project_config_path():
    """<Project>/Config/jun_cinematic_sop.json. 에디터 밖이면 None."""
    try:
        import unreal
    except ImportError:
        return None

    try:
        return os.path.join(unreal.Paths.project_config_dir(), CONFIG_FILE_NAME)
    except Exception:
        return None


def _read_json(path):
    if not path or not os.path.isfile(path):
        return None
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def load_config(extra_overrides=None):
    """설정을 읽어 하나로 합친다. 파일이 깨져 있으면 예외를 올린다(조용히 넘어가지 않는다)."""
    merged = json.loads(json.dumps(DEFAULT_CONFIG))  # 깊은 복사

    for path in (plugin_config_path(), project_config_path()):
        data = None
        try:
            data = _read_json(path)
        except Exception as error:
            raise RuntimeError("Failed to read config '{}': {}".format(path, error))
        if not data:
            continue
        for key, value in data.items():
            if key.startswith("_"):
                continue
            merged[key] = value

    if extra_overrides:
        merged.update(extra_overrides)

    return merged


def sub_type_keys(config):
    return [entry["key"] for entry in config["sub_types"]]


def sub_type_entry(config, key):
    for entry in config["sub_types"]:
        if entry["key"] == key:
            return entry
    return None


# ---------------------------------------------------------------------------
# 사양
# ---------------------------------------------------------------------------

class CutSpec(object):
    """컷 하나. 마스터 타임라인에서의 위치(start_frame)까지 여기서 확정한다."""

    def __init__(self, number, name, start_frame, duration_frames):
        self.number = int(number)
        self.name = name                      # 'C0010'
        self.start_frame = int(start_frame)   # 마스터 타임라인 기준
        self.duration_frames = int(duration_frames)

    @property
    def end_frame(self):
        return self.start_frame + self.duration_frames

    def __repr__(self):
        return "CutSpec({} @{}+{})".format(self.name, self.start_frame, self.duration_frames)


class SceneSpec(object):
    """빌드 한 번의 입력 전체."""

    def __init__(
        self,
        root_path,
        stem,
        scene_number,
        cuts,
        display_rate=30,
        tick_resolution=24000,
        make_scene_subs=True,
        make_cut_subs=True,
        make_camera_rig=True,
        apply_colors=True,
        make_side_folders=True,
    ):
        self.root_path = (root_path or "").rstrip("/")
        self.stem = (stem or "")
        self.scene_number = int(scene_number)
        self.cuts = list(cuts)
        self.display_rate = int(display_rate)
        self.tick_resolution = int(tick_resolution)
        self.make_scene_subs = bool(make_scene_subs)
        self.make_cut_subs = bool(make_cut_subs)
        self.make_camera_rig = bool(make_camera_rig)
        self.apply_colors = bool(apply_colors)
        self.make_side_folders = bool(make_side_folders)

    @property
    def total_frames(self):
        return sum(cut.duration_frames for cut in self.cuts)

    def __repr__(self):
        return "SceneSpec({} / {} / S{:02d} / {} cuts)".format(
            self.root_path, self.stem, self.scene_number, len(self.cuts)
        )


def make_uniform_cuts(config, start_number, count, step, frames_per_cut):
    """균등 컷 목록. 시작번호 10 / 개수 3 / 증분 10 → C0010, C0020, C0030.

    start_frame 은 컷을 시간축에 이어 붙인 누적 오프셋이다(프로토타입 D6 수정).
    """
    cuts = []
    offset = 0
    for index in range(int(count)):
        number = int(start_number) + index * int(step)
        cuts.append(
            CutSpec(
                number=number,
                name=naming.format_cut(number, config.get("cut_format", "C{:04d}")),
                start_frame=offset,
                duration_frames=int(frames_per_cut),
            )
        )
        offset += int(frames_per_cut)
    return cuts


def make_cuts_from_list(config, entries):
    """[{'number': 10, 'frames': 96}, ...] → CutSpec 목록. Phase 5 의 JSON 컷리스트 입력용."""
    cuts = []
    offset = 0
    default_frames = config["sequence"]["default_cut_frames"]
    for entry in entries:
        number = int(entry["number"])
        frames = int(entry.get("frames", default_frames))
        cuts.append(
            CutSpec(
                number=number,
                name=naming.format_cut(number, config.get("cut_format", "C{:04d}")),
                start_frame=offset,
                duration_frames=frames,
            )
        )
        offset += frames
    return cuts


# ---------------------------------------------------------------------------
# 검증
# ---------------------------------------------------------------------------

def validate_spec(scene_spec, config):
    """문제 목록을 돌려준다. 비어 있으면 통과."""
    problems = []

    path_problem = naming.validate_package_path(scene_spec.root_path)
    if path_problem:
        problems.append(path_problem)

    stem_problem = naming.validate_stem(scene_spec.stem)
    if stem_problem:
        problems.append(stem_problem)

    if scene_spec.scene_number < 0:
        problems.append("Scene Number must be zero or greater.")

    if not scene_spec.cuts:
        problems.append("Cut Count must be at least 1.")

    if scene_spec.display_rate <= 0:
        problems.append("Display Rate must be greater than zero.")

    if scene_spec.tick_resolution <= 0:
        problems.append("Tick Resolution must be greater than zero.")

    seen = set()
    for cut in scene_spec.cuts:
        if cut.duration_frames <= 0:
            problems.append("Cut {} has a duration of {} frames.".format(cut.name, cut.duration_frames))
        if cut.name in seen:
            problems.append("Cut name '{}' appears more than once - check Cut Step.".format(cut.name))
        seen.add(cut.name)

    if not config.get("sub_types"):
        problems.append("Config has no 'sub_types' entries.")

    # 조립이 실제로 되는지 한 번 돌려본다. 템플릿에 오타가 있으면 여기서 잡힌다.
    if not problems:
        try:
            builder = naming.NameBuilder(config, scene_spec.root_path, scene_spec.stem,
                                         scene_spec.scene_number)
            builder.master_asset_path()
            first_cut = scene_spec.cuts[0].name
            builder.cut_asset_path(first_cut)
            for key in sub_type_keys(config):
                builder.scene_sub_asset_path(key)
                builder.cut_sub_asset_path(first_cut, key)
            builder.camera_binding_name(first_cut)
        except naming.NamingError as error:
            problems.append(str(error))

    return problems

# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-24
#
# A00520 - UI.
#
# UI 는 얇게 유지한다. 여기서 하는 일은 "물어보고 core 를 부르는 것"뿐이다.
# 다이얼로그는 A00510 과 같은 방식 — 파이썬 uclass 를 만들어
# `unreal.EditorDialog.show_object_details_view()` 로 디테일 패널처럼 띄운다.
#
# ── Name Stem 이 이 UI 의 핵심이다 (계획서 §5.2 · §5.6) ─────────────────────
# 이름의 접두 부분을 코드가 정하지 않는다. 사용자가 친 문자열이 그대로 들어간다.
#   "PreDebut_TSR_CT01"        → MSEQ_PreDebut_TSR_CT01_S06
#   "MANU_PreDebut_TSR_CT01"   → MSEQ_MANU_PreDebut_TSR_CT01_S06
# 이렇게 하면 "정답 이름"을 툴이 강요하지 않으면서도, 한 번 정한 stem 이 그 씬 전체에
# 일관되게 적용된다. 실제로 발생했던 씬 내 이름 불일치 사고가 구조적으로 불가능해진다.
#
# ── 모달 디테일 뷰의 제약 ────────────────────────────────────────────────────
# 실시간 미리보기가 안 된다. 그래서 2단계로 나눈다.
#   ① 값 입력 → OK   ② Dry Run 결과를 Output Log 에 출력   ③ "만들까요?" 확인   ④ 생성

import json
import os

import unreal

from . import core
from . import spec as spec_module

TITLE = "JUN Cinematic Sequence Builder"
VALIDATE_TITLE = "JUN Cinematic Structure Validate"

DEFAULT_ROOT_PATH = "/Game"
LAST_VALUES_FILE = "a00520_last.json"

# 다이얼로그가 떠 있는 동안 설정 오브젝트가 GC 되지 않도록 붙잡아 둔다.
_ALIVE = []

# uclass 는 에디터에 등록되는 타입이라 한 번만 만들어 재사용한다.
_SETTINGS_CLASS = None


# ---------------------------------------------------------------------------
# 콘텐츠 브라우저에서 대상 경로 얻기  (프로토타입 P2 이식)
# ---------------------------------------------------------------------------

def get_root_path_from_content_browser(default_root=DEFAULT_ROOT_PATH):
    """선택된 폴더 → 현재 콘텐츠 브라우저 경로 → 기본값 순으로 찾는다."""
    utility_library = getattr(unreal, "EditorUtilityLibrary", None)
    if utility_library is None:
        return default_root

    try:
        folder_paths = utility_library.get_selected_folder_paths()
        if folder_paths:
            return _normalise_content_path(folder_paths[0], default_root)
    except Exception:
        pass

    try:
        current_path = utility_library.get_current_content_browser_path()
        if current_path:
            return _normalise_content_path(current_path, default_root)
    except Exception:
        pass

    return default_root


def _normalise_content_path(path, default_root=DEFAULT_ROOT_PATH):
    """'/All/Game/Foo' 같은 콘텐츠 브라우저 표시 경로를 '/Game/Foo' 로 되돌린다."""
    if not path:
        return default_root
    text = str(path).rstrip("/")
    if text.startswith("/All/"):
        text = text[len("/All"):]
    return text or default_root


# ---------------------------------------------------------------------------
# 마지막 입력값 기억
# ---------------------------------------------------------------------------

def _last_values_path():
    try:
        return os.path.join(unreal.Paths.project_saved_dir(), "JUNTools", LAST_VALUES_FILE)
    except Exception:
        return None


def load_last_values():
    path = _last_values_path()
    if not path or not os.path.isfile(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle) or {}
    except Exception:
        return {}


def save_last_values(values):
    path = _last_values_path()
    if not path:
        return
    try:
        directory = os.path.dirname(path)
        if not os.path.isdir(directory):
            os.makedirs(directory)
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(values, handle, indent=2)
    except Exception:
        # 기억은 편의 기능이다. 실패해도 툴 동작을 막지 않는다.
        pass


# ---------------------------------------------------------------------------
# 설정 오브젝트
# ---------------------------------------------------------------------------

def _build_settings_class():
    @unreal.uclass()
    class JUNCinematicBuilderSettings(unreal.Object):
        root_path = unreal.uproperty(
            str,
            meta=dict(
                Category="Target",
                DisplayName="Root Path",
                ToolTip="Chapter folder the scene goes under, e.g. "
                        "/Game/MANUCinematic/PreDebut/Teaser/CT01. "
                        "Picked up from the Content Browser selection.",
            ),
        )
        name_stem = unreal.uproperty(
            str,
            meta=dict(
                Category="Target",
                DisplayName="Name Stem",
                ToolTip="Free text placed between the prefix and the scene number. "
                        "MSEQ_<stem>_S06. Type it exactly as you want it - the tool never "
                        "adds or removes tokens of its own.",
            ),
        )
        scene_number = unreal.uproperty(
            int,
            meta=dict(
                Category="Target",
                DisplayName="Scene Number",
                ToolTip="6 becomes S06.",
                ClampMin="0",
            ),
        )

        cut_start = unreal.uproperty(
            int,
            meta=dict(
                Category="Cuts",
                DisplayName="Cut Start",
                ToolTip="10 becomes C0010.",
                ClampMin="0",
            ),
        )
        cut_count = unreal.uproperty(
            int,
            meta=dict(
                Category="Cuts",
                DisplayName="Cut Count",
                ToolTip="How many cuts to create.",
                ClampMin="1",
            ),
        )
        cut_step = unreal.uproperty(
            int,
            meta=dict(
                Category="Cuts",
                DisplayName="Cut Step",
                ToolTip="Gap between cut numbers. 10 gives C0010, C0020, C0030.",
                ClampMin="1",
            ),
        )
        frames_per_cut = unreal.uproperty(
            int,
            meta=dict(
                Category="Cuts",
                DisplayName="Frames Per Cut",
                ToolTip="Placeholder length for every cut. Cuts are laid end to end in the "
                        "master sequence.",
                ClampMin="1",
            ),
        )
        display_rate = unreal.uproperty(
            int,
            meta=dict(
                Category="Cuts",
                DisplayName="Display Rate (fps)",
                ClampMin="1",
            ),
        )

        create_scene_subsequences = unreal.uproperty(
            bool,
            meta=dict(
                Category="Options",
                DisplayName="Create Scene Subsequences",
                ToolTip="The 7 SOP subsequences that live at scene level.",
            ),
        )
        create_cut_subsequences = unreal.uproperty(
            bool,
            meta=dict(
                Category="Options",
                DisplayName="Create Cut Subsequences",
                ToolTip="The 7 SOP subsequences inside every cut.",
            ),
        )
        set_up_cine_camera = unreal.uproperty(
            bool,
            meta=dict(
                Category="Options",
                DisplayName="Set Up CineCamera in CAM",
                ToolTip="Add a spawnable CineCameraActor, a camera cut and the usual transform "
                        "and lens tracks to each CAM subsequence. Existing CAM subsequences are "
                        "never touched.",
            ),
        )
        apply_folder_colors = unreal.uproperty(
            bool,
            meta=dict(
                Category="Options",
                DisplayName="Apply SOP Folder Colors",
                ToolTip="Group tracks into sequencer folders and tint them with the SOP colours.",
            ),
        )
        create_side_folders = unreal.uproperty(
            bool,
            meta=dict(
                Category="Options",
                DisplayName="Create Map / Animation Folders",
            ),
        )
        dry_run_first = unreal.uproperty(
            bool,
            meta=dict(
                Category="Options",
                DisplayName="Dry Run First",
                ToolTip="List everything in the Output Log and ask for confirmation before "
                        "creating anything. Recommended.",
            ),
        )

    return JUNCinematicBuilderSettings


def _settings_class():
    global _SETTINGS_CLASS
    if _SETTINGS_CLASS is None:
        _SETTINGS_CLASS = _build_settings_class()
    return _SETTINGS_CLASS


def _make_settings(config):
    """기본값을 채운 설정 오브젝트."""
    sequence_settings = config["sequence"]
    remembered = load_last_values()

    settings = _settings_class()()

    settings.set_editor_property(
        "root_path", remembered.get("root_path") or get_root_path_from_content_browser()
    )
    # 콘텐츠 브라우저에서 다른 폴더를 골랐다면 그쪽을 우선한다.
    browser_path = get_root_path_from_content_browser()
    if browser_path and browser_path != DEFAULT_ROOT_PATH:
        settings.set_editor_property("root_path", browser_path)

    settings.set_editor_property("name_stem", remembered.get("name_stem", ""))
    settings.set_editor_property("scene_number", int(remembered.get("scene_number", 1)))
    settings.set_editor_property("cut_start", int(remembered.get("cut_start", 10)))
    settings.set_editor_property("cut_count", int(remembered.get("cut_count", 1)))
    settings.set_editor_property("cut_step", int(remembered.get("cut_step", 10)))
    settings.set_editor_property(
        "frames_per_cut",
        int(remembered.get("frames_per_cut", sequence_settings["default_cut_frames"])),
    )
    settings.set_editor_property(
        "display_rate", int(remembered.get("display_rate", sequence_settings["display_rate"]))
    )

    settings.set_editor_property(
        "create_scene_subsequences", bool(remembered.get("create_scene_subsequences", True))
    )
    settings.set_editor_property(
        "create_cut_subsequences", bool(remembered.get("create_cut_subsequences", True))
    )
    settings.set_editor_property(
        "set_up_cine_camera", bool(remembered.get("set_up_cine_camera", True))
    )
    settings.set_editor_property(
        "apply_folder_colors", bool(remembered.get("apply_folder_colors", True))
    )
    settings.set_editor_property(
        "create_side_folders", bool(remembered.get("create_side_folders", True))
    )
    settings.set_editor_property("dry_run_first", bool(remembered.get("dry_run_first", True)))

    return settings


def _read_settings(settings):
    return {
        "root_path": str(settings.get_editor_property("root_path")).strip(),
        "name_stem": str(settings.get_editor_property("name_stem")).strip(),
        "scene_number": int(settings.get_editor_property("scene_number")),
        "cut_start": int(settings.get_editor_property("cut_start")),
        "cut_count": int(settings.get_editor_property("cut_count")),
        "cut_step": int(settings.get_editor_property("cut_step")),
        "frames_per_cut": int(settings.get_editor_property("frames_per_cut")),
        "display_rate": int(settings.get_editor_property("display_rate")),
        "create_scene_subsequences": bool(settings.get_editor_property("create_scene_subsequences")),
        "create_cut_subsequences": bool(settings.get_editor_property("create_cut_subsequences")),
        "set_up_cine_camera": bool(settings.get_editor_property("set_up_cine_camera")),
        "apply_folder_colors": bool(settings.get_editor_property("apply_folder_colors")),
        "create_side_folders": bool(settings.get_editor_property("create_side_folders")),
        "dry_run_first": bool(settings.get_editor_property("dry_run_first")),
    }


def _scene_spec_from(values, config):
    sequence_settings = config["sequence"]
    return spec_module.SceneSpec(
        root_path=values["root_path"],
        stem=values["name_stem"],
        scene_number=values["scene_number"],
        cuts=spec_module.make_uniform_cuts(
            config,
            values["cut_start"],
            values["cut_count"],
            values["cut_step"],
            values["frames_per_cut"],
        ),
        display_rate=values["display_rate"],
        tick_resolution=sequence_settings["tick_resolution"],
        make_scene_subs=values["create_scene_subsequences"],
        make_cut_subs=values["create_cut_subsequences"],
        make_camera_rig=values["set_up_cine_camera"],
        apply_colors=values["apply_folder_colors"],
        make_side_folders=values["create_side_folders"],
    )


# ---------------------------------------------------------------------------
# 진입점
# ---------------------------------------------------------------------------

def show():
    """빌더 다이얼로그를 띄운다."""
    config = spec_module.load_config()

    settings = _make_settings(config)
    _ALIVE.append(settings)

    try:
        dialog_options = unreal.EditorDialogLibraryObjectDetailsViewOptions()
        dialog_options.set_editor_property("show_object_name", False)
        dialog_options.set_editor_property("allow_search", False)
        dialog_options.set_editor_property("allow_resizing", True)
        dialog_options.set_editor_property("min_width", 560)

        accepted = unreal.EditorDialog.show_object_details_view(TITLE, settings, dialog_options)
        if not accepted:
            unreal.log("[JUNTools] Cinematic Sequence Builder cancelled.")
            return None

        values = _read_settings(settings)
    finally:
        if settings in _ALIVE:
            _ALIVE.remove(settings)

    save_last_values(values)

    scene_spec = _scene_spec_from(values, config)

    problems = spec_module.validate_spec(scene_spec, config)
    if problems:
        for problem in problems:
            unreal.log_error("[JUNTools] {}".format(problem))
        unreal.EditorDialog.show_message(
            TITLE,
            "The settings are not valid:\n\n- " + "\n- ".join(problems),
            unreal.AppMsgType.OK,
            unreal.AppReturnType.OK,
        )
        return None

    # ② Dry Run — 무엇이 만들어질지 로그에 전부 찍는다
    build_plan = core.preview(scene_spec, config)
    if build_plan is None:
        return None

    if build_plan.conflicts:
        unreal.EditorDialog.show_message(
            TITLE,
            "{} name conflicts were found - see the Output Log.\n"
            "Nothing was created.".format(len(build_plan.conflicts)),
            unreal.AppMsgType.OK,
            unreal.AppReturnType.OK,
        )
        return build_plan

    new_assets = len(build_plan.sequence_creates)
    if new_assets == 0:
        unreal.EditorDialog.show_message(
            TITLE,
            "Everything already exists. Nothing to create.\n"
            "Missing links and folders can still be repaired - see the Output Log.",
            unreal.AppMsgType.OK,
            unreal.AppReturnType.OK,
        )

    # ③ 확인
    if values["dry_run_first"]:
        confirmed = unreal.EditorDialog.show_message(
            TITLE,
            "Create {} sequence assets under\n{}\n\n"
            "Names start with '{}'. The full list is in the Output Log.".format(
                new_assets, scene_spec.root_path, build_plan.scene_spec.stem
            ),
            unreal.AppMsgType.OK_CANCEL,
            unreal.AppReturnType.CANCEL,  # -unattended 로 돌 때의 기본값
        )
        if confirmed != unreal.AppReturnType.OK:
            unreal.log("[JUNTools] Cinematic Sequence Builder cancelled before creating anything.")
            return build_plan

    # ④ 생성
    return core.build(scene_spec, dry_run=False, config=config, build_plan=build_plan)


def validate_selected():
    """콘텐츠 브라우저에서 선택한 씬 폴더를 검사한다. 아무것도 만들지 않는다."""
    scene_path = get_root_path_from_content_browser(default_root="")

    if not scene_path:
        unreal.EditorDialog.show_message(
            VALIDATE_TITLE,
            "Select a scene folder (for example .../CT01/S02) in the Content Browser first.",
            unreal.AppMsgType.OK,
            unreal.AppReturnType.OK,
        )
        return None

    report = core.validate(scene_path)

    unreal.EditorDialog.show_message(
        VALIDATE_TITLE,
        "{}\n\n{}\n\nDetails are in the Output Log.".format(report.scene_path, report.summary_line()),
        unreal.AppMsgType.OK,
        unreal.AppReturnType.OK,
    )
    return report

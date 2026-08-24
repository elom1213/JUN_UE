# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-24
#
# A00520 - 진입점.
#
# 여기 있는 함수는 UI 없이도 그대로 부를 수 있어야 한다(설계 가이드 §4).
# 파이썬 콘솔 / 커맨드렛 / 배치에서:
#
#   from jun_tools.tools.A00520_cinematic_sequence_builder import core
#   core.build_uniform(
#       root_path="/Game/MANUCinematic/PreDebut/Teaser/CT01",
#       stem="PreDebut_TSR_CT01",
#       scene_number=6,
#       cut_start=10, cut_count=13, cut_step=10, frames_per_cut=120,
#       dry_run=True,
#   )

import unreal

from . import build as build_module
from . import plan as plan_module
from . import spec as spec_module
from . import validate as validate_module

LOG_PREFIX = "[JUNTools]"


def _log(message):
    unreal.log("{} {}".format(LOG_PREFIX, message))


def _log_warning(message):
    unreal.log_warning("{} {}".format(LOG_PREFIX, message))


def _log_error(message):
    unreal.log_error("{} {}".format(LOG_PREFIX, message))


def _log_block(title, lines):
    _log("--- {} ---".format(title))
    for line in lines:
        _log("  {}".format(line))
    _log("-" * (len(title) + 8))


# ---------------------------------------------------------------------------
# 계획 / 미리보기
# ---------------------------------------------------------------------------

def preview(scene_spec, config=None):
    """생성 계획을 세워 돌려준다. 아무것도 만들지 않는다."""
    config = config or spec_module.load_config()

    problems = spec_module.validate_spec(scene_spec, config)
    if problems:
        for problem in problems:
            _log_error(problem)
        return None

    build_plan = plan_module.build_plan(scene_spec, config)
    _log_block("Cinematic Sequence Builder - dry run", build_plan.report_lines())
    return build_plan


# ---------------------------------------------------------------------------
# 생성
# ---------------------------------------------------------------------------

def build(scene_spec, dry_run=False, config=None, build_plan=None):
    """씬 하나의 시퀀서 구조를 만든다.

    Returns: dry_run 이면 BuildPlan, 아니면 BuildResult. 입력이 잘못됐으면 None.
    """
    config = config or spec_module.load_config()

    problems = spec_module.validate_spec(scene_spec, config)
    if problems:
        for problem in problems:
            _log_error(problem)
        return None

    if build_plan is None:
        build_plan = plan_module.build_plan(scene_spec, config)

    if dry_run:
        _log_block("Cinematic Sequence Builder - dry run", build_plan.report_lines())
        return build_plan

    if build_plan.conflicts:
        _log_block(
            "Cinematic Sequence Builder - name conflicts, nothing created",
            ["{}  ({})".format(item.path, item.detail) for item in build_plan.conflicts],
        )
        return build_module.BuildResult()

    result = build_module.execute(scene_spec, config, build_plan)
    log_result(result, scene_spec)
    return result


def build_uniform(
    root_path,
    stem,
    scene_number,
    cut_start=10,
    cut_count=1,
    cut_step=10,
    frames_per_cut=None,
    display_rate=None,
    dry_run=False,
    make_scene_subs=True,
    make_cut_subs=True,
    make_camera_rig=True,
    apply_colors=True,
    make_side_folders=True,
    config=None,
):
    """균등 컷으로 SceneSpec 을 만들어 build() 를 부르는 편의 함수."""
    config = config or spec_module.load_config()
    sequence_settings = config["sequence"]

    frames = frames_per_cut if frames_per_cut is not None else sequence_settings["default_cut_frames"]
    rate = display_rate if display_rate is not None else sequence_settings["display_rate"]

    scene_spec = spec_module.SceneSpec(
        root_path=root_path,
        stem=stem,
        scene_number=scene_number,
        cuts=spec_module.make_uniform_cuts(config, cut_start, cut_count, cut_step, frames),
        display_rate=rate,
        tick_resolution=sequence_settings["tick_resolution"],
        make_scene_subs=make_scene_subs,
        make_cut_subs=make_cut_subs,
        make_camera_rig=make_camera_rig,
        apply_colors=apply_colors,
        make_side_folders=make_side_folders,
    )
    return build(scene_spec, dry_run=dry_run, config=config)


def log_result(result, scene_spec=None):
    """BuildResult 를 Output Log 에 정리해 찍는다."""
    for message in result.errors:
        _log_error(message)

    lines = []
    if scene_spec is not None:
        lines.append("Scene  : {}".format(scene_spec.root_path))
        lines.append("Stem   : '{}'".format(scene_spec.stem))
    lines.append(result.summary_line())
    if result.already_linked:
        lines.append("{} links were already in place and were left alone.".format(result.already_linked))
    _log_block("Cinematic Sequence Builder - done", lines)

    for message in result.warnings:
        _log_warning(message)

    if result.created_assets:
        # MANUCinematic 은 별도 SVN 리포다. 툴은 버전관리를 건드리지 않는다(계획서 §8).
        _log_warning(
            "{} assets created - remember to add them to SVN before committing.".format(
                len(result.created_assets)
            )
        )


# ---------------------------------------------------------------------------
# 검사
# ---------------------------------------------------------------------------

def validate(scene_path, config=None, write_report=True):
    """씬 폴더 하나를 SOP 규격과 대조한다. 아무것도 쓰지 않는다(CSV 리포트 제외)."""
    config = config or spec_module.load_config()
    report = validate_module.validate_scene(scene_path, config)

    lines = [
        "Scene : {}".format(report.scene_path),
        "Cuts  : {}".format(len(report.cut_tokens)),
        "",
    ]
    if report.issues:
        lines.extend(issue.as_line() for issue in report.issues)
    else:
        lines.append("No problems found.")
    lines.append("")
    lines.append(report.summary_line())

    _log_block("Cinematic Structure Validate", lines)

    if write_report and report.issues:
        csv_path = validate_module.write_csv(report)
        if csv_path:
            _log("Report written to {}".format(csv_path))

    return report

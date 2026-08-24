# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-24
#
# A00520 - 계획 실행.
#
# 생성 순서는 **leaf → 위**다. SSEQ → CSEQ → MSEQ.
# 참조가 아래에서 위로 흐르므로 역순이면 결선 시점에 붙일 대상이 아직 없다.
#
# 프로토타입에서 고친 것:
#   D1  생성 전 존재 확인 → 이미 있으면 만들지 않고 결선만 시도 (멱등)
#   D2  ScopedEditorTransaction 으로 묶는다
#   D4  ScopedSlowTask 로 진행률 + 취소
#   D5  save_directory(recursive) 대신 **우리가 건드린 에셋만** save_asset
#   D6  마스터의 샷은 누적 오프셋으로 순차 배치 (프로토타입은 전부 0 부터라 겹쳤다)
#   D7  마스터에 CinematicShotTrack 으로 CSEQ 를 넣는다 (프로토타입은 이 줄이 주석)

import unreal

from . import camera as camera_module
from . import compat, naming, plan as plan_module
from . import spec as spec_module

LOG_PREFIX = "[JUNTools]"


class BuildResult(object):
    def __init__(self):
        self.created_assets = []
        self.skipped_assets = []
        self.created_directories = []
        self.linked = 0
        self.already_linked = 0
        self.cameras_set_up = 0
        self.saved = []
        self.warnings = []
        self.errors = []
        self.cancelled = False

    def warn(self, message):
        if message not in self.warnings:
            self.warnings.append(message)

    def summary_line(self):
        return (
            "{} assets created, {} left untouched, {} folders, {} links, "
            "{} cameras set up, {} saved".format(
                len(self.created_assets),
                len(self.skipped_assets),
                len(self.created_directories),
                self.linked,
                self.cameras_set_up,
                len(self.saved),
            )
        )


# ---------------------------------------------------------------------------
# 에셋 · 폴더
# ---------------------------------------------------------------------------

def ensure_directory(directory_path, result):
    if unreal.EditorAssetLibrary.does_directory_exist(directory_path):
        return False
    unreal.EditorAssetLibrary.make_directory(directory_path)
    result.created_directories.append(directory_path)
    return True


def get_or_create_sequence(asset_path, result):
    """(sequence, created) 를 돌려준다. 이미 있으면 로드만 한다."""
    if unreal.EditorAssetLibrary.does_asset_exist(asset_path):
        existing = unreal.EditorAssetLibrary.load_asset(asset_path)
        if not isinstance(existing, unreal.LevelSequence):
            result.errors.append(
                "'{}' exists but is not a Level Sequence - skipped.".format(asset_path)
            )
            return None, False
        result.skipped_assets.append(asset_path)
        return existing, False

    package_path, asset_name = asset_path.rsplit("/", 1)
    ensure_directory(package_path, result)

    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    sequence = asset_tools.create_asset(
        asset_name=asset_name,
        package_path=package_path,
        asset_class=unreal.LevelSequence,
        factory=unreal.LevelSequenceFactoryNew(),
    )
    if sequence is None:
        result.errors.append("Could not create '{}'.".format(asset_path))
        return None, False

    result.created_assets.append(asset_path)
    return sequence, True


def apply_sequence_settings(sequence, scene_spec, start_frame, end_frame, result):
    if not compat.set_tick_resolution(sequence, scene_spec.tick_resolution):
        result.warn("Tick Resolution could not be set through python on this engine build.")
    if not compat.set_display_rate(sequence, scene_spec.display_rate):
        result.warn("Display Rate could not be set through python on this engine build.")
    if not compat.set_playback_range(sequence, start_frame, end_frame):
        result.warn("Playback Range could not be set through python on this engine build.")


# ---------------------------------------------------------------------------
# 결선
# ---------------------------------------------------------------------------

def _linked_sequence_paths(parent_sequence, track_class):
    """이 부모가 이미 물고 있는 자식 시퀀스 경로 집합."""
    paths = set()
    for track in compat.find_sequence_tracks(parent_sequence, track_class):
        for section in compat.get_track_sections(track):
            child = compat.get_section_sequence(section)
            if child is not None:
                try:
                    paths.add(child.get_path_name())
                except Exception:
                    continue
    return paths


def link_subsequence(parent_sequence, child_sequence, start_frame, end_frame, result,
                     display_name=None, track_color=None, folder_name=None, row_index=None):
    """부모에 자식 시퀀스를 SubTrack 하나로 붙인다. 이미 붙어 있으면 아무것도 하지 않는다.

    트랙 하나에 섹션 하나를 두는 이유: 한 SubTrack 에 7개 섹션을 넣으면 같은 시간 구간에서
    겹쳐 하나만 평가된다. 프로토타입이 루프 안에서 트랙을 새로 만든 것은 의도된 설계다.
    """
    child_path = child_sequence.get_path_name()
    if child_path in _linked_sequence_paths(parent_sequence, unreal.MovieSceneSubTrack):
        result.already_linked += 1
        return None

    track = compat.add_sequence_track(parent_sequence, unreal.MovieSceneSubTrack)
    section = track.add_section()
    section.set_sequence(child_sequence)
    compat.set_section_range(section, start_frame, end_frame)

    if row_index is not None:
        compat.set_section_row_index(section, row_index)
    if display_name:
        compat.set_track_display_name(track, display_name)
    if track_color is not None and not compat.set_track_color(track, track_color):
        result.warn("Track tint is not exposed to python on this engine build - skipped.")
    if folder_name:
        _place_in_folder(parent_sequence, track, folder_name, result)

    result.linked += 1
    return track


def _place_in_folder(sequence, track, folder_name, result):
    """트랙을 이름이 folder_name 인 최상위 폴더 아래로 옮긴다. 없으면 만든다."""
    folder = None
    for candidate in compat.get_root_folders(sequence):
        if compat.get_folder_name(candidate) == folder_name:
            folder = candidate
            break

    if folder is None:
        folder = compat.add_root_folder(sequence, folder_name)

    if folder is None:
        result.warn("Sequencer folders are not exposed to python on this engine build - skipped.")
        return None

    if not compat.add_track_to_folder(folder, track):
        result.warn("A track could not be moved into its sequencer folder - skipped.")
    return folder


def _apply_folder_color(sequence, folder_name, hex_color, result):
    for folder in compat.get_root_folders(sequence):
        if compat.get_folder_name(folder) != folder_name:
            continue
        if not compat.set_folder_color(folder, compat.color_from_hex(hex_color)):
            result.warn("Folder colours are not exposed to python on this engine build - skipped.")
        return True
    return False


def link_shots(master_sequence, shot_entries, result):
    """마스터에 CSEQ 를 샷으로 배치한다.

    shot_entries: [(sequence, start_frame, end_frame, display_name), ...]
    CinematicShotTrack 이 파이썬에 없으면 SubTrack 으로 폴백하고 경고를 남긴다(계획서 A8).
    """
    shot_track_class = getattr(unreal, "MovieSceneCinematicShotTrack", None)

    track = None
    if shot_track_class is not None:
        existing = compat.find_sequence_tracks(master_sequence, shot_track_class)
        if existing:
            track = existing[0]
        else:
            try:
                track = compat.add_sequence_track(master_sequence, shot_track_class)
            except compat.BindingUnavailable:
                track = None

    if track is None:
        result.warn(
            "MovieSceneCinematicShotTrack is not available through python on this engine build. "
            "Cuts were linked as plain sub-sequences instead - the master will not match the "
            "reference structure. Please review before rendering."
        )
        for sequence, start_frame, end_frame, display_name in shot_entries:
            link_subsequence(
                master_sequence, sequence, start_frame, end_frame, result,
                display_name=display_name,
            )
        return

    already = set()
    for section in compat.get_track_sections(track):
        child = compat.get_section_sequence(section)
        if child is not None:
            try:
                already.add(child.get_path_name())
            except Exception:
                continue

    for sequence, start_frame, end_frame, display_name in shot_entries:
        if sequence.get_path_name() in already:
            result.already_linked += 1
            continue
        section = track.add_section()
        section.set_sequence(sequence)
        compat.set_section_range(section, start_frame, end_frame)
        compat.set_shot_display_name(section, display_name)
        result.linked += 1


# ---------------------------------------------------------------------------
# 실행
# ---------------------------------------------------------------------------

def execute(scene_spec, config, build_plan=None):
    """계획을 실제로 만든다. 반환: BuildResult"""
    result = BuildResult()

    if build_plan is None:
        build_plan = plan_module.build_plan(scene_spec, config)

    if build_plan.conflicts:
        for item in build_plan.conflicts:
            result.errors.append("{} ({})".format(item.path, item.detail))
        result.errors.append(
            "Nothing was created. Resolve the name conflicts above and run again."
        )
        return result

    builder = naming.NameBuilder(config, scene_spec.root_path, scene_spec.stem,
                                 scene_spec.scene_number)
    sub_type_entries = config["sub_types"]
    camera_float_tracks = config.get("camera", {}).get("float_tracks", [])
    total_frames = scene_spec.total_frames

    dirty_paths = []

    def remember(asset_path):
        if asset_path not in dirty_paths:
            dirty_paths.append(asset_path)

    with unreal.ScopedEditorTransaction("JUN Build Cinematic Sequences"):
        with unreal.ScopedSlowTask(build_plan.total_steps, "Building cinematic sequences") as task:
            task.make_dialog(True)

            # --- A. 씬 폴더 --------------------------------------------------
            ensure_directory(builder.scene_path, result)
            if scene_spec.make_side_folders:
                ensure_directory(builder.scene_map_path, result)
                ensure_directory(builder.scene_animation_path, result)

            # --- B. 씬 레벨 SSEQ (leaf) --------------------------------------
            scene_subsequences = {}
            if scene_spec.make_scene_subs:
                ensure_directory(builder.scene_subsequence_path, result)
                for entry in sub_type_entries:
                    if task.should_cancel():
                        result.cancelled = True
                        break
                    sub_type = entry["key"]
                    task.enter_progress_frame(1, "Scene subsequence {}".format(sub_type))

                    asset_path = builder.scene_sub_asset_path(sub_type)
                    sequence, created = get_or_create_sequence(asset_path, result)
                    if sequence is None:
                        continue
                    if created:
                        apply_sequence_settings(sequence, scene_spec, 0, max(total_frames, 1), result)
                        remember(asset_path)
                    scene_subsequences[sub_type] = sequence

            # --- C. 컷: leaf SSEQ → CSEQ ------------------------------------
            cut_sequences = []
            for cut in scene_spec.cuts:
                if result.cancelled or task.should_cancel():
                    result.cancelled = True
                    break

                task.enter_progress_frame(1, "Cut {}".format(cut.name))

                ensure_directory(builder.cut_path(cut.name), result)
                if scene_spec.make_side_folders:
                    ensure_directory(builder.cut_animation_path(cut.name), result)
                    ensure_directory(builder.cut_vfx_path(cut.name), result)

                cut_subsequences = {}
                if scene_spec.make_cut_subs:
                    ensure_directory(builder.cut_subsequence_path(cut.name), result)
                    for entry in sub_type_entries:
                        sub_type = entry["key"]
                        asset_path = builder.cut_sub_asset_path(cut.name, sub_type)
                        sequence, created = get_or_create_sequence(asset_path, result)
                        if sequence is None:
                            continue
                        if created:
                            apply_sequence_settings(
                                sequence, scene_spec, 0, cut.duration_frames, result
                            )
                            # CAM 만 내용이 있다. 나머지 6종은 빈 껍데기로 둔다.
                            if sub_type == "CAM" and scene_spec.make_camera_rig:
                                if not camera_module.is_already_set_up(sequence):
                                    for message in camera_module.setup_camera(
                                        sequence,
                                        builder.camera_binding_name(cut.name),
                                        cut.duration_frames,
                                        camera_float_tracks,
                                    ):
                                        result.warn(message)
                                    result.cameras_set_up += 1
                            remember(asset_path)
                        cut_subsequences[sub_type] = sequence

                # CSEQ
                cut_asset_path = builder.cut_asset_path(cut.name)
                cut_sequence, created = get_or_create_sequence(cut_asset_path, result)
                if cut_sequence is None:
                    continue
                if created:
                    apply_sequence_settings(cut_sequence, scene_spec, 0, cut.duration_frames, result)

                # CSEQ ← 컷 SSEQ 7종
                links_before = result.linked
                for row_index, entry in enumerate(sub_type_entries):
                    sub_type = entry["key"]
                    child = cut_subsequences.get(sub_type)
                    if child is None:
                        continue
                    link_subsequence(
                        cut_sequence,
                        child,
                        0,
                        cut.duration_frames,
                        result,
                        display_name=sub_type,
                        track_color=(
                            compat.color_from_hex(entry["track_color"])
                            if scene_spec.apply_colors else None
                        ),
                        folder_name=sub_type if scene_spec.apply_colors else None,
                        row_index=row_index,
                    )
                    if scene_spec.apply_colors:
                        _apply_folder_color(cut_sequence, sub_type, entry["folder_color"], result)

                # 빈 Camera Cut Track — 컷 작업 시 아티스트가 채운다 (실측 CSEQ 와 동일)
                camera_cut_added = False
                if not compat.find_sequence_tracks(cut_sequence, unreal.MovieSceneCameraCutTrack):
                    try:
                        compat.add_sequence_track(cut_sequence, unreal.MovieSceneCameraCutTrack)
                        camera_cut_added = True
                    except compat.BindingUnavailable as error:
                        result.warn("Could not add a camera cut track to a cut sequence: {}".format(error))

                # 우리가 실제로 건드린 것만 저장 대상에 올린다. 손대지 않은 에셋을 다시 저장하면
                # 내용이 같아도 SVN 이 수정으로 잡는다.
                if created or camera_cut_added or result.linked > links_before:
                    remember(cut_asset_path)
                cut_sequences.append((cut, cut_sequence))

            # --- D. 마스터 ---------------------------------------------------
            if not result.cancelled:
                task.enter_progress_frame(1, "Master sequence")

                master_path = builder.master_asset_path()
                master_sequence, created = get_or_create_sequence(master_path, result)

                if master_sequence is not None:
                    if created:
                        apply_sequence_settings(
                            master_sequence, scene_spec, 0, max(total_frames, 1), result
                        )
                    else:
                        # 이미 있는 마스터의 재생 범위·프레임레이트는 건드리지 않는다.
                        # 컷을 뒤에 덧붙였다면 사용자가 직접 늘려야 한다.
                        result.warn(
                            "The master sequence already existed - its playback range and frame "
                            "rate were left as they were. Extend the range by hand if you added cuts."
                        )

                    links_before = result.linked

                    # 씬 레벨 SSEQ 7종 — 씬 전체 길이
                    for row_index, entry in enumerate(sub_type_entries):
                        sub_type = entry["key"]
                        child = scene_subsequences.get(sub_type)
                        if child is None:
                            continue
                        link_subsequence(
                            master_sequence,
                            child,
                            0,
                            max(total_frames, 1),
                            result,
                            display_name=sub_type,
                            track_color=(
                                compat.color_from_hex(entry["track_color"])
                                if scene_spec.apply_colors else None
                            ),
                            folder_name=sub_type if scene_spec.apply_colors else None,
                            row_index=row_index,
                        )
                        if scene_spec.apply_colors:
                            _apply_folder_color(
                                master_sequence, sub_type, entry["folder_color"], result
                            )

                    # CSEQ 를 샷으로 — 누적 오프셋 순차 배치 (D6/D7)
                    link_shots(
                        master_sequence,
                        [
                            (
                                cut_sequence,
                                cut.start_frame,
                                cut.end_frame,
                                builder.shot_display_name(cut.name),
                            )
                            for cut, cut_sequence in cut_sequences
                        ],
                        result,
                    )

                    if created or result.linked > links_before:
                        remember(master_path)

    # --- E. 저장: 우리가 건드린 것만 (D5) --------------------------------------
    for asset_path in dirty_paths:
        try:
            if unreal.EditorAssetLibrary.save_asset(asset_path, only_if_is_dirty=False):
                result.saved.append(asset_path)
        except Exception as error:
            result.warn("Could not save '{}': {}".format(asset_path, error))

    if result.cancelled:
        result.warn(
            "Cancelled by the user. Assets created before the cancel are still on disk - "
            "run again to finish, or delete them by hand."
        )

    return result

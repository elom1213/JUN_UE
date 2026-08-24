# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-24
#
# A00520 - 엔진 버전별 Python 바인딩 차이 흡수.
#
# 프로토타입 `Docs/Plans/seq_batch_tool_ue57.py` 의 `_call_first_working` + `*_compat()` 패턴을
# 이식한 것이다. 그 스크립트가 5.7 에서 실제로 겪은 사고가 근거다:
#   `LevelSequence.add_master_track` 이 버전에 따라 있기도, 없기도 하다.
#
# **버전차 흡수 로직은 이 파일에만 둔다.** 엔진이 5.8 로 올라가 API 가 또 갈릴 때
# 고칠 곳이 한 군데로 남게 하려는 것이다. 다른 모듈은 여기 함수만 부른다.
#
# 규칙:
#   - 반드시 성공해야 하는 것 → `call_first_working()` 으로 후보를 돌리고 실패 시 RuntimeError
#   - 없어도 되는 것(컬러 등)  → try 로 삼키고 True/False 를 돌려준다. 호출부가 경고를 남긴다

import unreal


class BindingUnavailable(RuntimeError):
    """필요한 Python 바인딩을 어떤 후보로도 찾지 못했다."""


def call_first_working(candidates, context):
    """(함수, 인자튜플) 후보를 순서대로 시도하고 첫 성공을 돌려준다."""
    last_error = None
    for function, arguments in candidates:
        try:
            return function(*arguments)
        except Exception as error:  # noqa: BLE001 - 다음 후보로 넘어가기 위한 광범위 캐치
            last_error = error
            continue
    raise BindingUnavailable(
        "{} - no usable python binding found. last error: {}".format(context, last_error)
    )


def _library(name):
    """`unreal.<name>` 이 있으면 돌려주고 없으면 None."""
    return getattr(unreal, name, None)


# ---------------------------------------------------------------------------
# 시퀀스 트랙
# ---------------------------------------------------------------------------

def add_sequence_track(sequence, track_class):
    """시퀀스에 트랙을 추가한다.

    5.4+ 는 `add_track`, 그 이전은 `add_master_track`. 양쪽 다, 그리고 확장 라이브러리
    경유까지 후보에 넣는다. 최신 이름을 먼저 시도한다.
    """
    extensions = _library("MovieSceneSequenceExtensions")
    candidates = []

    if hasattr(sequence, "add_track"):
        candidates.append((sequence.add_track, (track_class,)))
    if extensions is not None and hasattr(extensions, "add_track"):
        candidates.append((extensions.add_track, (sequence, track_class)))
    if hasattr(sequence, "add_master_track"):
        candidates.append((sequence.add_master_track, (track_class,)))
    if extensions is not None and hasattr(extensions, "add_master_track"):
        candidates.append((extensions.add_master_track, (sequence, track_class)))

    return call_first_working(candidates, "add_sequence_track({})".format(track_class.__name__))


def get_sequence_tracks(sequence):
    """시퀀스의 최상위 트랙 전부."""
    extensions = _library("MovieSceneSequenceExtensions")
    candidates = []

    if hasattr(sequence, "get_tracks"):
        candidates.append((sequence.get_tracks, ()))
    if extensions is not None and hasattr(extensions, "get_tracks"):
        candidates.append((extensions.get_tracks, (sequence,)))
    if hasattr(sequence, "get_master_tracks"):
        candidates.append((sequence.get_master_tracks, ()))
    if extensions is not None and hasattr(extensions, "get_master_tracks"):
        candidates.append((extensions.get_master_tracks, (sequence,)))

    try:
        return list(call_first_working(candidates, "get_sequence_tracks") or [])
    except BindingUnavailable:
        return []


def find_sequence_tracks(sequence, track_class):
    """주어진 클래스의 트랙만 골라 돌려준다."""
    return [track for track in get_sequence_tracks(sequence) if isinstance(track, track_class)]


def get_track_sections(track):
    try:
        return list(track.get_sections() or [])
    except Exception:
        return []


def get_section_sequence(section):
    """서브/샷 섹션이 가리키는 시퀀스. 아니면 None."""
    try:
        return section.get_sequence()
    except Exception:
        return None


def set_section_range(section, start_frame, end_frame):
    candidates = [(section.set_range, (int(start_frame), int(end_frame)))]
    if hasattr(section, "set_start_frame") and hasattr(section, "set_end_frame"):
        def _split():
            section.set_start_frame(int(start_frame))
            section.set_end_frame(int(end_frame))
        candidates.append((_split, ()))
    return call_first_working(candidates, "set_section_range")


def set_section_row_index(section, row_index):
    try:
        section.set_row_index(int(row_index))
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# 바인딩 (카메라 셋업용)
# ---------------------------------------------------------------------------

def add_possessable(sequence, target_object):
    extensions = _library("MovieSceneSequenceExtensions")
    candidates = []
    if hasattr(sequence, "add_possessable"):
        candidates.append((sequence.add_possessable, (target_object,)))
    if extensions is not None and hasattr(extensions, "add_possessable"):
        candidates.append((extensions.add_possessable, (sequence, target_object)))
    return call_first_working(candidates, "add_possessable")


def add_spawnable_from_instance(sequence, source_actor):
    extensions = _library("MovieSceneSequenceExtensions")
    candidates = []
    if hasattr(sequence, "add_spawnable_from_instance"):
        candidates.append((sequence.add_spawnable_from_instance, (source_actor,)))
    if extensions is not None and hasattr(extensions, "add_spawnable_from_instance"):
        candidates.append((extensions.add_spawnable_from_instance, (sequence, source_actor)))
    return call_first_working(candidates, "add_spawnable_from_instance")


def add_binding_track(binding, track_class):
    extensions = _library("MovieSceneBindingExtensions")
    candidates = []
    if hasattr(binding, "add_track"):
        candidates.append((binding.add_track, (track_class,)))
    if extensions is not None and hasattr(extensions, "add_track"):
        candidates.append((extensions.add_track, (binding, track_class)))
    return call_first_working(candidates, "add_binding_track({})".format(track_class.__name__))


def set_binding_parent(child_binding, parent_binding):
    extensions = _library("MovieSceneBindingExtensions")
    candidates = []
    if hasattr(child_binding, "set_parent"):
        candidates.append((child_binding.set_parent, (parent_binding,)))
    if extensions is not None and hasattr(extensions, "set_parent"):
        candidates.append((extensions.set_parent, (child_binding, parent_binding)))
    return call_first_working(candidates, "set_binding_parent")


def set_binding_name(binding, name):
    extensions = _library("MovieSceneBindingExtensions")
    candidates = []
    if hasattr(binding, "set_name"):
        candidates.append((binding.set_name, (name,)))
    if extensions is not None and hasattr(extensions, "set_name"):
        candidates.append((extensions.set_name, (binding, name)))
    try:
        call_first_working(candidates, "set_binding_name")
        return True
    except BindingUnavailable:
        return False


def get_binding_id(sequence, binding):
    extensions = _library("MovieSceneSequenceExtensions")
    candidates = []
    if extensions is not None and hasattr(extensions, "get_binding_id"):
        candidates.append((extensions.get_binding_id, (sequence, binding)))
    if hasattr(binding, "get_id"):
        candidates.append((binding.get_id, ()))
    return call_first_working(candidates, "get_binding_id")


def get_bindings(sequence):
    extensions = _library("MovieSceneSequenceExtensions")
    candidates = []
    if hasattr(sequence, "get_bindings"):
        candidates.append((sequence.get_bindings, ()))
    if extensions is not None and hasattr(extensions, "get_bindings"):
        candidates.append((extensions.get_bindings, (sequence,)))
    try:
        return list(call_first_working(candidates, "get_bindings") or [])
    except BindingUnavailable:
        return []


def get_binding_tracks(binding):
    extensions = _library("MovieSceneBindingExtensions")
    candidates = []
    if hasattr(binding, "get_tracks"):
        candidates.append((binding.get_tracks, ()))
    if extensions is not None and hasattr(extensions, "get_tracks"):
        candidates.append((extensions.get_tracks, (binding,)))
    try:
        return list(call_first_working(candidates, "get_binding_tracks") or [])
    except BindingUnavailable:
        return []


def remove_binding(sequence, binding):
    """빈 바인딩 정리. 바인딩이 없는 엔진도 있으므로 성공 여부를 bool 로 돌려준다."""
    extensions = _library("MovieSceneSequenceExtensions")
    if extensions is not None and hasattr(extensions, "remove_binding"):
        try:
            extensions.remove_binding(sequence, binding)
            return True
        except Exception:
            return False
    try:
        binding.remove()
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# 시퀀스 설정
# ---------------------------------------------------------------------------

def set_display_rate(sequence, frames_per_second):
    rate = unreal.FrameRate(numerator=int(frames_per_second), denominator=1)
    extensions = _library("MovieSceneSequenceExtensions")
    candidates = []
    if hasattr(sequence, "set_display_rate"):
        candidates.append((sequence.set_display_rate, (rate,)))
    if extensions is not None and hasattr(extensions, "set_display_rate"):
        candidates.append((extensions.set_display_rate, (sequence, rate)))
    try:
        call_first_working(candidates, "set_display_rate")
        return True
    except BindingUnavailable:
        return False


def set_tick_resolution(sequence, ticks_per_second):
    rate = unreal.FrameRate(numerator=int(ticks_per_second), denominator=1)
    extensions = _library("MovieSceneSequenceExtensions")
    candidates = []
    if hasattr(sequence, "set_tick_resolution"):
        candidates.append((sequence.set_tick_resolution, (rate,)))
    if extensions is not None and hasattr(extensions, "set_tick_resolution"):
        candidates.append((extensions.set_tick_resolution, (sequence, rate)))
    try:
        call_first_working(candidates, "set_tick_resolution")
        return True
    except BindingUnavailable:
        return False


def set_playback_range(sequence, start_frame, end_frame):
    extensions = _library("MovieSceneSequenceExtensions")
    candidates = []
    if hasattr(sequence, "set_playback_range"):
        candidates.append((sequence.set_playback_range, (int(start_frame), int(end_frame))))
    if extensions is not None and hasattr(extensions, "set_playback_range"):
        candidates.append((extensions.set_playback_range, (sequence, int(start_frame), int(end_frame))))

    def _split():
        sequence.set_playback_start(int(start_frame))
        sequence.set_playback_end(int(end_frame))

    if hasattr(sequence, "set_playback_start") and hasattr(sequence, "set_playback_end"):
        candidates.append((_split, ()))

    try:
        call_first_working(candidates, "set_playback_range")
        return True
    except BindingUnavailable:
        return False


# ---------------------------------------------------------------------------
# 폴더 · 컬러  (계획서 §7 R1 / R2 — 미확인 영역. 실패해도 진행한다)
# ---------------------------------------------------------------------------

def color_from_hex(hex_string):
    """'#FF604F' → unreal.Color"""
    value = str(hex_string).lstrip("#")
    if len(value) == 3:
        value = "".join(character * 2 for character in value)
    red = int(value[0:2], 16)
    green = int(value[2:4], 16)
    blue = int(value[4:6], 16)
    alpha = int(value[6:8], 16) if len(value) >= 8 else 255
    return unreal.Color(r=red, g=green, b=blue, a=alpha)


def add_root_folder(sequence, folder_name):
    """시퀀서 트리의 최상위 폴더. 만들지 못하면 None."""
    extensions = _library("MovieSceneSequenceExtensions")
    candidates = []
    if hasattr(sequence, "add_root_folder_to_sequence"):
        candidates.append((sequence.add_root_folder_to_sequence, (folder_name,)))
    if extensions is not None and hasattr(extensions, "add_root_folder_to_sequence"):
        candidates.append((extensions.add_root_folder_to_sequence, (sequence, folder_name)))
    try:
        return call_first_working(candidates, "add_root_folder")
    except BindingUnavailable:
        return None


def get_root_folders(sequence):
    """시퀀서 트리의 최상위 폴더 목록. 못 얻으면 빈 목록."""
    extensions = _library("MovieSceneSequenceExtensions")
    candidates = []
    if hasattr(sequence, "get_root_folders_in_sequence"):
        candidates.append((sequence.get_root_folders_in_sequence, ()))
    if extensions is not None and hasattr(extensions, "get_root_folders_in_sequence"):
        candidates.append((extensions.get_root_folders_in_sequence, (sequence,)))
    try:
        return list(call_first_working(candidates, "get_root_folders") or [])
    except BindingUnavailable:
        return []


def get_folder_name(folder):
    """폴더 이름 문자열. 못 읽으면 빈 문자열."""
    extensions = _library("MovieSceneFolderExtensions")
    if extensions is not None and hasattr(extensions, "get_folder_name"):
        try:
            return str(extensions.get_folder_name(folder))
        except Exception:
            pass
    for property_name in ("folder_name", "FolderName"):
        try:
            return str(folder.get_editor_property(property_name))
        except Exception:
            continue
    return ""


def set_folder_color(folder, color):
    """폴더 컬러. 바인딩이 없으면 False — 호출부가 경고만 남기고 계속 간다."""
    extensions = _library("MovieSceneFolderExtensions")
    if extensions is not None and hasattr(extensions, "set_folder_color"):
        try:
            extensions.set_folder_color(folder, color)
            return True
        except Exception:
            pass
    for property_name in ("folder_color", "FolderColor"):
        try:
            folder.set_editor_property(property_name, color)
            return True
        except Exception:
            continue
    return False


def add_track_to_folder(folder, track):
    """트랙을 폴더 아래로 옮긴다. 실패하면 False."""
    extensions = _library("MovieSceneFolderExtensions")
    if extensions is None:
        return False
    for method_name in ("add_child_track", "add_child_master_track"):
        function = getattr(extensions, method_name, None)
        if function is None:
            continue
        try:
            function(folder, track)
            return True
        except Exception:
            continue
    return False


def set_track_color(track, color):
    """트랙 틴트. 바인딩이 없으면 False."""
    extensions = _library("MovieSceneTrackExtensions")
    if extensions is not None and hasattr(extensions, "set_color_tint"):
        try:
            extensions.set_color_tint(track, color)
            return True
        except Exception:
            pass
    for property_name in ("track_tint", "TrackTint"):
        try:
            track.set_editor_property(property_name, color)
            return True
        except Exception:
            continue
    return False


def set_track_display_name(track, display_name):
    extensions = _library("MovieSceneTrackExtensions")
    if extensions is not None and hasattr(extensions, "set_display_name"):
        for value in (display_name, unreal.Text(display_name)):
            try:
                extensions.set_display_name(track, value)
                return True
            except Exception:
                continue
    try:
        track.set_editor_property("display_name", display_name)
        return True
    except Exception:
        return False


def set_shot_display_name(section, display_name):
    for method_name in ("set_shot_display_name", "set_display_name"):
        function = getattr(section, method_name, None)
        if function is None:
            continue
        try:
            function(display_name)
            return True
        except Exception:
            continue
    return False


# ---------------------------------------------------------------------------
# 레벨 액터  (프로토타입 D9 — EditorLevelLibrary 는 UE5 에서 deprecated 경고 대상)
# ---------------------------------------------------------------------------

def _actor_subsystem():
    actor_subsystem_class = _library("EditorActorSubsystem")
    if actor_subsystem_class is None:
        return None
    try:
        return unreal.get_editor_subsystem(actor_subsystem_class)
    except Exception:
        return None


def spawn_actor(actor_class, location=None, rotation=None):
    location = location if location is not None else unreal.Vector(0.0, 0.0, 0.0)
    rotation = rotation if rotation is not None else unreal.Rotator(0.0, 0.0, 0.0)

    candidates = []
    subsystem = _actor_subsystem()
    if subsystem is not None and hasattr(subsystem, "spawn_actor_from_class"):
        candidates.append((subsystem.spawn_actor_from_class, (actor_class, location, rotation)))

    level_library = _library("EditorLevelLibrary")
    if level_library is not None and hasattr(level_library, "spawn_actor_from_class"):
        candidates.append((level_library.spawn_actor_from_class, (actor_class, location, rotation)))

    return call_first_working(candidates, "spawn_actor({})".format(actor_class.__name__))


def destroy_actor(actor):
    if actor is None:
        return False

    subsystem = _actor_subsystem()
    if subsystem is not None and hasattr(subsystem, "destroy_actor"):
        try:
            subsystem.destroy_actor(actor)
            return True
        except Exception:
            pass

    level_library = _library("EditorLevelLibrary")
    if level_library is not None and hasattr(level_library, "destroy_actor"):
        try:
            level_library.destroy_actor(actor)
            return True
        except Exception:
            pass

    try:
        actor.destroy_actor()
        return True
    except Exception:
        return False

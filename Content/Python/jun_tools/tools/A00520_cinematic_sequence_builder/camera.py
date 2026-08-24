# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-24
#
# A00520 - CAM 서브시퀀스의 CineCamera 초기 셋업.
#
# 프로토타입 `seq_batch_tool_ue57.py` 의 `setup_cam_sequence_with_cine()` (176~276줄) 이식.
#
# 이 셋업을 툴이 하는 근거: 실측한 `SSEQ_PreDebut_TSR_CT01_S01_C0010_CAM.uasset` 에서 추출한
# 클래스 목록(스포너블 CineCameraActor / CameraCutTrack / 3DTransformTrack ×2 /
# FloatTrack ×3 - CurrentAperture · CurrentFocalLength · FocusSettings:ManualFocusDistance)이
# 프로토타입 출력과 **프로퍼티 경로까지 일치**한다. 아티스트가 손으로 하던 초기 셋업이다.
#
# 프로토타입에서 고친 것:
#   D8  이름 역파싱(`seq_name.replace("SEQ_cam_", "")`) 제거 → 호출부가 템플릿으로 조립해 넘긴다
#   D9  `EditorLevelLibrary` 직접 호출 → `compat.spawn_actor/destroy_actor` (EditorActorSubsystem 우선)
#   --  임시 액터 삭제를 try/finally 로 보장 (중간에 실패해도 레벨에 카메라가 남지 않는다)
#   --  float 트랙 목록을 설정(JSON)에서 받는다

import unreal

from . import compat


def is_already_set_up(sequence):
    """이미 카메라 컷 트랙이 있으면 손대지 않는다(비파괴)."""
    return bool(compat.find_sequence_tracks(sequence, unreal.MovieSceneCameraCutTrack))


def setup_camera(sequence, binding_name, duration_frames, float_tracks=None):
    """cam_sequence 안에 CineCameraActor 스포너블 + 카메라 컷 + 기본 트랙을 만든다.

    Returns: 경고 문자열 목록 (비어 있으면 완전 성공)
    """
    warnings = []
    float_tracks = float_tracks or []
    temporary_actor = None

    try:
        # 0) 레벨에 임시 CineCameraActor 를 스폰한다. 스포너블 템플릿을 뜨기 위한 것뿐이다.
        temporary_actor = compat.spawn_actor(unreal.CineCameraActor)

        # 1) 임시 액터로부터 스포너블 바인딩 생성
        camera_binding = compat.add_spawnable_from_instance(sequence, temporary_actor)

        # 2) CineCameraComponent 를 Possessable 로 추가하고 액터 바인딩의 자식으로 붙인다
        camera_component = temporary_actor.get_cine_camera_component()
        component_binding = compat.add_possessable(sequence, camera_component)
        compat.set_binding_parent(component_binding, camera_binding)

        # 3) Camera Cut Track — 스포너블 카메라를 바인딩 ID 로 연결
        camera_cut_track = compat.add_sequence_track(sequence, unreal.MovieSceneCameraCutTrack)
        camera_cut_section = camera_cut_track.add_section()
        compat.set_section_range(camera_cut_section, 0, duration_frames)
        try:
            binding_id = compat.get_binding_id(sequence, camera_binding)
            camera_cut_section.set_camera_binding_id(binding_id)
        except Exception as error:
            warnings.append("could not bind the camera cut section: {}".format(error))

        # 4) 액터 Transform 트랙
        actor_transform_track = compat.add_binding_track(
            camera_binding, unreal.MovieScene3DTransformTrack
        )
        compat.set_section_range(actor_transform_track.add_section(), 0, duration_frames)

        # 5) 컴포넌트 Transform 트랙
        component_transform_track = compat.add_binding_track(
            component_binding, unreal.MovieScene3DTransformTrack
        )
        compat.set_section_range(component_transform_track.add_section(), 0, duration_frames)

        # 6) 컴포넌트 Float 트랙 (초점거리 / 조리개 / 수동 초점거리)
        for entry in float_tracks:
            try:
                float_track = compat.add_binding_track(
                    component_binding, unreal.MovieSceneFloatTrack
                )
                unreal.MovieScenePropertyTrackExtensions.set_property_name_and_path(
                    float_track, entry["name"], entry["path"]
                )
                compat.set_section_range(float_track.add_section(), 0, duration_frames)
            except Exception as error:
                warnings.append(
                    "could not add float track '{}': {}".format(entry.get("name"), error)
                )

        # 7) 스포너블 이름 정리. 역파싱이 아니라 호출부가 템플릿으로 조립해 넘긴 이름을 쓴다 (D8)
        if binding_name and not compat.set_binding_name(camera_binding, binding_name):
            warnings.append("could not rename the camera binding to '{}'".format(binding_name))

        # 8) 트랙이 하나도 없는 빈 바인딩 정리
        #    add_spawnable_from_instance 가 잔여 바인딩을 남기는 엔진 버전이 있다.
        for binding in compat.get_bindings(sequence):
            if binding in (camera_binding, component_binding):
                continue
            if compat.get_binding_tracks(binding):
                continue
            if not compat.remove_binding(sequence, binding):
                warnings.append(
                    "an empty binding could not be removed - if the sequencer shows a red "
                    "binding, delete it by hand (remove_binding may be missing on this engine)"
                )

        return warnings

    finally:
        # 임시 액터는 무슨 일이 있어도 지운다. 프로토타입은 정상 경로에서만 지웠다.
        if temporary_actor is not None:
            if not compat.destroy_actor(temporary_actor):
                warnings.append(
                    "the temporary CineCameraActor could not be removed from the level - "
                    "delete it by hand"
                )

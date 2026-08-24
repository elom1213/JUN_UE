import unreal

# ===============================
# 기본 설정값
# ===============================

DEFAULT_ROOT_PATH = "/Game"     # 루트 폴더 기본값 (선택 폴더 없을 때 fallback)
DEFAULT_START_NUMBER = 1010     # 샷 번호 시작 (01010)
DEFAULT_STEP = 10               # 샷 번호 증가 단위 (01010, 01020, 01030 ...)


# ===============================
# 유틸 함수들
# ===============================

def ensure_directory(path: str):
    """폴더가 없으면 생성"""
    editor_lib = unreal.EditorAssetLibrary
    if not editor_lib.does_directory_exist(path):
        editor_lib.make_directory(path)


def create_level_sequence(asset_name: str, package_path: str) -> unreal.LevelSequence:
    """레벨 시퀀스를 생성하고 반환"""
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    factory = unreal.LevelSequenceFactoryNew()
    sequence = asset_tools.create_asset(
        asset_name=asset_name,
        package_path=package_path,
        asset_class=unreal.LevelSequence,
        factory=factory
    )
    return sequence


def save_all_under(path: str):
    """지정 경로 아래의 모든 에셋 저장"""
    unreal.EditorAssetLibrary.save_directory(path, only_if_is_dirty=False, recursive=True)


def get_root_path_from_content_browser(default_root: str = DEFAULT_ROOT_PATH) -> str:
    """
    콘텐츠 브라우저에서 선택된 폴더나 현재 경로를 가져와서 root path로 사용.
    - 폴더 선택되어 있으면: 그 폴더 사용
    - 아니면 현재 Content Browser 경로 사용
    - 그래도 없으면 DEFAULT_ROOT_PATH 사용
    """
    util_lib = unreal.EditorUtilityLibrary

    # 1) 선택된 폴더 우선
    folder_paths = util_lib.get_selected_folder_paths()
    if folder_paths:
        return folder_paths[0]

    # 2) 활성 콘텐츠 브라우저의 현재 경로
    current_path = util_lib.get_current_content_browser_path()
    if current_path:
        return current_path

    # 3) 둘 다 없으면 fallback
    return default_root




# ===============================
# UE 버전별 Python 바인딩 차이 대응 (5.7 포함)
# ===============================

def _call_first_working(calls, context: str):
    """여러 호출 후보 중 첫 번째로 성공하는 것을 반환."""
    last_err = None
    for fn, args in calls:
        try:
            return fn(*args)
        except Exception as e:
            last_err = e
            continue
    raise RuntimeError(f"[SeqTool] {context} - 사용 가능한 Python 바인딩을 찾지 못했습니다. 마지막 에러: {last_err}")


def add_master_track_compat(seq: unreal.MovieSceneSequence, track_class):
    """UE 5.7에서 LevelSequence.add_master_track 바인딩이 없는 경우를 포함해 호환적으로 마스터 트랙을 추가."""
    calls = []

    # 1) 일부 버전: LevelSequence.add_master_track(track_class)
    if hasattr(seq, "add_master_track"):
        calls.append((getattr(seq, "add_master_track"), (track_class,)))

    # 2) 일부 버전: MovieSceneSequenceExtensions.add_master_track(seq, track_class)
    if hasattr(unreal, "MovieSceneSequenceExtensions") and hasattr(unreal.MovieSceneSequenceExtensions, "add_master_track"):
        calls.append((unreal.MovieSceneSequenceExtensions.add_master_track, (seq, track_class)))

    # 3) 혹시 add_track 로만 공개된 경우
    if hasattr(unreal, "MovieSceneSequenceExtensions") and hasattr(unreal.MovieSceneSequenceExtensions, "add_track"):
        calls.append((unreal.MovieSceneSequenceExtensions.add_track, (seq, track_class)))

    return _call_first_working(calls, "add_master_track_compat")


def add_possessable_compat(seq: unreal.MovieSceneSequence, obj):
    """LevelSequence.add_possessable 바인딩 유무에 따라 호환적으로 Possessable 바인딩 추가."""
    calls = []
    if hasattr(seq, "add_possessable"):
        calls.append((getattr(seq, "add_possessable"), (obj,)))
    if hasattr(unreal, "MovieSceneSequenceExtensions") and hasattr(unreal.MovieSceneSequenceExtensions, "add_possessable"):
        calls.append((unreal.MovieSceneSequenceExtensions.add_possessable, (seq, obj)))
    return _call_first_working(calls, "add_possessable_compat")


# def add_binding_track_compat(binding: unreal.MovieSceneBinding, track_class):
def add_binding_track_compat(binding, track_class):
    """Binding.add_track / MovieSceneBindingExtensions.add_track 등 버전차 대응."""
    calls = []
    if hasattr(binding, "add_track"):
        calls.append((getattr(binding, "add_track"), (track_class,)))
    if hasattr(unreal, "MovieSceneBindingExtensions") and hasattr(unreal.MovieSceneBindingExtensions, "add_track"):
        calls.append((unreal.MovieSceneBindingExtensions.add_track, (binding, track_class)))
    return _call_first_working(calls, "add_binding_track_compat")


# def set_binding_parent_compat(child_binding: unreal.MovieSceneBinding, parent_binding: unreal.MovieSceneBinding):
def set_binding_parent_compat(child_binding, parent_binding):
    """child_binding.set_parent / MovieSceneBindingExtensions.set_parent 등 버전차 대응."""
    calls = []
    if hasattr(child_binding, "set_parent"):
        calls.append((getattr(child_binding, "set_parent"), (parent_binding,)))
    if hasattr(unreal, "MovieSceneBindingExtensions") and hasattr(unreal.MovieSceneBindingExtensions, "set_parent"):
        calls.append((unreal.MovieSceneBindingExtensions.set_parent, (child_binding, parent_binding)))
    return _call_first_working(calls, "set_binding_parent_compat")


def remove_binding_compat(seq: unreal.MovieSceneSequence, binding):
    """MovieSceneSequenceExtensions.remove_binding 의 유무/시그니처 차이 대응."""
    if hasattr(unreal, "MovieSceneSequenceExtensions") and hasattr(unreal.MovieSceneSequenceExtensions, "remove_binding"):
        try:
            unreal.MovieSceneSequenceExtensions.remove_binding(seq, binding)
            return True
        except Exception:
            return False
    return False

# ===============================
# 서브 시퀀스 / 카메라 셋업
# ===============================

def add_sub_sequences_to_parent(
    parent_seq: unreal.LevelSequence,
    sub_sequences,
    duration_frames: int = 100
):
    """
    parent_seq 안에 Sub Sequence Track을 3개 만들고
    각각 anim / cam / lgt 시퀀스를 하나씩 연결.
    모든 섹션의 프레임 범위는 0~duration_frames 동일.
    sub_sequences: [anim_seq, cam_seq, lgt_seq] 순서를 가정.
    """

    for sub_seq in sub_sequences:
        # 각 서브 시퀀스마다 master track 하나 생성
        sub_track = add_master_track_compat(parent_seq, unreal.MovieSceneSubTrack)

        # 섹션 하나 추가
        sub_section = sub_track.add_section()  # MovieSceneSubSection

        # 이 섹션이 재생할 시퀀스 지정
        sub_section.set_sequence(sub_seq)

        # 모든 섹션을 0~duration_frames 프레임 구간으로 고정
        sub_section.set_range(0, duration_frames)





def setup_cam_sequence_with_cine(cam_seq: unreal.LevelSequence, duration_frames: int = 100):
    """
    cam_seq 안에:
      - Spawnable CineCameraActor 하나 생성
      - Camera Cut Track + 섹션(0~duration_frames)
      - CineCameraActor Transform 트랙
      - CameraComponent 바인딩 + Transform / Aperture / FocalLength / ManualFocusDistance 트랙
      - Spawnable 이름: 시퀀스명_샷번호_camera
      - 마지막에 쓰이지 않는 빈 CineCameraActor 바인딩 정리(가능한 경우에만)
    """

    level_lib = unreal.EditorLevelLibrary

    # 0) 레벨에 임시 CineCameraActor 스폰
    temp_actor = level_lib.spawn_actor_from_class(
        unreal.CineCameraActor,
        unreal.Vector(0.0, 0.0, 0.0),
        unreal.Rotator(0.0, 0.0, 0.0)
    )

    # 1) 임시 액터로부터 Spawnable CineCameraActor 바인딩 생성
    cine_binding = unreal.MovieSceneSequenceExtensions.add_spawnable_from_instance(
        cam_seq,
        temp_actor
    )

    # 2) CameraComponent 를 Possessable 바인딩으로 추가 (Actor 바인딩의 자식)
    camera_component = temp_actor.get_cine_camera_component()
    component_binding = add_possessable_compat(cam_seq, camera_component)
    set_binding_parent_compat(component_binding, cine_binding)

    # 3) Camera Cut Track 셋업
    camera_cut_track = add_master_track_compat(cam_seq, unreal.MovieSceneCameraCutTrack)
    camera_cut_section = camera_cut_track.add_section()
    camera_cut_section.set_range(0, duration_frames)

    # ❗ 카메라 컷에 스포너블 카메라 제대로 바인딩
    binding_id = unreal.MovieSceneSequenceExtensions.get_binding_id(
        cam_seq,
        cine_binding
    )
    camera_cut_section.set_camera_binding_id(binding_id)

    # 4) Actor Transform 트랙
    actor_transform_track = add_binding_track_compat(cine_binding, unreal.MovieScene3DTransformTrack)
    actor_transform_section = actor_transform_track.add_section()
    actor_transform_section.set_range(0, duration_frames)

    # 5) CameraComponent Transform + Float 트랙들
    comp_transform_track = add_binding_track_compat(component_binding, unreal.MovieScene3DTransformTrack)
    comp_transform_section = comp_transform_track.add_section()
    comp_transform_section.set_range(0, duration_frames)

    def _add_component_float_track(prop_name: str, prop_path: str):
        float_track = add_binding_track_compat(component_binding, unreal.MovieSceneFloatTrack)
        unreal.MovieScenePropertyTrackExtensions.set_property_name_and_path(
            float_track,
            prop_name,
            prop_path
        )
        section = float_track.add_section()
        section.set_range(0, duration_frames)
        return float_track

    _add_component_float_track("CurrentFocalLength", "CurrentFocalLength")
    _add_component_float_track("CurrentAperture", "CurrentAperture")
    _add_component_float_track("ManualFocusDistance", "FocusSettings.ManualFocusDistance")

    # 6) Spawnable CineCameraActor 이름 정리 (SEQ_cam_xxx 에서 xxx만 추출)
    seq_name = cam_seq.get_name()                  # 예: "SEQ_cam_SCH_01010"
    base_name = seq_name.replace("SEQ_cam_", "")   # "SCH_01010"
    new_name = f"{base_name}_camera"               # "SCH_01010_camera"

    unreal.MovieSceneBindingExtensions.set_name(
        cine_binding,
        new_name
    )

    # 7) 레벨 위의 임시 액터 삭제 (Spawnable/Component 바인딩만 남김)
    level_lib.destroy_actor(temp_actor)

    
    # 8) ❗ 쓰이지 않는 빈 CineCameraActor 바인딩 정리
    #    (엔진 버전에 따라 remove_binding 바인딩이 없을 수 있으니 안전하게 처리)
    removed_any = False
    for binding in list(cam_seq.get_bindings()):
        if binding == cine_binding or binding == component_binding:
            continue

        tracks = binding.get_tracks()
        if len(tracks) == 0:
            if remove_binding_compat(cam_seq, binding):
                removed_any = True

    if not removed_any:
        # remove_binding이 없어서 못 지웠거나, 지울 대상이 없었던 경우
        unreal.log_warning(
            "[SeqTool] 빈 바인딩 정리를 자동으로 수행하지 못했거나(또는 대상이 없거나) "
            "엔진 Python 바인딩에 remove_binding이 없을 수 있습니다. "
            "시퀀서에 빨간 바인딩이 남아있다면 수동으로 삭제하세요."
        )

# ===============================
# 메인 생성 함수
# ===============================

def generate_sequences_for_shots(
    seq_code: str,
    shot_count: int,
    root_path: str = None,
    start_number: int = DEFAULT_START_NUMBER,
    step: int = DEFAULT_STEP,
    shot_duration: int = 100
):
    """
    예)
      - 콘텐츠 브라우저에서 /Game/Proj_Hi/Seq 선택 후:
            generate_sequences_for_shots("SCH", 10)

      - 샷 길이를 120프레임으로 쓰고 싶다면:
            generate_sequences_for_shots("SCH", 10, shot_duration=120)

    생성 구조:

    root_path/SEQCODE/
        SEQ_master_SEQCODE
        SEQCODE_01010/
            SEQ_SEQCODE_01010
            Sub/
                SEQ_anim_SEQCODE_01010
                SEQ_cam_SEQCODE_01010
                SEQ_lgt_SEQCODE_01010
    """

    # root_path를 안 넣으면, 콘텐츠 브라우저 선택 경로를 자동으로 사용
    if root_path is None:
        root_path = get_root_path_from_content_browser()

    seq_code = seq_code.upper()

    # 예: /Game/Proj_Hi/Seq/SCH
    seq_root = f"{root_path}/{seq_code}"
    ensure_directory(seq_root)

    unreal.log(f"[SeqTool] Root Path: {root_path}")
    unreal.log(f"[SeqTool] Seq Root:  {seq_root}")

    # 마스터 레벨 시퀀스 생성: /.../SCH/SEQ_master_SCH
    master_name = f"SEQ_master_{seq_code}"
    unreal.log(f"[SeqTool] Create master sequence: {seq_root}/{master_name}")
    master_seq = create_level_sequence(master_name, seq_root)

    # 샷 루프
    for i in range(shot_count):
        shot_number = start_number + (i * step)
        shot_str = f"{shot_number:05d}"      # 5자리 zero padding, 예: 01010

        # /.../SCH/SCH_01010
        shot_folder = f"{seq_root}/{seq_code}_{shot_str}"
        sub_folder = f"{shot_folder}/Sub"

        ensure_directory(shot_folder)
        ensure_directory(sub_folder)

        unreal.log(f"[SeqTool] === Shot {seq_code}_{shot_str} ===")
        unreal.log(f"[SeqTool] Shot folder: {shot_folder}")
        unreal.log(f"[SeqTool] Sub folder : {sub_folder}")

        # 샷 메인 시퀀스: SEQ_SCH_01010
        main_seq_name = f"SEQ_{seq_code}_{shot_str}"
        main_seq = create_level_sequence(main_seq_name, shot_folder)
        unreal.log(f"[SeqTool]   Created main: {shot_folder}/{main_seq_name}")

        # 서브 시퀀스들: anim / cam / lgt
        anim_seq_name = f"SEQ_anim_{seq_code}_{shot_str}"
        cam_seq_name  = f"SEQ_cam_{seq_code}_{shot_str}"
        lgt_seq_name  = f"SEQ_lgt_{seq_code}_{shot_str}"

        anim_seq = create_level_sequence(anim_seq_name, sub_folder)
        cam_seq  = create_level_sequence(cam_seq_name, sub_folder)
        lgt_seq  = create_level_sequence(lgt_seq_name, sub_folder)

        unreal.log(f"[SeqTool]   Created sub: {sub_folder}/{anim_seq_name}")
        unreal.log(f"[SeqTool]   Created sub: {sub_folder}/{cam_seq_name}")
        unreal.log(f"[SeqTool]   Created sub: {sub_folder}/{lgt_seq_name}")

        # cam 서브 시퀀스에 CineCameraActor + Camera Cut 자동 셋업
        setup_cam_sequence_with_cine(cam_seq, duration_frames=shot_duration)

        # 메인 시퀀스에 anim / cam / lgt 서브 시퀀스를
        # 각각 하나씩 Sub Sequence Track으로 추가 (모두 0~shot_duration)
        add_sub_sequences_to_parent(
            main_seq,
            [anim_seq, cam_seq, lgt_seq],
            duration_frames=shot_duration
        )

        # (옵션) 마스터 시퀀스 안에 각 샷 메인 시퀀스를 서브로 넣고 싶으면:
        # add_sub_sequences_to_parent(master_seq, [main_seq], duration_frames=shot_duration)

    # 모든 에셋 저장
    save_all_under(seq_root)
    unreal.log(f"[SeqTool] 모든 시퀀스와 폴더 생성 완료: {seq_root}")


# ===============================
# 사용 예 (Output Log > Python 탭에서)
# ===============================
# import seq_batch_tool
# seq_batch_tool.generate_sequences_for_shots("SCH", 10)
# seq_batch_tool.generate_sequences_for_shots("CTY", 23, shot_duration=120)

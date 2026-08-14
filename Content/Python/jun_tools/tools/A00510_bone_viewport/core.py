# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-14
#
# A00510_bone_viewport - 로직.
#
# 스켈레탈 메시 / 애니메이션 에디터 뷰포트의 본 표시 설정은 `UPersonaOptions` 라는
# 전역 설정 오브젝트(CDO)에 들어 있다. 뷰포트 툴바의
#   눈 아이콘(Show flags) > Bones > All Hierarchy
# 를 누르면 이 오브젝트의 `DefaultBoneDrawSelection` 이 바뀌는 것이다.
#
# ── 알아둘 것 ──────────────────────────────────────────────────────────────
# 1) `UPersonaOptions` 는 파이썬 클래스로 생성되지 않는다(`unreal.PersonaOptions` 없음).
#    그래서 CDO 를 경로로 직접 찾아 쓴다.
# 2) 그 경우 프로퍼티 이름은 파이썬 관례인 snake_case 가 아니라 **C++ 이름 그대로**다.
#    `DefaultBoneDrawSelection` (O) / `default_bone_draw_selection` (X)
# 3) 파이썬에서는 `SaveConfig()` 를 부를 수 없다 → 여기서 바꾼 값은 **이번 에디터 세션 한정**이다.
#    ini 에 남기려면 뷰포트 메뉴에서 Persona 옵션을 아무거나 한 번 바꿔주면 된다
#    (그때 엔진이 이 오브젝트 전체를 저장한다).
# 4) Bone Draw Size 는 여기에 없다. 뷰포트 객체(FAnimationViewportClient)의 평범한 C++
#    멤버라서 리플렉션이 없고, 파이썬에서 건드릴 방법이 없다. C++ 모듈이 필요하다.

import unreal

# UPersonaOptions 의 CDO 경로.
PERSONA_OPTIONS_PATH = "/Script/UnrealEd.Default__PersonaOptions"

PROP_BONE_DRAW_MODE = "DefaultBoneDrawSelection"
PROP_SHOW_BONE_COLORS = "bShowBoneColors"


class BoneDrawMode(object):
    """EBoneDrawMode (SkeletalDebugRendering.h) 의 값. 뷰포트 메뉴 라디오 버튼과 1:1."""

    NONE = 0
    SELECTED_ONLY = 1
    SELECTED_AND_PARENTS = 2
    SELECTED_AND_CHILDREN = 3
    SELECTED_AND_PARENTS_AND_CHILDREN = 4
    ALL_HIERARCHY = 5


# 로그에 찍을 이름. 뷰포트 메뉴에 표시되는 문구를 그대로 쓴다.
MODE_LABELS = {
    BoneDrawMode.NONE: "None",
    BoneDrawMode.SELECTED_ONLY: "Selected Only",
    BoneDrawMode.SELECTED_AND_PARENTS: "Selected and Parents",
    BoneDrawMode.SELECTED_AND_CHILDREN: "Selected and Children",
    BoneDrawMode.SELECTED_AND_PARENTS_AND_CHILDREN: "Selected and Parents and Children",
    BoneDrawMode.ALL_HIERARCHY: "All Hierarchy",
}


def mode_label(mode):
    return MODE_LABELS.get(int(mode), "Unknown({})".format(mode))


def get_persona_options():
    """UPersonaOptions CDO. 못 찾으면 RuntimeError."""
    options = unreal.find_object(None, PERSONA_OPTIONS_PATH)
    if options is None:
        raise RuntimeError("Could not find PersonaOptions at {}".format(PERSONA_OPTIONS_PATH))
    return options


def get_bone_draw_mode():
    return int(get_persona_options().get_editor_property(PROP_BONE_DRAW_MODE))


def set_bone_draw_mode(mode):
    """본 그리기 모드를 바꾸고 이전 값을 돌려준다."""
    options = get_persona_options()
    previous = int(options.get_editor_property(PROP_BONE_DRAW_MODE))
    options.set_editor_property(PROP_BONE_DRAW_MODE, int(mode))
    return previous


def get_show_bone_colors():
    return bool(get_persona_options().get_editor_property(PROP_SHOW_BONE_COLORS))


def set_show_bone_colors(enabled):
    """본을 여러 색으로 그릴지. 이 값은 그릴 때마다 읽히므로 즉시 반영된다."""
    options = get_persona_options()
    previous = bool(options.get_editor_property(PROP_SHOW_BONE_COLORS))
    options.set_editor_property(PROP_SHOW_BONE_COLORS, bool(enabled))
    return previous


def apply(bone_draw_mode=None, show_bone_colors=None):
    """설정을 한 번에 적용하고, 바뀐 항목을 (이름, 이전, 현재) 목록으로 돌려준다."""
    changed = []

    if bone_draw_mode is not None:
        previous = set_bone_draw_mode(bone_draw_mode)
        if previous != int(bone_draw_mode):
            changed.append(("Bone Draw Mode", mode_label(previous), mode_label(bone_draw_mode)))

    if show_bone_colors is not None:
        previous = set_show_bone_colors(show_bone_colors)
        if previous != bool(show_bone_colors):
            changed.append(("Show Bone Colors", str(previous), str(bool(show_bone_colors))))

    return changed

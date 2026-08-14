# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-14
#
# A00510_bone_viewport - UI.
#
# 뷰포트 툴바의 눈 아이콘 > Bones > (라디오 버튼) 을 타고 들어가지 않고
# 팝업 하나에서 본 표시 모드를 고른다.
#
# 다이얼로그는 `unreal.EditorDialog.show_object_details_view()` 로 만든다.
# 파이썬으로 만든 UObject 의 프로퍼티가 디테일 패널 형태로 그려지므로,
# uenum 을 쓰면 드롭다운이, bool 을 쓰면 체크박스가 된다.

import unreal

from . import core

TITLE = "JUN Bone Display Settings"

# 다이얼로그가 떠 있는 동안 설정 오브젝트가 GC 되지 않도록 붙잡아 둔다.
_ALIVE = []

# uclass / uenum 은 에디터에 등록되는 타입이라 한 번만 만들어 재사용한다.
_TYPES = None


def _build_types():
    """설정 오브젝트용 uenum + uclass 를 만든다."""

    @unreal.uenum()
    class JUNBoneDrawMode(unreal.EnumBase):
        NONE = unreal.uvalue(core.BoneDrawMode.NONE)
        SELECTED_ONLY = unreal.uvalue(core.BoneDrawMode.SELECTED_ONLY)
        SELECTED_AND_PARENTS = unreal.uvalue(core.BoneDrawMode.SELECTED_AND_PARENTS)
        SELECTED_AND_CHILDREN = unreal.uvalue(core.BoneDrawMode.SELECTED_AND_CHILDREN)
        SELECTED_AND_PARENTS_AND_CHILDREN = unreal.uvalue(
            core.BoneDrawMode.SELECTED_AND_PARENTS_AND_CHILDREN)
        ALL_HIERARCHY = unreal.uvalue(core.BoneDrawMode.ALL_HIERARCHY)

    @unreal.uclass()
    class JUNBoneDisplaySettings(unreal.Object):
        bone_draw_mode = unreal.uproperty(
            JUNBoneDrawMode,
            meta=dict(
                Category="Bone Display",
                DisplayName="Bone Draw Mode",
                ToolTip="Same as Show flags > Bones in the skeletal mesh viewport.",
            ),
        )
        show_bone_colors = unreal.uproperty(
            bool,
            meta=dict(
                Category="Bone Display",
                DisplayName="Show Bone Colors",
                ToolTip="Draw bones with multiple semi-random colors.",
            ),
        )

    return JUNBoneDisplaySettings, JUNBoneDrawMode


def _types():
    global _TYPES
    if _TYPES is None:
        _TYPES = _build_types()
    return _TYPES


def _to_enum(enum_cls, value):
    """정수를 uenum 값으로. 변환이 안 되면 정수를 그대로 돌려준다."""
    value = int(value)
    try:
        return enum_cls(value)
    except Exception:
        pass
    for name in dir(enum_cls):
        if name.startswith("_"):
            continue
        member = getattr(enum_cls, name)
        if getattr(member, "value", None) == value:
            return member
    return value


def _to_int(value):
    """uenum 값을 정수로."""
    return int(getattr(value, "value", value))


def _report(changed, mode_changed):
    """무엇이 바뀌었는지, 어떻게 해야 보이는지 Output Log 에 남긴다."""
    if not changed:
        unreal.log("[JUNTools] Bone display: nothing changed.")
        return

    for name, before, after in changed:
        unreal.log("[JUNTools] Bone display: {} : {} -> {}".format(name, before, after))

    if mode_changed:
        # 뷰포트는 그릴 본 목록을 캐시해 두고, 그 캐시는 에디터를 열 때 /
        # 프리뷰 메시가 바뀔 때 / 본 선택이 바뀔 때만 다시 계산된다.
        unreal.log(
            "[JUNTools] Applies to skeletal mesh editors opened from now on. "
            "For an editor that is already open, click any bone in the Skeleton Tree to refresh."
        )


def show():
    """본 표시 설정 팝업을 띄운다."""
    settings_cls, mode_enum = _types()

    settings = settings_cls()
    _ALIVE.append(settings)

    # 현재 값을 채워서 띄운다.
    current_mode = core.get_bone_draw_mode()
    settings.set_editor_property("bone_draw_mode", _to_enum(mode_enum, current_mode))
    settings.set_editor_property("show_bone_colors", core.get_show_bone_colors())

    dialog_options = unreal.EditorDialogLibraryObjectDetailsViewOptions()
    dialog_options.set_editor_property("show_object_name", False)
    dialog_options.set_editor_property("allow_search", False)
    dialog_options.set_editor_property("allow_resizing", True)
    dialog_options.set_editor_property("min_width", 460)

    accepted = unreal.EditorDialog.show_object_details_view(TITLE, settings, dialog_options)

    if not accepted:
        unreal.log("[JUNTools] Bone display settings cancelled.")
        _ALIVE.remove(settings)
        return None

    new_mode = _to_int(settings.get_editor_property("bone_draw_mode"))
    new_colors = bool(settings.get_editor_property("show_bone_colors"))

    changed = core.apply(bone_draw_mode=new_mode, show_bone_colors=new_colors)
    _report(changed, mode_changed=(new_mode != current_mode))

    _ALIVE.remove(settings)
    return changed


def quick_show_all():
    """다이얼로그 없이 바로 All Hierarchy 로 바꾼다."""
    target = core.BoneDrawMode.ALL_HIERARCHY
    previous = core.set_bone_draw_mode(target)

    changed = []
    if previous != target:
        changed.append(("Bone Draw Mode", core.mode_label(previous), core.mode_label(target)))

    _report(changed, mode_changed=bool(changed))
    return changed

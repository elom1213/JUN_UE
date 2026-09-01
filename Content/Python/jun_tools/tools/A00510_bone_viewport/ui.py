# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-09-01
#
# A00510_bone_viewport - UI.
#
# 뷰포트 툴바의 눈 아이콘 > Bones > (라디오 버튼) 을 타고 들어가지 않고
# 팝업 하나에서 본 표시 모드를 고른다.
#
# 다이얼로그는 `unreal.EditorDialog.show_object_details_view()` 로 만든다.
# 파이썬으로 만든 UObject 의 프로퍼티가 디테일 패널 형태로 그려지므로,
# uenum 을 쓰면 드롭다운이, bool 을 쓰면 체크박스가 된다.
#
# ── Apply 버튼 ────────────────────────────────────────────────────────────
# 파이썬만으로는 모덜리스(non-modal) 창을 띄울 수 없다. 창을 만드는 수단이
# `show_object_details_view()` 하나뿐이고 그건 모달이라, 원래는 OK 를 눌러 창을 닫아야만
# 설정이 적용됐다. 값을 조금씩 바꿔 가며 뷰포트를 확인하려면 매번 메뉴를 다시 눌러야 했다.
#
# 해결: **디테일 패널 안에 버튼을 넣는다.** 인자가 없고 `CallInEditor` 메타가 붙은 UFUNCTION 은
# 디테일 뷰가 알아서 버튼으로 그려 준다(`FObjectDetails::AddCallInEditorMethods`).
# `@unreal.ufunction(meta=...)` 로 만든 파이썬 함수도 똑같은 UFUNCTION 이라 그대로 통한다.
# 이 버튼은 창을 닫지 않으므로 창을 띄워 둔 채 몇 번이고 누를 수 있다.
#
# 버튼의 역할:
#   Apply  : 지금 값을 적용한다. 창은 그대로 떠 있다.  ← 주 경로
#   Reset  : 창을 열었을 때의 값으로 되돌려 적용한다 (Apply 를 잘못 눌렀을 때).
#   OK     : 아직 적용 안 된 값이 있으면 적용하고 닫는다.
#   Cancel : 그냥 닫는다. 이미 Apply 한 것은 되돌리지 않는다 (그건 Reset 의 몫이다).

import unreal

from . import core

TITLE = "JUN Bone Display Settings"

PROP_MODE = "bone_draw_mode"
PROP_COLORS = "show_bone_colors"

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

        # 인자 없음 + CallInEditor="true" → 디테일 뷰가 Category 밑에 버튼으로 그린다.
        @unreal.ufunction(
            meta=dict(
                CallInEditor="true",
                Category="Bone Display",
                DisplayName="Apply",
                ToolTip="Apply the settings above now. This window stays open.",
            )
        )
        def apply(self):
            apply_settings(self)

        @unreal.ufunction(
            meta=dict(
                CallInEditor="true",
                Category="Bone Display",
                DisplayName="Reset",
                ToolTip="Restore the values this window was opened with, and apply them.",
            )
        )
        def reset(self):
            reset_settings(self)

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


def _read(settings):
    """다이얼로그가 지금 보여 주는 값. 디테일 뷰는 편집하는 즉시 오브젝트에 써 넣는다."""
    return (
        _to_int(settings.get_editor_property(PROP_MODE)),
        bool(settings.get_editor_property(PROP_COLORS)),
    )


def _write(settings, mode_enum, mode, colors):
    settings.set_editor_property(PROP_MODE, _to_enum(mode_enum, mode))
    settings.set_editor_property(PROP_COLORS, bool(colors))


def _pending(settings):
    """아직 적용되지 않은 항목의 이름들. 적용 상태의 정본은 PersonaOptions 쪽이다."""
    mode, colors = _read(settings)

    names = []
    if mode != core.get_bone_draw_mode():
        names.append(core.CHANGE_BONE_DRAW_MODE)
    if colors != core.get_show_bone_colors():
        names.append(core.CHANGE_SHOW_BONE_COLORS)
    return names


def _report(changed):
    """무엇이 바뀌었는지, 어떻게 해야 보이는지 Output Log 에 남긴다."""
    if not changed:
        unreal.log("[JUNTools] Bone display: nothing changed.")
        return

    for name, before, after in changed:
        unreal.log("[JUNTools] Bone display: {} : {} -> {}".format(name, before, after))

    if any(name == core.CHANGE_BONE_DRAW_MODE for name, _, _ in changed):
        # 뷰포트는 그릴 본 목록을 캐시해 두고, 그 캐시는 에디터를 열 때 /
        # 프리뷰 메시가 바뀔 때 / 본 선택이 바뀔 때만 다시 계산된다.
        unreal.log(
            "[JUNTools] Applies to skeletal mesh editors opened from now on. "
            "For an editor that is already open, click any bone in the Skeleton Tree to refresh."
        )


def apply_settings(settings):
    """다이얼로그의 현재 값을 적용한다. Apply 버튼과 OK 가 함께 쓴다."""
    mode, colors = _read(settings)
    changed = core.apply(bone_draw_mode=mode, show_bone_colors=colors)
    _report(changed)
    return changed


def reset_settings(settings):
    """창을 열었을 때의 값으로 위젯을 되돌리고, 그 값을 적용한다."""
    original = _ORIGINALS.get(id(settings))
    if original is None:
        unreal.log_warning("[JUNTools] Bone display: nothing to reset to.")
        return []

    _write(settings, _types()[1], *original)
    return apply_settings(settings)


# Reset 이 돌아갈 값. uclass 인스턴스에는 파이썬 속성을 붙일 수 없어 여기에 따로 둔다.
# 키는 id() 지만 오브젝트가 _ALIVE 에 살아 있는 동안만 쓰이므로 id 가 재사용될 일은 없다.
_ORIGINALS = {}


def show():
    """본 표시 설정 팝업을 띄운다."""
    settings_cls, mode_enum = _types()

    settings = settings_cls()
    _ALIVE.append(settings)

    try:
        # 현재 값을 채워서 띄운다. Reset 이 돌아갈 자리도 여기서 기억해 둔다.
        original = (core.get_bone_draw_mode(), core.get_show_bone_colors())
        _write(settings, mode_enum, *original)
        _ORIGINALS[id(settings)] = original

        dialog_options = unreal.EditorDialogLibraryObjectDetailsViewOptions()
        dialog_options.set_editor_property("show_object_name", False)
        dialog_options.set_editor_property("allow_search", False)
        dialog_options.set_editor_property("allow_resizing", True)
        dialog_options.set_editor_property("min_width", 460)

        unreal.log("[JUNTools] Bone display: press Apply to apply without closing the window.")

        accepted = unreal.EditorDialog.show_object_details_view(TITLE, settings, dialog_options)

        if accepted:
            # OK = 남은 변경을 적용하고 닫기. Apply 로 이미 반영했다면 여기서는 아무것도 안 바뀐다.
            return apply_settings(settings)

        # Cancel. Apply 로 이미 적용한 것은 그대로 둔다 - 되돌리려면 Reset 이 있다.
        pending = _pending(settings)
        if pending:
            unreal.log(
                "[JUNTools] Bone display: closed without applying {}.".format(", ".join(pending)))
        else:
            unreal.log("[JUNTools] Bone display settings closed.")
        return []
    finally:
        _ORIGINALS.pop(id(settings), None)
        _ALIVE.remove(settings)


def quick_show_all():
    """다이얼로그 없이 바로 All Hierarchy 로 바꾼다."""
    target = core.BoneDrawMode.ALL_HIERARCHY
    previous = core.set_bone_draw_mode(target)

    changed = []
    if previous != target:
        changed.append(
            (core.CHANGE_BONE_DRAW_MODE, core.mode_label(previous), core.mode_label(target)))

    _report(changed)
    return changed

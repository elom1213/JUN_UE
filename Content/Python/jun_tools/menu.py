# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-14
#
# Tools > JUN 메뉴 등록.
#
# 툴이 늘어나도 Tools 메뉴가 지저분해지지 않도록, 최상위에는 "JUN" 하위 메뉴
# 하나만 만들고 그 안에서 섹션으로 나눈다.
#
# 등록/해제는 전부 owner 이름(version.MENU_OWNER)으로 묶어서 처리한다.
# → register() 를 몇 번 호출해도 메뉴가 중복되지 않는다.

import unreal

from . import registry, version

# 레벨 에디터 상단 Tools 메뉴. 5.x 의 UToolMenus 이름 규칙.
PARENT_MENU = "LevelEditor.MainMenu.Tools"

# Tools 메뉴 안에서 우리가 차지할 섹션 / 하위 메뉴
PARENT_SECTION = "JUN"
SUB_MENU_NAME = "JUNTools"
SUB_MENU_LABEL = "JUN"
SUB_MENU_TOOLTIP = "JUN personal tool suite"


def _make_entry(name, label, tooltip, command):
    """파이썬 명령을 실행하는 메뉴 항목 하나를 만든다."""
    entry = unreal.ToolMenuEntry(
        name=name,
        type=unreal.MultiBlockType.MENU_ENTRY,
    )
    entry.set_label(label)
    entry.set_tool_tip(tooltip)
    entry.set_string_command(
        type=unreal.ToolMenuStringCommandType.PYTHON,
        custom_type="",
        string=command,
    )
    return entry


def register():
    """Tools > JUN 메뉴를 (재)등록한다."""
    menus = unreal.ToolMenus.get()

    # 이전 등록분을 먼저 지운다. 리로드 시 항목이 두 번 생기는 것을 막는다.
    menus.unregister_owner_by_name(version.MENU_OWNER)

    # extend_menu 는 아직 만들어지지 않은 메뉴여도 안전하게 확장 지점을 잡아준다.
    tools_menu = menus.extend_menu(PARENT_MENU)
    tools_menu.add_section(PARENT_SECTION, PARENT_SECTION)

    sub_menu = tools_menu.add_sub_menu(
        version.MENU_OWNER,
        PARENT_SECTION,
        SUB_MENU_NAME,
        SUB_MENU_LABEL,
        SUB_MENU_TOOLTIP,
    )

    # --- 툴 목록: registry.TOOLS 를 그대로 그린다 ---
    for section, specs in registry.sections():
        sub_menu.add_section(section, section)
        for spec in specs:
            sub_menu.add_menu_entry(
                section,
                _make_entry(
                    name=spec.tool_id,
                    label=spec.label,
                    tooltip=spec.tooltip,
                    command='import jun_tools; jun_tools.run("{}")'.format(spec.tool_id),
                ),
            )

    # --- 개발용 항목 ---
    sub_menu.add_section("Dev", "Developer")
    sub_menu.add_menu_entry(
        "Dev",
        _make_entry(
            name="ReloadJUNTools",
            label="Reload JUN Tools",
            tooltip="Re-read all JUN Tools python modules without restarting the editor.",
            command="import jun_tools; jun_tools.reload_all()",
        ),
    )

    menus.refresh_all_widgets()

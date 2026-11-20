# -*- coding: utf-8 -*-
# 헤드리스 검증 - Tools > JUN 메뉴 등록 (v01.14: 섹션을 Tools 메뉴 맨 위 FIRST 로).
# 커맨드렛은 메뉴를 그리지 않으므로 **실제 순서는 에디터 화면으로만** 확인된다. 여기서는 등록이 에러 없이 되는지만 본다.
import traceback

import unreal

RESULTS = []


def check(name, condition, detail=""):
    RESULTS.append(bool(condition))
    unreal.log("[MENU-VERIFY] {} {} {}".format("PASS" if condition else "FAIL", name, detail))


try:
    from jun_tools import menu
    check("ToolMenuInsertType.FIRST exists", hasattr(unreal.ToolMenuInsertType, "FIRST"))
    check("Tools menu is registered", unreal.ToolMenus.get().find_menu(menu.PARENT_MENU) is not None)
    for attempt in (1, 2):              # 두 번 = 리로드처럼 다시 등록해도 깨지지 않는지
        menu.register()
        check("register() runs without error (#{})".format(attempt), True)
    check("JUN sub menu exists", unreal.ToolMenus.get().find_menu(
        menu.PARENT_MENU + "." + menu.SUB_MENU_NAME) is not None)
except Exception:
    check("menu registration", False, traceback.format_exc())

unreal.log("[MENU-VERIFY] RESULT {}/{}".format(sum(RESULTS), len(RESULTS)))

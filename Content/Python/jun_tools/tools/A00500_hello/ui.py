# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-14
#
# A00500_hello - UI.
#
# UI 는 얇게 유지한다. 여기서 하는 일은 "물어보고 core 를 부르는 것"뿐이다.
#
# 다이얼로그는 EditorScriptingUtilities 플러그인의 UEditorDialogLibrary 를 쓴다
# (파이썬 이름은 unreal.EditorDialog). C++ 컴파일 없이 쓸 수 있는 모달 팝업이다.
# 입력 필드가 필요한 툴로 넘어갈 때는 같은 라이브러리의
# show_object_details_view() 로 확장한다 (Docs 참고).

import unreal

from . import core

TITLE = "JUN Hello Tool"
MESSAGE = "Press OK to print '{}' to the Output Log.".format(core.DEFAULT_MESSAGE)


def show():
    """팝업을 띄우고, OK 를 누르면 Output Log 에 Hello 를 찍는다."""
    result = unreal.EditorDialog.show_message(
        TITLE,
        MESSAGE,
        unreal.AppMsgType.OK_CANCEL,
        unreal.AppReturnType.CANCEL,  # -unattended 로 돌 때의 기본값
    )

    if result != unreal.AppReturnType.OK:
        unreal.log("[JUNTools] Hello Tool cancelled.")
        return None

    return core.say_hello()

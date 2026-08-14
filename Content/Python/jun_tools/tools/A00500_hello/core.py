# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-14
#
# A00500_hello - 로직.
#
# core 에는 UI 코드를 넣지 않는다. 여기 있는 함수는 다이얼로그 없이도
# (파이썬 콘솔 / 커맨드렛 / 배치)에서 그대로 호출할 수 있어야 한다.

import unreal

DEFAULT_MESSAGE = "Hello"


def say_hello(message=DEFAULT_MESSAGE):
    """Output Log 에 메시지를 찍고 그대로 돌려준다."""
    unreal.log(message)
    return message

# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-14
#
# JUNTools plugin entry point.
#
# 언리얼은 활성화된 플러그인의 `Content/Python` 폴더를 sys.path 에 추가하고,
# 그 안의 `init_unreal.py` 를 에디터 시작 시 자동 실행한다.
# 마야에서 `__dragDrop_A000XX.py` 로 셸프 버튼을 설치하던 것과 같은 자리다.
#
# 여기서는 메뉴만 등록하고 실제 툴 모듈은 건드리지 않는다(지연 로딩).
# 툴 하나가 임포트 에러를 내도 에디터 부팅과 다른 툴 메뉴가 죽지 않게 하기 위함.

import traceback

import unreal


def _startup():
    from jun_tools import menu, version

    menu.register()
    unreal.log("[JUNTools] {} loaded. See Tools > JUN.".format(version.VERSION))


try:
    _startup()
except Exception:
    # 부팅 중 예외를 삼키지 않고 로그로 남긴다(에디터는 계속 뜨게 둔다).
    unreal.log_error("[JUNTools] startup failed:\n{}".format(traceback.format_exc()))

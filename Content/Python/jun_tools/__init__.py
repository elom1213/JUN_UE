# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-14
#
# JUNTools 공용 진입점.
#
# 메뉴가 실행하는 명령은 전부 `jun_tools.run("<tool_id>")` 한 줄로 통일한다.
# (마야에서 셸프 버튼이 `tools.A000XX_name.run(True)` 를 부르던 것과 같은 구조)

import importlib
import sys
import traceback

from . import config, registry, version

__all__ = ["run", "reload_all", "VERSION"]

VERSION = version.VERSION


def _purge(prefix):
    """sys.modules 에서 prefix 로 시작하는 모듈을 전부 제거한다."""
    doomed = [n for n in sys.modules if n == prefix or n.startswith(prefix + ".")]
    for name in doomed:
        del sys.modules[name]
    return doomed


def run(tool_id):
    """tool_id 에 해당하는 툴을 연다. 메뉴에서 호출하는 유일한 함수."""
    import unreal

    try:
        spec = registry.find(tool_id)

        if config.DEV_MODE:
            # 툴 패키지만 비운다. jun_tools 자신은 건드리지 않는다
            # (지금 이 함수가 그 안에서 돌고 있으므로).
            _purge("jun_tools.tools.{}".format(tool_id))

        module = importlib.import_module(spec.module)
        return getattr(module, spec.entry)()

    except Exception:
        unreal.log_error("[JUNTools] '{}' failed:\n{}".format(tool_id, traceback.format_exc()))
        return None


def reload_all():
    """jun_tools 패키지 전체를 다시 읽고 메뉴를 재등록한다(에디터 재시작 없이)."""
    import unreal

    try:
        _purge("jun_tools")

        fresh = importlib.import_module("jun_tools")
        menu = importlib.import_module("jun_tools.menu")
        menu.register()

        unreal.log("[JUNTools] reloaded ({}).".format(fresh.VERSION))
    except Exception:
        unreal.log_error("[JUNTools] reload failed:\n{}".format(traceback.format_exc()))

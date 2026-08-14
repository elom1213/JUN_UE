# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-14
#
# 툴 목록(레지스트리).
#
# 새 툴을 추가할 때 손대는 곳은 여기 한 군데다.
#   1. `jun_tools/tools/A00NNN_<name>/` 폴더를 만들고 core.py / ui.py 를 채운다
#   2. 아래 TOOLS 에 ToolSpec 을 한 줄 추가한다
# 메뉴는 이 목록을 그대로 그린다.


class ToolSpec(object):
    """메뉴 한 줄 + 진입점 정보."""

    def __init__(self, tool_id, label, module, entry="show", section="Test", tooltip=""):
        self.tool_id = tool_id      # 고유 ID (폴더 이름과 동일하게 유지)
        self.label = label          # 메뉴에 보이는 이름
        self.module = module        # 진입점이 있는 모듈 경로
        self.entry = entry          # 그 모듈에서 호출할 함수 이름
        self.section = section      # 메뉴 섹션(그룹) 이름
        self.tooltip = tooltip


# 섹션 표시 순서. 여기 없는 섹션은 뒤에 알파벳 순으로 붙는다.
SECTION_ORDER = ["Test", "Rigging", "Animation", "Asset"]


TOOLS = [
    ToolSpec(
        tool_id="A00500_hello",
        label="Hello Tool",
        module="jun_tools.tools.A00500_hello.ui",
        entry="show",
        section="Test",
        tooltip="Open a dialog and print 'Hello' to the Output Log.",
    ),
]


def find(tool_id):
    """tool_id 로 ToolSpec 을 찾는다. 없으면 KeyError."""
    for spec in TOOLS:
        if spec.tool_id == tool_id:
            return spec
    raise KeyError("Unknown tool id: {}".format(tool_id))


def sections():
    """(section, [ToolSpec, ...]) 목록을 표시 순서대로 돌려준다."""
    grouped = {}
    for spec in TOOLS:
        grouped.setdefault(spec.section, []).append(spec)

    ordered = [s for s in SECTION_ORDER if s in grouped]
    ordered += sorted(s for s in grouped if s not in SECTION_ORDER)
    return [(s, grouped[s]) for s in ordered]

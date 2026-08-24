# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-24
#
# 툴 목록(레지스트리).
#
# 새 툴을 추가할 때 손대는 곳은 여기 한 군데다.
#   1. `jun_tools/tools/A00NNN_<name>/` 폴더를 만들고 core.py / ui.py 를 채운다
#   2. 아래 TOOLS 에 ToolSpec 을 한 줄 추가한다
# 메뉴는 이 목록을 그대로 그린다.


class ToolSpec(object):
    """메뉴 한 줄 + 진입점 정보."""

    def __init__(self, tool_id, label, module, entry="show", section="Test", tooltip="",
                 package=None):
        self.tool_id = tool_id      # 메뉴 항목의 고유 ID
        self.label = label          # 메뉴에 보이는 이름
        self.module = module        # 진입점이 있는 모듈 경로
        self.entry = entry          # 그 모듈에서 호출할 함수 이름
        self.section = section      # 메뉴 섹션(그룹) 이름
        self.tooltip = tooltip
        # 툴 폴더 이름. 보통 tool_id 와 같지만, 한 툴이 메뉴 항목을 여러 개 가질 때
        # (예: 다이얼로그 + 원클릭 단축 실행) 나머지 항목이 같은 폴더를 가리키게 한다.
        # DEV_MODE 리로드는 이 값을 기준으로 모듈을 비운다.
        self.package = package or tool_id


# 섹션 표시 순서. 여기 없는 섹션은 뒤에 알파벳 순으로 붙는다.
SECTION_ORDER = ["Test", "Rigging", "Animation", "Cinematic", "Asset"]


TOOLS = [
    ToolSpec(
        tool_id="A00500_hello",
        label="Hello Tool",
        module="jun_tools.tools.A00500_hello.ui",
        entry="show",
        section="Test",
        tooltip="Open a dialog and print 'Hello' to the Output Log.",
    ),
    ToolSpec(
        tool_id="A00510_bone_viewport",
        label="Bone Display Settings...",
        module="jun_tools.tools.A00510_bone_viewport.ui",
        entry="show",
        section="Animation",
        tooltip="Set the skeletal mesh viewport bone draw mode in one dialog.",
    ),
    ToolSpec(
        tool_id="A00510_bone_viewport_all",
        package="A00510_bone_viewport",
        label="Show All Bones",
        module="jun_tools.tools.A00510_bone_viewport.ui",
        entry="quick_show_all",
        section="Animation",
        tooltip="Set bone draw mode to All Hierarchy right away, without a dialog.",
    ),
    ToolSpec(
        tool_id="A00520_cinematic_sequence_builder",
        label="Cinematic Sequence Builder...",
        module="jun_tools.tools.A00520_cinematic_sequence_builder.ui",
        entry="show",
        section="Cinematic",
        tooltip="Create the MSEQ / CSEQ / SSEQ sequencer structure for one scene, "
                "wired and named to the SOP.",
    ),
    ToolSpec(
        tool_id="A00520_cinematic_validate",
        package="A00520_cinematic_sequence_builder",
        label="Validate Cinematic Structure",
        module="jun_tools.tools.A00520_cinematic_sequence_builder.ui",
        entry="validate_selected",
        section="Cinematic",
        tooltip="Check the scene folder selected in the Content Browser against the SOP. "
                "Creates and changes nothing.",
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

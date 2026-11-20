# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-11-20
#
# 공용 - EUW 탭 안의 화면을 파이썬으로 조립하는 헬퍼.
#
# EUW 루트에 변수로 노출한 VerticalBox 하나(`Root`)만 두고, 화면은 실행 중에
# `unreal.new_object(<위젯>)` + `PanelWidget.add_child()` 로 만든다 (A00530 에서 시작해 공용으로 옮김).
#
# 꼭 지킬 것 두 가지 (실측 2026-11-20):
#   1) **`EditorUtility*` 위젯을 쓴다.** `unreal.Button / EditableTextBox / ComboBoxString` 은 게임 스타일
#      (글꼴 24, 밝은 입력칸)이다. Blutility 의 `EditorUtilityButton` 등은 생성자에서 에디터 스타일을 입힌다.
#      TextBlock 은 에디터 판이 없어서 `editor_font()` 를 입힌다.
#   2) **콜백은 `connect()` 로 단다.** `add_callable` 의 중계 오브젝트(UPythonCallableForDelegate)는 파이썬이
#      참조를 쥔 위젯의 델리게이트를 통해서만 GC 에서 지켜진다(FPyReferenceCollector). 위젯을 버리면 에디터의
#      주기 GC 뒤 콜백이 소리 없이 끊긴다. `connect()` 는 위젯을 `keep` 리스트에 넣어 붙잡는다.
#   + 델리게이트는 기본값 인자까지 인자 수로 센다 — `lambda p=x:` 는 거부된다. 값은 클로저로 묶을 것.
#
# UI 문자열은 영어만 (전역 규칙 6장).

import unreal

COLOR_TEXT = unreal.LinearColor(0.85, 0.85, 0.85, 1.0)
COLOR_DIM = unreal.LinearColor(0.5, 0.5, 0.5, 1.0)
COLOR_ERROR = unreal.LinearColor(1.0, 0.3, 0.3, 1.0)
COLOR_PANEL = unreal.LinearColor(0.012, 0.012, 0.012, 1.0)     # 원본 "ToolPanel.GroupBorder" 비슷한 어두운 박스
COLOR_LIST = unreal.LinearColor(0.006, 0.006, 0.006, 1.0)      # 리스트 바탕
COLOR_HOVER = unreal.LinearColor(1.0, 1.0, 1.0, 0.06)
COLOR_SELECTED = unreal.LinearColor(0.2, 0.45, 1.0, 0.35)
COLOR_CLEAR = unreal.LinearColor(1.0, 1.0, 1.0, 0.0)

FALLBACK_FONT_SIZE = 9

_FONT = {}


def editor_font(bold=False):
    """에디터 기본 글꼴(SlateFontInfo). 에디터 입력칸 스타일의 글꼴을 빌려 온다(크기 9)."""
    key = "bold" if bold else "regular"
    if key in _FONT:
        return _FONT[key]

    font = None
    try:
        style = unreal.new_object(unreal.EditorUtilityEditableTextBox).get_editor_property("widget_style")
        for path in (("text_style", "font"), ("font",)):
            try:
                value = style
                for name in path:
                    value = value.get_editor_property(name)
                if value.get_editor_property("font_object") is not None:
                    font = value
                    break
            except Exception:
                continue
    except Exception:
        font = None

    if font is None:
        font = unreal.new_object(unreal.TextBlock).get_editor_property("font")
        font.set_editor_property("size", FALLBACK_FONT_SIZE)

    # get_editor_property 는 구조체 사본을 돌려준다 - 고쳐도 원본 스타일은 그대로다.
    if bold:
        font.set_editor_property("typeface_font_name", "Bold")
    _FONT[key] = font
    return font


# ---------------------------------------------------------------------------
# 콜백
# ---------------------------------------------------------------------------

def connect(keep, widget, delegate_name, callback):
    """widget.<delegate_name> 에 callback 을 달고 widget 을 keep 리스트에 넣어 GC 에서 지킨다."""
    getattr(widget, delegate_name).add_callable(callback)
    keep.append(widget)
    return widget


def bind(function, *args):
    """인자 없는 이벤트(on_clicked · on_hovered ...)용 콜백. 인자를 클로저로 묶는다.

    델리게이트는 파이썬 함수의 인자 수를 시그니처와 정확히 맞춰 보므로(기본값 인자 · *args 포함)
    반환하는 함수는 인자를 하나도 받지 않는다.
    """
    def _call():
        return function(*args)
    return _call


# ---------------------------------------------------------------------------
# 위젯
# ---------------------------------------------------------------------------

def color(linear):
    return unreal.SlateColor(specified_color=linear)


def text(label, tint=None, bold=False):
    widget = unreal.new_object(unreal.TextBlock)
    widget.set_font(editor_font(bold))
    widget.set_text(label)
    widget.set_color_and_opacity(color(tint or COLOR_TEXT))
    return widget


def button(keep, label, callback, tooltip="", align="center"):
    """align: "center" | "left" (메뉴 항목처럼 왼쪽 정렬)."""
    widget = unreal.new_object(unreal.EditorUtilityButton)
    slot = widget.add_child(text(label))
    slot.set_horizontal_alignment(unreal.HorizontalAlignment.H_ALIGN_LEFT if align == "left"
                                  else unreal.HorizontalAlignment.H_ALIGN_CENTER)
    slot.set_vertical_alignment(unreal.VerticalAlignment.V_ALIGN_CENTER)
    if tooltip:
        widget.set_tool_tip_text(tooltip)
    return connect(keep, widget, "on_clicked", callback)


def text_box(hint="", value=""):
    widget = unreal.new_object(unreal.EditorUtilityEditableTextBox)
    if hint:
        widget.set_hint_text(hint)
    if value:
        widget.set_text(value)
    return widget


def combo(options, index=0):
    widget = unreal.new_object(unreal.EditorUtilityComboBoxString)
    try:
        widget.set_editor_property("font", editor_font())
    except Exception:
        pass
    # 글자색: UComboBoxString 생성자가 ForegroundColor 를 **게임 스타일** 글자색(검정)으로 정한 뒤,
    # EditorUtilityComboBoxString 은 배경 스타일만 에디터 것으로 바꾸고 글자색은 그대로 둔다
    # → 어두운 배경에 검은 글자(고른 값이 안 보임). 위젯이 그려지기 전에만 바꿀 수 있다(그 뒤엔 무시).
    try:
        widget.set_editor_property("foreground_color", color(COLOR_TEXT))
    except Exception:
        pass
    for option in options:
        widget.add_option(option)
    widget.set_selected_index(index)
    return widget


def check_box(label, checked=False):
    """체크박스 + 오른쪽 글자. 반환: (HorizontalBox, CheckBox)."""
    box = unreal.new_object(unreal.EditorUtilityCheckBox)
    box.set_is_checked(bool(checked))
    return row(fixed(box), fixed(text(label))), box


# ---------------------------------------------------------------------------
# 배치
# ---------------------------------------------------------------------------

def size(slot, weight):
    """박스 슬롯 크기. weight > 0 = 남는 공간을 그 비율로 채움, 0 = 내용 크기만큼."""
    child_size = unreal.SlateChildSize()
    child_size.set_editor_property("value", float(weight) if weight else 1.0)
    child_size.set_editor_property(
        "size_rule", unreal.SlateSizeRule.FILL if weight else unreal.SlateSizeRule.AUTOMATIC)
    slot.set_size(child_size)
    return slot


def pad(slot, left=2.0, top=1.0, right=2.0, bottom=1.0):
    slot.set_padding(unreal.Margin(left, top, right, bottom))
    return slot


def middle(slot):
    slot.set_vertical_alignment(unreal.VerticalAlignment.V_ALIGN_CENTER)
    return slot


class Cell(object):
    """row() / column() 에 넣는 한 칸: 위젯 + 크기(0 = 내용만큼) + 여백."""

    def __init__(self, widget, weight=0.0, padding=(2.0, 1.0, 2.0, 1.0)):
        self.widget = widget
        self.weight = weight
        self.padding = padding


def fixed(widget, padding=(2.0, 1.0, 2.0, 1.0)):
    return Cell(widget, 0.0, padding)


def stretch(widget, weight=1.0, padding=(2.0, 1.0, 2.0, 1.0)):
    return Cell(widget, weight, padding)


def _cell(item):
    if isinstance(item, Cell):
        return item
    widget, weight = item
    return Cell(widget, weight)


def row(*cells):
    """가로로 놓는다. 칸은 Cell 또는 (widget, weight)."""
    box = unreal.new_object(unreal.HorizontalBox)
    for item in cells:
        cell = _cell(item)
        slot = middle(pad(box.add_child(cell.widget), *cell.padding))
        size(slot, cell.weight)
    return box


def column(*cells):
    """세로로 놓는다. 칸은 Cell 또는 (widget, weight)."""
    box = unreal.new_object(unreal.VerticalBox)
    for item in cells:
        cell = _cell(item)
        slot = pad(box.add_child(cell.widget), *cell.padding)
        size(slot, cell.weight)
    return box


def panel(content, tint=None, padding=5.0):
    """원본 SBorder("ToolPanel.GroupBorder") 처럼 어두운 박스에 담는다."""
    border = unreal.new_object(unreal.Border)
    border.set_brush_color(tint or COLOR_PANEL)
    border.set_padding(unreal.Margin(padding, padding, padding, padding))
    border.set_content(content)
    return border


def add(parent, widget, weight=0.0, padding=(2.0, 1.0, 2.0, 1.0)):
    """VerticalBox / HorizontalBox 에 칸 하나를 더한다."""
    slot = pad(parent.add_child(widget), *padding)
    size(slot, weight)
    return slot

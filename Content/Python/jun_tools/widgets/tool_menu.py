# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-11-20
#
# 공용 - 모든 툴 메뉴 바에 공통으로 들어가는 항목(레지스트리) + 툴 이름 + 클립보드.
#
# 마야 `Framework/core/tool_menu.py` 의 언리얼 대응. 여기 한 줄 더하면 `MenuBar`(menu_bar.py)를 쓰는
# 모든 툴의 메뉴에 그 항목이 생긴다. UMG 를 import 하지 않는다 - 헤드리스에서도 그대로 쓸 수 있다.
#
#     register_common_item("Help", MenuItemSpec("Open Docs", open_docs, "Open this tool's guide"))
#
# 클립보드: 언리얼 파이썬 API 에는 클립보드 함수가 없다(5.4 · 5.7 실측). Windows 클립보드를 ctypes 로 직접 쓴다.
# 다른 플러그인과 `ctypes.windll` 의 argtypes 설정이 엉키지 않게 DLL 을 따로 연다.
#
# UI 문자열 · 로그는 영어만 (전역 규칙 6장).

import sys

import unreal

TOOLS_PACKAGE = "tools"          # jun_tools.tools.<툴 폴더>
TAB_PATH_SEPARATOR = " / "        # 마야와 같은 구분자 - `A00530_jun_renamer / Copy Name`


# ======================================================================
# 툴 이름
# ======================================================================

def tool_name_from_module(module_name):
    """모듈 이름에서 툴 폴더 이름 - `jun_tools.tools.A00530_jun_renamer.ui_tab` → `A00530_jun_renamer`."""
    parts = (module_name or "").split(".")
    for i, part in enumerate(parts[:-1]):
        if part == TOOLS_PACKAGE:
            return parts[i + 1]
    return None


def tool_tab_path_text(tool_name, tab_path):
    """`툴 이름 / 탭 / 안쪽 탭`. 탭이 없으면 툴 이름만."""
    return TAB_PATH_SEPARATOR.join([tool_name] + [label for label in (tab_path or []) if label])


# ======================================================================
# 클립보드 (Windows)
# ======================================================================

CF_UNICODETEXT = 13
GMEM_MOVEABLE = 0x0002

_WIN = {}


def _win():
    """user32 / kernel32 를 이 모듈 전용으로 열고 시그니처를 맞춘다 (64 비트 핸들 잘림 방지)."""
    if _WIN:
        return _WIN["user32"], _WIN["kernel32"]
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

    user32.CreateWindowExW.restype = wintypes.HWND
    user32.CreateWindowExW.argtypes = [wintypes.DWORD, wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.DWORD,
                                       ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                                       wintypes.HWND, wintypes.HMENU, wintypes.HINSTANCE, wintypes.LPVOID]
    user32.DestroyWindow.argtypes = [wintypes.HWND]
    user32.OpenClipboard.argtypes = [wintypes.HWND]
    user32.OpenClipboard.restype = wintypes.BOOL
    user32.CloseClipboard.restype = wintypes.BOOL
    user32.EmptyClipboard.restype = wintypes.BOOL
    user32.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
    user32.SetClipboardData.restype = wintypes.HANDLE
    user32.GetClipboardData.argtypes = [wintypes.UINT]
    user32.GetClipboardData.restype = wintypes.HANDLE
    kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
    kernel32.GlobalAlloc.restype = wintypes.HGLOBAL
    kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalLock.restype = wintypes.LPVOID
    kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalFree.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalFree.restype = wintypes.HGLOBAL

    _WIN["user32"], _WIN["kernel32"] = user32, kernel32
    return user32, kernel32


class _Clipboard(object):
    """with 블록 동안 클립보드를 연다. 소유 창으로 숨은 STATIC 창을 하나 만든다
    (NULL 소유로 열면 EmptyClipboard 뒤 SetClipboardData 가 실패할 수 있다 - MSDN)."""

    def __init__(self):
        self.user32, self.kernel32 = _win()
        self.hwnd = None
        self.opened = False

    def __enter__(self):
        self.hwnd = self.user32.CreateWindowExW(0, u"STATIC", None, 0, 0, 0, 0, 0, None, None, None, None)
        import time
        for _ in range(10):                      # 다른 프로그램이 잠깐 쥐고 있을 수 있다
            if self.user32.OpenClipboard(self.hwnd):
                self.opened = True
                break
            time.sleep(0.01)
        return self

    def __exit__(self, *exc):
        if self.opened:
            self.user32.CloseClipboard()
        if self.hwnd:
            self.user32.DestroyWindow(self.hwnd)
        return False


def get_clipboard_text():
    """클립보드 글자. 없거나 못 읽으면 None."""
    if sys.platform != "win32":
        return None
    import ctypes
    try:
        with _Clipboard() as clip:
            if not clip.opened:
                return None
            handle = clip.user32.GetClipboardData(CF_UNICODETEXT)
            if not handle:
                return None
            pointer = clip.kernel32.GlobalLock(handle)
            if not pointer:
                return None
            try:
                return ctypes.wstring_at(pointer)
            finally:
                clip.kernel32.GlobalUnlock(handle)
    except Exception:
        return None


def copy_text_to_clipboard(text):
    """클립보드에 글자를 넣는다. 성공(다시 읽어 같음)하면 True."""
    if sys.platform != "win32" or text is None:
        return False
    import ctypes
    data = (u"{}".format(text) + u"\0").encode("utf-16-le")
    try:
        with _Clipboard() as clip:
            if not clip.opened:
                return False
            clip.user32.EmptyClipboard()
            handle = clip.kernel32.GlobalAlloc(GMEM_MOVEABLE, len(data))
            if not handle:
                return False
            pointer = clip.kernel32.GlobalLock(handle)
            if not pointer:
                clip.kernel32.GlobalFree(handle)
                return False
            ctypes.memmove(pointer, data, len(data))
            clip.kernel32.GlobalUnlock(handle)
            if not clip.user32.SetClipboardData(CF_UNICODETEXT, handle):
                clip.kernel32.GlobalFree(handle)      # 성공하면 시스템 소유라 풀면 안 된다
                return False
    except Exception:
        return False
    return get_clipboard_text() == text


# ======================================================================
# 메뉴 항목
# ======================================================================

def _log(message):
    unreal.log(message)


class MenuContext(object):
    """항목 콜백이 받는 정보.

    tool_name : 툴 폴더 이름 (못 찾았으면 None)
    log       : log(message) - 메뉴 바가 Output Log + 메뉴 바 오른쪽 글자로 보낸다
    tab_path  : 지금 보이는 탭(모드) 라벨들. 함수를 주면 **누를 때** 부른다.
    """

    def __init__(self, tool_name=None, log=None, tab_path=None):
        self.tool_name = tool_name
        self.log = log or _log
        self._tab_path = tab_path

    @property
    def tab_path(self):
        source = self._tab_path
        if callable(source):
            try:
                source = source()
            except Exception:
                source = None
        return [str(label) for label in (source or []) if label]


class MenuItemSpec(object):
    """메뉴 항목 하나. callback(ctx: MenuContext) 을 부른다."""

    def __init__(self, label, callback, tooltip=""):
        self.label = label
        self.callback = callback
        self.tooltip = tooltip


def copy_tool_name(ctx):
    """툴 폴더 이름을 클립보드로 - `A00530_jun_renamer`."""
    if not ctx.tool_name:
        ctx.log("[Copy Tool Name] Could not find the tool folder name.")
        return False
    if not copy_text_to_clipboard(ctx.tool_name):
        ctx.log("[Copy Tool Name] Could not access the clipboard.")
        return False
    ctx.log("[Copy Tool Name] Copied to clipboard : {0}".format(ctx.tool_name))
    return True


def copy_tool_name_with_tabs(ctx):
    """툴 폴더 이름 + 지금 보이는 탭(모드) - `A00530_jun_renamer / Copy Name`."""
    label = "Copy Tool Name + Tabs"
    if not ctx.tool_name:
        ctx.log("[{0}] Could not find the tool folder name.".format(label))
        return False
    tab_path = ctx.tab_path
    text = tool_tab_path_text(ctx.tool_name, tab_path)
    if not copy_text_to_clipboard(text):
        ctx.log("[{0}] Could not access the clipboard.".format(label))
        return False
    suffix = "" if tab_path else " (no visible tabs)"
    ctx.log("[{0}] Copied to clipboard : {1}{2}".format(label, text, suffix))
    return True


# [(메뉴 제목, [MenuItemSpec, ...]), ...] - 순서 = 메뉴 바 순서 · 메뉴 안 순서. 마야와 같은 항목.
COMMON_MENUS = [
    ("Help", [
        MenuItemSpec("Copy Tool Name", copy_tool_name,
                     "Copy this tool's folder name (e.g. A00530_jun_renamer) to the clipboard"),
        MenuItemSpec("Copy Tool Name + Tabs", copy_tool_name_with_tabs,
                     "Copy the tool name and the mode/tab you are looking at "
                     "(e.g. A00530_jun_renamer / Copy Name) to the clipboard"),
    ]),
]


def common_menus():
    """공통 메뉴 사본 [(제목, [MenuItemSpec])]."""
    return [(title, list(items)) for title, items in COMMON_MENUS]


def register_common_item(menu_title, spec):
    """공통 항목을 더한다. 같은 label 이 있으면 교체(리로드 안전). 이미 열린 탭에는 다시 열 때 반영."""
    for title, items in COMMON_MENUS:
        if title == menu_title:
            for i, item in enumerate(items):
                if item.label == spec.label:
                    items[i] = spec
                    return
            items.append(spec)
            return
    COMMON_MENUS.append((menu_title, [spec]))

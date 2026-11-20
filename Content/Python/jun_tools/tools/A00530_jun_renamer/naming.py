# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-11-20
#
# A00530 JUN_Renamer - 이름 문자열 규칙 (순수 파이썬, unreal 비의존).
#
# 이 모듈은 "문자열 → 문자열" 만 다룬다. 에셋을 찾거나 바꾸는 일은 core.py 가 한다.
# 그래서 언리얼 없이 일반 파이썬으로도 테스트할 수 있다.
#
# 원본 출처
#   - MANUEditor `SMANUAssetRenamerWidget::GenerateNewName / ApplyTextOperations` (C++ Slate)
#       찾기/바꾸기(어디서든 · 접두 · 접미) → 접두사 → 접미사 → 텍스트 정리
#   - Maya_Python A00330_NamingTool
#       Quick Rename > Selection 의 `-1 Front` / `-1 Rear` (trim_front / trim_rear)
#       Copy Name 의 Prefix + (Search/Replace 한) Base 이름 + Set suffix

import re

# 언리얼 에셋 이름에 쓸 수 없는 글자 (INVALID_OBJECTNAME_CHARACTERS 와 같다).
# 공백도 여기 들어간다 - 에셋 이름에 공백이 있으면 엔진이 이름 변경을 거부한다.
INVALID_NAME_CHARACTERS = "\"' ,/.:|&!~\n\r\t@#(){}[]=;^%$`"

# 찾기/바꾸기를 어디에 걸지 (원본 ESearchMatchMode)
MATCH_ANYWHERE = 0
MATCH_PREFIX = 1
MATCH_SUFFIX = 2

MATCH_LABELS = {
    MATCH_ANYWHERE: "anywhere",
    MATCH_PREFIX: "prefix only",
    MATCH_SUFFIX: "suffix only",
}


# ---------------------------------------------------------------------------
# 비교 헬퍼 - 원본 FString 함수의 기본값은 대소문자 무시(ESearchCase::IgnoreCase)다.
# ---------------------------------------------------------------------------

def starts_with(text, part, case_sensitive=False):
    if case_sensitive:
        return text.startswith(part)
    return text.lower().startswith(part.lower())


def ends_with(text, part, case_sensitive=False):
    if case_sensitive:
        return text.endswith(part)
    return text.lower().endswith(part.lower())


def equals(a, b, case_sensitive=False):
    if case_sensitive:
        return a == b
    return a.lower() == b.lower()


# ---------------------------------------------------------------------------
# 개별 연산
# ---------------------------------------------------------------------------

def trim(name, front=0, rear=0):
    """앞에서 front 글자, 뒤에서 rear 글자를 지운다.

    A00330 Quick Rename 의 `-1 Front` / `-1 Rear` 를 횟수로 일반화한 것이다.
    버튼을 한 번 누를 때마다 횟수가 1 씩 오른다(ui.py). 다 지워지면 빈 문자열 -
    호출하는 쪽이 `invalid_reason()` 으로 걸러낸다.
    """
    front = max(0, int(front or 0))
    rear = max(0, int(rear or 0))
    if front + rear >= len(name):
        return ""
    return name[front:len(name) - rear]


def search_replace(name, search, replace, mode=MATCH_ANYWHERE, case_sensitive=False):
    """search 를 replace 로 바꾼다. 글자 그대로(정규식 아님).

    - MATCH_ANYWHERE : 이름 안의 search 를 **전부** 바꾼다
    - MATCH_PREFIX   : 이름이 search 로 시작할 때 그 앞부분만 바꾼다
    - MATCH_SUFFIX   : 이름이 search 로 끝날 때 그 뒷부분만 바꾼다
    """
    if not search:
        return name

    if mode == MATCH_PREFIX:
        if starts_with(name, search, case_sensitive):
            return replace + name[len(search):]
        return name

    if mode == MATCH_SUFFIX:
        if ends_with(name, search, case_sensitive):
            return name[:len(name) - len(search)] + replace
        return name

    flags = 0 if case_sensitive else re.IGNORECASE
    # 치환 문자열을 함수로 넘겨야 replace 안의 `\1` 같은 글자가 그대로 들어간다.
    return re.sub(re.escape(search), lambda _match: replace, name, flags=flags)


def add_prefix(name, prefix, case_sensitive=False):
    """이미 prefix 로 시작하면 다시 붙이지 않는다 (원본과 같다)."""
    if prefix and not starts_with(name, prefix, case_sensitive):
        return prefix + name
    return name


def add_suffix(name, suffix, case_sensitive=False):
    """이미 suffix 로 끝나면 다시 붙이지 않는다 (원본과 같다)."""
    if suffix and not ends_with(name, suffix, case_sensitive):
        return name + suffix
    return name


def text_operations(name, remove_spaces=False, collapse_underscores=False,
                    capitalize_words=False):
    """원본 ApplyTextOperations 이식."""
    result = name

    if remove_spaces:
        result = result.replace(" ", "")

    if collapse_underscores:
        while "__" in result:
            result = result.replace("__", "_")

    if capitalize_words:
        # 원본은 ParseIntoArray(..., CullEmpty=true) 라 빈 조각이 사라진다
        # (앞뒤 밑줄과 연속 밑줄도 함께 정리된다).
        words = [w for w in result.split("_") if w]
        result = "_".join(w[:1].upper() + w[1:].lower() for w in words)

    return result


def invalid_reason(name):
    """에셋 이름으로 쓸 수 없으면 이유(영어 UI 문자열), 쓸 수 있으면 빈 문자열."""
    if not name:
        return "empty name"
    bad = sorted({c for c in name if c in INVALID_NAME_CHARACTERS})
    if bad:
        shown = " ".join("space" if c == " " else repr(c)[1:-1] for c in bad)
        return "invalid character: {}".format(shown)
    return ""


# ---------------------------------------------------------------------------
# 묶음 - Rename 섹션 하나의 결과
# ---------------------------------------------------------------------------

class RenameOptions(object):
    """Rename 섹션의 입력값. ui.py 가 디테일 뷰에서 읽어 채운다."""

    def __init__(self, search="", replace="", match_mode=MATCH_ANYWHERE,
                 case_sensitive=False, prefix="", suffix="", trim_front=0, trim_rear=0,
                 use_naming_convention=False, remove_spaces=False,
                 collapse_underscores=False, capitalize_words=False):
        self.search = search or ""
        self.replace = replace or ""
        self.match_mode = int(match_mode)
        self.case_sensitive = bool(case_sensitive)
        self.prefix = prefix or ""
        self.suffix = suffix or ""
        self.trim_front = max(0, int(trim_front or 0))
        self.trim_rear = max(0, int(trim_rear or 0))
        self.use_naming_convention = bool(use_naming_convention)
        self.remove_spaces = bool(remove_spaces)
        self.collapse_underscores = bool(collapse_underscores)
        self.capitalize_words = bool(capitalize_words)

    def has_manual_operation(self):
        """수동 입력이 하나라도 있으면 네이밍 규칙(CSV)을 쓰지 않는다 (원본 규칙)."""
        return bool(self.search or self.prefix or self.suffix
                    or self.trim_front or self.trim_rear)


def build_new_name(name, options, convention=None):
    """한 에셋의 새 이름.

    순서: Trim → Search/Replace → Prefix → Suffix → (수동 입력이 없을 때만) 네이밍 규칙
          → 텍스트 정리.
    Trim 을 맨 앞에 두는 이유: "지금 이름의 첫 글자를 지운다" 가 직관이고,
    뒤에 붙일 Prefix 를 지워 버리면 안 되기 때문이다.

    convention : 이름 하나를 받아 규칙을 적용한 이름을 돌려주는 함수 (core 가 넘긴다).
    """
    new_name = name

    if options.has_manual_operation():
        new_name = trim(new_name, options.trim_front, options.trim_rear)
        new_name = search_replace(new_name, options.search, options.replace,
                                  options.match_mode, options.case_sensitive)
        new_name = add_prefix(new_name, options.prefix, options.case_sensitive)
        new_name = add_suffix(new_name, options.suffix, options.case_sensitive)
    elif options.use_naming_convention and convention is not None:
        new_name = convention(new_name)

    return text_operations(new_name, options.remove_spaces,
                           options.collapse_underscores, options.capitalize_words)


# ---------------------------------------------------------------------------
# Copy Name - Base 이름을 Target 으로
# ---------------------------------------------------------------------------

def copy_name(base_name, prefix="", suffix="", search="", replace="", case_sensitive=True):
    """A00330 Copy Name 이식: Prefix + (Search/Replace 한) Base 이름 + Suffix.

    - 치환은 **Base 이름에만** 걸린다. Prefix / Suffix 는 그 뒤에 붙는다
      (Prefix 안의 단어는 바뀌지 않는다).
    - Prefix / Suffix 는 이미 있어도 **항상** 붙인다 - 마야 Copy Name 과 같다.
      (Rename 섹션의 Prefix 는 "없을 때만" 붙인다. 두 섹션의 목적이 다르다.)
    """
    core = search_replace(base_name, search, replace, MATCH_ANYWHERE, case_sensitive)
    if not core:
        # Base 이름 전체를 지운 경우 - 마야 쪽도 이 대상은 건너뛴다.
        return ""
    return (prefix or "") + core + (suffix or "")

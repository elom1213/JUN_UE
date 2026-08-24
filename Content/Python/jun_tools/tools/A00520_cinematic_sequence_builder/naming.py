# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-24
#
# A00520 - 이름 · 경로 조립.
#
# 이 모듈은 `unreal` 을 임포트하지 않는다. 순수 문자열 로직만 두어
# 커맨드렛 · 단위 테스트 · 일반 파이썬에서 그대로 돌릴 수 있게 한다.
#
# ── 네이밍 정책 (계획서 §5.2) ──────────────────────────────────────────────
# 이름의 접두 부분(`stem`)은 **툴이 정하지 않는다.** 사용자가 UI 에서 직접 친 문자열을
# 그대로 템플릿에 끼워 넣는다. `MANU_` 를 넣을지 말지는 사용자의 선택이지 코드의 것이 아니다.
#
#   stem = "PreDebut_TSR_CT01"        → MSEQ_PreDebut_TSR_CT01_S06
#   stem = "MANU_PreDebut_TSR_CT01"   → MSEQ_MANU_PreDebut_TSR_CT01_S06
#
# 툴은 stem 을 해석하지도, 검사하지도(문자 유효성 제외) 않는다.

import re

# 언리얼 에셋 이름에 쓸 수 있는 문자. 파일 시스템 · 패키지 경로 양쪽에서 안전한 범위로 좁혔다.
# (엔진이 허용하는 범위보다 좁지만, 좁게 잡아 두면 나중에 넓히기는 쉬워도 그 반대는 어렵다)
VALID_NAME_PATTERN = re.compile(r"^[A-Za-z0-9_\-]+$")

# 패키지 경로. `/Game/...` 또는 `/PluginName/...` 형태만 받는다.
VALID_PACKAGE_PATH_PATTERN = re.compile(r"^/[A-Za-z0-9_\-]+(/[A-Za-z0-9_\-]+)*$")


class NamingError(ValueError):
    """이름/경로 조립에 쓸 수 없는 입력."""


# ---------------------------------------------------------------------------
# 검사
# ---------------------------------------------------------------------------

def validate_stem(stem):
    """Name Stem 문자열 검사. 문제가 있으면 사유 문자열, 없으면 None."""
    if stem is None:
        return "Name Stem is empty."

    stripped = stem.strip()
    if not stripped:
        return "Name Stem is empty."
    if stripped != stem:
        return "Name Stem has leading or trailing whitespace."
    if not VALID_NAME_PATTERN.match(stem):
        return (
            "Name Stem may only contain letters, digits, underscore and hyphen "
            "(got '{}').".format(stem)
        )
    return None


def validate_package_path(path):
    """콘텐츠 브라우저 경로 검사. 문제가 있으면 사유 문자열, 없으면 None."""
    if not path:
        return "Root Path is empty."
    if not path.startswith("/"):
        return "Root Path must start with '/' (got '{}').".format(path)
    if path.endswith("/"):
        return "Root Path must not end with '/' (got '{}').".format(path)
    if not VALID_PACKAGE_PATH_PATTERN.match(path):
        return "Root Path contains characters that are not valid in a package path: '{}'.".format(path)
    return None


# ---------------------------------------------------------------------------
# 조립
# ---------------------------------------------------------------------------

def join_path(*parts):
    """패키지 경로 조각을 이어 붙인다. 중복 슬래시를 만들지 않는다."""
    cleaned = [str(part).strip("/") for part in parts if part not in (None, "")]
    cleaned = [part for part in cleaned if part]
    return "/" + "/".join(cleaned)


def format_scene(number, scene_format="S{:02d}"):
    """6 → 'S06'"""
    return scene_format.format(int(number))


def format_cut(number, cut_format="C{:04d}"):
    """10 → 'C0010'"""
    return cut_format.format(int(number))


def render(template, **tokens):
    """템플릿에 토큰을 채운다. 템플릿이 모르는 토큰을 요구하면 NamingError."""
    try:
        return template.format(**tokens)
    except KeyError as error:
        raise NamingError(
            "Template '{}' needs a token that was not provided: {}".format(template, error)
        )


class NameBuilder(object):
    """한 씬(stem + scene) 안에서 쓰이는 모든 이름과 경로를 조립한다.

    설정(name_templates / scene_format / cut_format / folders)을 통째로 받아
    코드 어디에도 이름 규칙이 흩어지지 않게 한다.
    """

    def __init__(self, config, root_path, stem, scene_number):
        self.templates = config["name_templates"]
        self.folders = config["folders"]
        self.scene_format = config.get("scene_format", "S{:02d}")
        self.cut_format = config.get("cut_format", "C{:04d}")

        self.root_path = root_path.rstrip("/")
        self.stem = stem
        self.scene_number = int(scene_number)
        self.scene = format_scene(self.scene_number, self.scene_format)

    # --- 경로 ---------------------------------------------------------------

    @property
    def scene_path(self):
        """.../CT01/S06"""
        return join_path(self.root_path, self.scene)

    @property
    def scene_subsequence_path(self):
        return join_path(self.scene_path, self.folders["scene_sub"])

    @property
    def scene_map_path(self):
        return join_path(self.scene_path, self.folders["map"])

    @property
    def scene_animation_path(self):
        return join_path(self.scene_path, self.folders["animation"])

    def cut_path(self, cut_name):
        return join_path(self.scene_path, cut_name)

    def cut_subsequence_path(self, cut_name):
        return join_path(self.cut_path(cut_name), self.folders["cut_sub"])

    def cut_animation_path(self, cut_name):
        return join_path(self.cut_path(cut_name), self.folders["animation"])

    def cut_vfx_path(self, cut_name):
        return join_path(self.cut_path(cut_name), self.folders["vfx"])

    # --- 이름 ---------------------------------------------------------------

    def cut_token(self, cut_number):
        return format_cut(cut_number, self.cut_format)

    def master_name(self):
        return render(self.templates["master"], stem=self.stem, scene=self.scene)

    def cut_name(self, cut_name):
        return render(self.templates["cut"], stem=self.stem, scene=self.scene, cut=cut_name)

    def scene_sub_name(self, sub_type):
        return render(
            self.templates["scene_sub"], stem=self.stem, scene=self.scene, type=sub_type
        )

    def cut_sub_name(self, cut_name, sub_type):
        return render(
            self.templates["cut_sub"],
            stem=self.stem,
            scene=self.scene,
            cut=cut_name,
            type=sub_type,
        )

    def camera_binding_name(self, cut_name):
        return render(
            self.templates["camera_binding"], stem=self.stem, scene=self.scene, cut=cut_name
        )

    def shot_display_name(self, cut_name):
        template = self.templates.get("shot_display", "{cut}")
        return render(template, stem=self.stem, scene=self.scene, cut=cut_name)

    # --- 이름 + 경로 --------------------------------------------------------

    def master_asset_path(self):
        return join_path(self.scene_path, self.master_name())

    def cut_asset_path(self, cut_name):
        return join_path(self.cut_path(cut_name), self.cut_name(cut_name))

    def scene_sub_asset_path(self, sub_type):
        return join_path(self.scene_subsequence_path, self.scene_sub_name(sub_type))

    def cut_sub_asset_path(self, cut_name, sub_type):
        return join_path(self.cut_subsequence_path(cut_name), self.cut_sub_name(cut_name, sub_type))


# ---------------------------------------------------------------------------
# 역파싱 — Validate 전용
# ---------------------------------------------------------------------------
#
# 생성 쪽에서는 절대 역파싱을 쓰지 않는다(프로토타입 D8). 여기 있는 함수는
# **이미 존재하는 에셋을 검사할 때만** 쓰인다. 실패해도 "규격 밖"으로 보고할 뿐
# 아무것도 만들지 않으므로 안전하다.

def split_prefix(asset_name):
    """'MSEQ_Foo_S01' → ('MSEQ', 'Foo_S01'). 언더스코어가 없으면 (None, 원본)."""
    if "_" not in asset_name:
        return None, asset_name
    prefix, remainder = asset_name.split("_", 1)
    return prefix, remainder


def strip_suffix(text, suffix):
    """'Foo_S01' 에서 '_S01' 을 떼어낸다. 안 맞으면 None."""
    marker = "_" + suffix
    if text.endswith(marker):
        return text[: -len(marker)]
    return None


def parse_stem(asset_name, prefix, trailing_tokens):
    """'<prefix>_<stem>_<trailing...>' 에서 stem 을 뽑는다.

    trailing_tokens 는 뒤에서부터 떼어낼 토큰 목록(앞→뒤 순서로 준다).
    하나라도 안 맞으면 None 을 돌려준다 — 규격에서 벗어난 이름이라는 뜻이다.
    """
    found_prefix, remainder = split_prefix(asset_name)
    if found_prefix != prefix:
        return None

    for token in reversed(list(trailing_tokens)):
        remainder = strip_suffix(remainder, token)
        if remainder is None:
            return None

    return remainder or None

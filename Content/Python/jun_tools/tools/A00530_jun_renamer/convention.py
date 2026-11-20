# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-11-20
#
# A00530 JUN_Renamer - 에셋 타입별 네이밍 규칙 (CSV). 순수 파이썬, unreal 비의존.
#
# 원본: MANUEditor `FAssetRenameRuleManager` (CSV 읽기) + `FAssetNamingConventionProcessor`
#       (규칙 적용). 동작을 **그대로** 옮겼다 - 원본의 버릇까지 포함해서.
#
# CSV 열: AssetClass,NewPrefix,NewSuffix,PrefixesToRemove,SuffixAliasesToRemove,
#         StringReplacements,SearchCase,Priority
#   - 목록 칸은 `|` 로 나눈다. StringReplacements 는 원본도 읽기만 하고 쓰지 않는다.
#   - 첫 줄(헤더)과 `#` 으로 시작하는 줄, 열이 8 개 미만인 줄(`---`)은 건너뛴다.
#
# 원본과 다른 점 한 가지 - 클래스 판정
#   원본은 에셋을 **로드**해서 `Asset->IsA(UClass*)` 로 판정했고, UClass 표(ClassMap)에 없는
#   클래스(TextureCube, BehaviorTree, MediaTexture ...)의 규칙은 건너뛰었다.
#   여기서는 에셋 레지스트리의 **클래스 이름 + 조상 클래스 이름**으로 판정한다(로드하지 않는다).
#   그래서 CSV 에 적힌 클래스가 엔진에 있으면 그 규칙이 실제로 적용된다.
#
# 원본의 버릇 (그대로 두었다 - 문서 Docs/Tools/A00530_JUNRenamer.md §6 참고)
#   - 우선순위가 **같으면 먼저 나온 규칙**이 이긴다(`>` 비교).
#   - 텍스처 공통 정리 줄은 열이 한 칸 밀려 있어 우선순위가 0 으로 읽힌다. 그 결과
#     접미사가 없는 텍스처는 첫 번째 텍스처 규칙(_DIF, 90)을 받는다.
#   - 이미 텍스처 접미사(_DIF, _NOR ...)로 끝나는 이름은 아예 건드리지 않는다.

import io
import os
import re

# 원본 `TextureSuffixes` (CSV 와 동기화된 목록)
TEXTURE_SUFFIXES = [
    "_DIF", "_NOR", "_ROG", "_SPC", "_MET", "_AO", "_ORM", "_HIG", "_DSP", "_EMS",
    "_OPC", "_OPM", "_MSK", "_HDR",
]

EXPECTED_MIN_COLUMNS = 8


class Rule(object):
    def __init__(self):
        self.asset_class = ""         # CSV 원문 (예: "UStaticMesh")
        self.class_name = ""          # 레지스트리 이름 (예: "StaticMesh")
        self.new_prefix = ""
        self.new_suffix = ""
        self.prefixes_to_remove = []
        self.suffix_aliases_to_remove = []
        self.string_replacements = []
        self.case_sensitive = False
        self.priority = 0

    def is_valid(self):
        return bool(self.asset_class) and bool(
            self.new_prefix or self.new_suffix or self.prefixes_to_remove
            or self.suffix_aliases_to_remove or self.string_replacements)

    def __repr__(self):
        return "Rule({} {}+{} p{})".format(self.class_name, self.new_prefix,
                                           self.new_suffix, self.priority)


# ---------------------------------------------------------------------------
# CSV 읽기 - FAssetRenameRuleManager::ParseCsvLine 이식
# ---------------------------------------------------------------------------

def _trim_quotes(text):
    """FString::TrimQuotes - 앞뒤 따옴표를 하나씩 뗀다."""
    if text.startswith('"'):
        text = text[1:]
    if text.endswith('"'):
        text = text[:-1]
    return text


def _cell(text):
    return _trim_quotes(text).strip()


def _split_list(text):
    """`a|b|c` → [a, b, c]. 빈 조각은 버린다 (ParseIntoArray CullEmpty=true)."""
    return [part for part in text.split("|") if part]


def _atoi(text):
    """FCString::Atoi - 앞쪽 정수만 읽고, 숫자가 없으면 0."""
    match = re.match(r"\s*([+-]?\d+)", text)
    return int(match.group(1)) if match else 0


def class_name_from_rule(asset_class):
    """"UStaticMesh" → "StaticMesh". C++ 접두사 U 를 뗀다."""
    if len(asset_class) > 1 and asset_class[0] == "U" and asset_class[1].isupper():
        return asset_class[1:]
    return asset_class


def parse_line(line):
    """CSV 한 줄 → Rule. 열이 모자라면 빈 Rule(is_valid() == False)."""
    rule = Rule()
    # 원본은 따옴표를 무시하고 쉼표로만 자른다 (CullEmpty=false).
    cells = line.split(",")
    if len(cells) < EXPECTED_MIN_COLUMNS:
        return rule

    rule.asset_class = _cell(cells[0])
    rule.class_name = class_name_from_rule(rule.asset_class)
    rule.new_prefix = _cell(cells[1])
    rule.new_suffix = _cell(cells[2])
    rule.prefixes_to_remove = _split_list(_cell(cells[3]))
    rule.suffix_aliases_to_remove = _split_list(_cell(cells[4]))
    rule.string_replacements = _split_list(_cell(cells[5]))
    rule.case_sensitive = _cell(cells[6]).lower() == "casesensitive"
    rule.priority = _atoi(_cell(cells[7]))
    return rule


def parse_text(text):
    """CSV 전체 → (rules, skipped_lines)."""
    lines = text.splitlines()
    if lines:
        lines = lines[1:]  # 헤더

    rules = []
    skipped = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        rule = parse_line(line)
        if rule.is_valid():
            rules.append(rule)
        else:
            skipped.append(line)
    return rules, skipped


def load_rules(path):
    """CSV 파일 → (rules, skipped_lines). 파일이 없으면 ([], [])."""
    if not path or not os.path.isfile(path):
        return [], []
    with io.open(path, "r", encoding="utf-8-sig", errors="replace") as handle:
        return parse_text(handle.read())


# ---------------------------------------------------------------------------
# 규칙 적용 - FAssetNamingConventionProcessor::GenerateNewAssetName 이식
# ---------------------------------------------------------------------------

def _starts(text, part, case_sensitive):
    return text.startswith(part) if case_sensitive else text.lower().startswith(part.lower())


def _ends(text, part, case_sensitive):
    return text.endswith(part) if case_sensitive else text.lower().endswith(part.lower())


def apply(name, class_names, rules):
    """규칙을 적용한 새 이름. 맞는 규칙이 없으면 name 그대로.

    class_names : 에셋 클래스 이름 + 조상 클래스 이름들
                  (예: ["Texture2D", "Texture", "StreamableRenderAsset", "Object"])
    """
    if not rules:
        return name

    # 이미 텍스처 접미사가 붙은 이름은 건드리지 않는다 (원본: 대소문자 무시 EndsWith)
    for suffix in TEXTURE_SUFFIXES:
        if _ends(name, suffix, False):
            return name

    classes = set(class_names)
    best = name
    highest = -1
    matched = False

    for rule in rules:
        if rule.class_name not in classes:
            continue

        cs = rule.case_sensitive
        base = name

        # 첫 번째로 맞는 접두사 하나만 뗀다
        for prefix in rule.prefixes_to_remove:
            if prefix and _starts(base, prefix, cs):
                base = base[len(prefix):].strip()
                break

        # 다른 텍스처 접미사가 붙어 있으면 떼고 새 접미사로 바꾼다
        if rule.new_suffix:
            for suffix in TEXTURE_SUFFIXES:
                if _ends(base, suffix, cs):
                    if (rule.new_suffix == suffix if cs
                            else rule.new_suffix.lower() == suffix.lower()):
                        continue
                    base = base[:len(base) - len(suffix)]
                    break

        # 첫 번째로 맞는 접미사 별칭 하나만 뗀다
        for alias in rule.suffix_aliases_to_remove:
            if alias and _ends(base, alias, cs):
                base = base[:len(base) - len(alias)].strip()
                break

        proposed = (rule.new_prefix + base + rule.new_suffix).strip()

        if highest == -1 or rule.priority > highest:
            best = proposed
            highest = rule.priority
            matched = True

    return best if matched else name

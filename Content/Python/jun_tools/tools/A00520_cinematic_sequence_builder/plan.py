# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-24
#
# A00520 - 생성 계획 수립.
#
# **이 모듈은 아무것도 쓰지 않는다.** 무엇을 만들지 전부 먼저 열거하고,
# 각 항목이 CREATE / SKIP / CONFLICT 중 무엇인지 판정만 한다.
# Dry Run 이 보여주는 목록과 실제 생성이 어긋나지 않게 하려면, 실행 쪽도
# 반드시 이 계획을 그대로 따라야 한다(build.execute 참조).
#
# 프로토타입은 존재 확인 없이 바로 create_asset 을 불렀다(결함 D1).
# 재실행하면 `SEQ_..._1`, `_2` 가 쌓인다. 그래서 계획/실행을 갈랐다.

import unreal

from . import naming, spec as spec_module

CREATE = "CREATE"
SKIP = "SKIP"
CONFLICT = "CONFLICT"

KIND_DIRECTORY = "directory"
KIND_SEQUENCE = "sequence"


class PlanItem(object):
    def __init__(self, kind, path, action, role, detail=""):
        self.kind = kind        # directory | sequence
        self.path = path        # 패키지 경로 (에셋이면 에셋 경로)
        self.action = action    # CREATE | SKIP | CONFLICT
        self.role = role        # master | cut | scene_sub | cut_sub | folder
        self.detail = detail

    @property
    def name(self):
        return self.path.rsplit("/", 1)[-1]

    def __repr__(self):
        return "{} {} {}".format(self.action, self.role, self.path)


class BuildPlan(object):
    def __init__(self, scene_spec, config):
        self.scene_spec = scene_spec
        self.config = config
        self.items = []

    def add(self, item):
        self.items.append(item)
        return item

    # --- 조회 --------------------------------------------------------------

    def by_action(self, action):
        return [item for item in self.items if item.action == action]

    def by_role(self, role, action=None):
        return [
            item
            for item in self.items
            if item.role == role and (action is None or item.action == action)
        ]

    @property
    def creates(self):
        return self.by_action(CREATE)

    @property
    def conflicts(self):
        return self.by_action(CONFLICT)

    @property
    def sequence_creates(self):
        return [item for item in self.creates if item.kind == KIND_SEQUENCE]

    @property
    def total_steps(self):
        """진행률 표시용. 생성할 에셋 수 + 결선/컬러 단계의 대략치."""
        return max(1, len(self.creates) + len(self.scene_spec.cuts) + 2)

    # --- 리포트 ------------------------------------------------------------

    def summary_line(self):
        counts = {}
        for item in self.sequence_creates:
            counts[item.role] = counts.get(item.role, 0) + 1

        pieces = []
        for role, label in (
            ("master", "MSEQ"),
            ("scene_sub", "scene SSEQ"),
            ("cut", "CSEQ"),
            ("cut_sub", "cut SSEQ"),
        ):
            if counts.get(role):
                pieces.append("{} {}".format(counts[role], label))

        created = ", ".join(pieces) if pieces else "nothing new"
        return "{} | {} folders | {} sequences already exist | {} conflicts".format(
            created,
            len([item for item in self.creates if item.kind == KIND_DIRECTORY]),
            len([item for item in self.by_action(SKIP) if item.kind == KIND_SEQUENCE]),
            len(self.conflicts),
        )

    def report_lines(self, max_listed=40):
        """Output Log 에 찍을 줄 목록."""
        lines = []
        lines.append("Target : {}".format(self.scene_spec.root_path))
        lines.append(
            "Stem   : '{}'   Scene : {}   Cuts : {}   Frames : {}".format(
                self.scene_spec.stem,
                naming.format_scene(
                    self.scene_spec.scene_number, self.config.get("scene_format", "S{:02d}")
                ),
                len(self.scene_spec.cuts),
                self.scene_spec.total_frames,
            )
        )
        lines.append("")

        sequences = self.sequence_creates
        lines.append("Will create {} sequence assets:".format(len(sequences)))
        for item in sequences[:max_listed]:
            lines.append("  + {}".format(item.path))
        if len(sequences) > max_listed:
            lines.append("  ... and {} more (not listed)".format(len(sequences) - max_listed))

        skipped = [item for item in self.by_action(SKIP) if item.kind == KIND_SEQUENCE]
        if skipped:
            lines.append("")
            lines.append("Sequences that already exist, left untouched ({}):".format(len(skipped)))
            for item in skipped[:max_listed]:
                lines.append("  = {}".format(item.path))
            if len(skipped) > max_listed:
                lines.append("  ... and {} more (not listed)".format(len(skipped) - max_listed))

        if self.conflicts:
            lines.append("")
            lines.append("CONFLICTS - these are not Level Sequences ({}):".format(len(self.conflicts)))
            for item in self.conflicts:
                lines.append("  ! {}  ({})".format(item.path, item.detail))

        lines.append("")
        lines.append(self.summary_line())
        return lines


# ---------------------------------------------------------------------------

def _asset_exists(asset_path):
    return unreal.EditorAssetLibrary.does_asset_exist(asset_path)


def _directory_exists(directory_path):
    return unreal.EditorAssetLibrary.does_directory_exist(directory_path)


def _is_level_sequence(asset_path):
    """이미 있는 에셋이 LevelSequence 인지. 아니면 이름이 겹친 다른 타입이다.

    에셋 레지스트리로 먼저 보고(로드 없이 빠르다), 그게 실패하면 실제로 로드해 확인한다.
    두 방법 모두 실패했을 때만 CONFLICT 로 본다 — 판정이 애매하면 만들지 않는 쪽이 안전하다.
    """
    try:
        asset_data = unreal.EditorAssetLibrary.find_asset_data(asset_path)
        if asset_data.is_valid():
            return isinstance(asset_data.get_asset(), unreal.LevelSequence)
    except Exception:
        pass

    try:
        return isinstance(unreal.EditorAssetLibrary.load_asset(asset_path), unreal.LevelSequence)
    except Exception:
        return False


def _judge_sequence(asset_path):
    if not _asset_exists(asset_path):
        return CREATE, ""
    if _is_level_sequence(asset_path):
        return SKIP, "already a Level Sequence"
    return CONFLICT, "an asset with this name exists but is not a Level Sequence"


def _judge_directory(directory_path):
    return (SKIP, "") if _directory_exists(directory_path) else (CREATE, "")


def build_plan(scene_spec, config):
    """무엇을 만들지 전부 열거한다. 쓰기 없음."""
    plan = BuildPlan(scene_spec, config)
    builder = naming.NameBuilder(config, scene_spec.root_path, scene_spec.stem,
                                 scene_spec.scene_number)
    sub_types = spec_module.sub_type_keys(config)

    def add_directory(path):
        action, detail = _judge_directory(path)
        plan.add(PlanItem(KIND_DIRECTORY, path, action, "folder", detail))

    def add_sequence(path, role):
        action, detail = _judge_sequence(path)
        plan.add(PlanItem(KIND_SEQUENCE, path, action, role, detail))

    # --- 씬 레벨 ------------------------------------------------------------
    add_directory(builder.scene_path)

    if scene_spec.make_scene_subs:
        add_directory(builder.scene_subsequence_path)
        for sub_type in sub_types:
            add_sequence(builder.scene_sub_asset_path(sub_type), "scene_sub")

    if scene_spec.make_side_folders:
        add_directory(builder.scene_map_path)
        add_directory(builder.scene_animation_path)

    # --- 컷 레벨 ------------------------------------------------------------
    for cut in scene_spec.cuts:
        add_directory(builder.cut_path(cut.name))
        add_sequence(builder.cut_asset_path(cut.name), "cut")

        if scene_spec.make_cut_subs:
            add_directory(builder.cut_subsequence_path(cut.name))
            for sub_type in sub_types:
                add_sequence(builder.cut_sub_asset_path(cut.name, sub_type), "cut_sub")

        if scene_spec.make_side_folders:
            add_directory(builder.cut_animation_path(cut.name))
            add_directory(builder.cut_vfx_path(cut.name))

    # --- 마스터 (마지막에 만든다. 참조가 아래에서 위로 흐른다) ----------------
    add_sequence(builder.master_asset_path(), "master")

    return plan

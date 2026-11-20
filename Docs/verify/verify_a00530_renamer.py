# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-11-20
#
# A00530 JUN_Renamer - headless verification.
#
# Run against a SCRATCH project only - it creates and renames assets under /Game/JUNRenamerTest.
#
#   UnrealEditor-Cmd.exe <Scratch>.uproject -PLUGIN="<JUN_UE>/JUNTools.uplugin" ^
#       -run=pythonscript -script="<this file>" -unattended -nosplash -nullrhi ^
#       -AbsLog="verify_a00530.log"
#
# Then grep the log for "[A00530-VERIFY]".
#
# What it proves: the uclass / uenum / CallInEditor functions register, the details-view
# options exist, and every button path (Load, -1 Front / -1 Rear, Preview, Rename, Base/Targets,
# Copy Name) renames real assets on disk, including a referenced asset that leaves a redirector.
# What it cannot prove: how the dialog looks (-unattended never opens the window).

import os
import traceback

import unreal

TAG = "[A00530-VERIFY]"
ROOT = "/Game/JUNRenamerTest"
RESULTS = []


def say(text):
    unreal.log("{} {}".format(TAG, text))


def check(name, condition, detail=""):
    RESULTS.append(bool(condition))
    say("{} {} {}".format("PASS" if condition else "FAIL", name, detail))


def exists(path):
    return unreal.EditorAssetLibrary.does_asset_exist(path)


def on_disk(package):
    relative = package[len("/Game/"):]
    return os.path.isfile(os.path.join(unreal.Paths.project_content_dir(), relative + ".uasset"))


def make_material(name):
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    asset = tools.create_asset(name, ROOT, unreal.Material, unreal.MaterialFactoryNew())
    unreal.EditorAssetLibrary.save_loaded_asset(asset, False)
    return asset


def make_instance(name, parent):
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    asset = tools.create_asset(name, ROOT, unreal.MaterialInstanceConstant,
                               unreal.MaterialInstanceConstantFactoryNew())
    unreal.MaterialEditingLibrary.set_material_instance_parent(asset, parent)
    unreal.EditorAssetLibrary.save_loaded_asset(asset, False)
    return asset


def main():
    if unreal.EditorAssetLibrary.does_directory_exist(ROOT):
        unreal.EditorAssetLibrary.delete_directory(ROOT)

    from jun_tools import registry
    spec = registry.find("A00530_jun_renamer")
    check("registry", spec.section == "Asset", spec.label)

    from jun_tools.tools.A00530_jun_renamer import ui, core

    # dialog options used by show()
    options = unreal.EditorDialogLibraryObjectDetailsViewOptions()
    for prop in ("show_object_name", "allow_search", "allow_resizing", "min_width", "min_height"):
        try:
            options.get_editor_property(prop)
            check("option " + prop, True)
        except Exception as error:
            check("option " + prop, False, str(error))

    # rules file
    check("rules csv", len(core.load_rules()) > 50, core.rules_path())

    # --- assets ---------------------------------------------------------------
    base_mat = make_material("XM_Base")          # referenced by the instance below
    make_material("XRock_A")
    make_material("XRock_B")
    make_instance("MI_Child", base_mat)

    settings = ui.make_settings()
    ui._state["assets"] = core.assets_in_folders([ROOT])
    check("load folder", len(ui._state["assets"]) == 4, str(len(ui._state["assets"])))

    # -1 Front through the real UFUNCTION (= the button), inside a transaction like the button
    with unreal.ScopedEditorTransaction("verify -1 Front"):
        settings.trim_front_one()
    check("-1 Front bumps counter", settings.get_editor_property("trim_front") == 1)
    preview = list(settings.get_editor_property("rename_preview"))
    say("preview after -1 Front: {}".format(preview))
    check("preview has rows", len(preview) == 4)
    check("MI_Child -> I_Child previewed", any("MI_Child  ->  I_Child" in line for line in preview))

    settings.trim_rear_one()
    settings.trim_rear_one()
    settings.reset_trim()
    check("reset trim", settings.get_editor_property("trim_front") == 0
          and settings.get_editor_property("trim_rear") == 0)

    # Rename: trim the leading X off the three materials only (name filter), add suffix
    settings.set_editor_property("name_filter", "xr")  # filter ignores case
    settings.set_editor_property("trim_front", 1)
    settings.set_editor_property("suffix", "_01")
    renamed, failed = ui.execute_rename(settings, confirm=False)
    check("rename count", len(renamed) == 2 and not failed, "{} / {}".format(len(renamed), len(failed)))
    check("Rock_A_01 exists", exists(ROOT + "/Rock_A_01") and on_disk(ROOT + "/Rock_A_01"))
    check("XRock_A gone from disk", not on_disk(ROOT + "/XRock_A"))
    check("trim reset after rename", settings.get_editor_property("trim_front") == 0)

    # referenced asset -> redirector, saved
    settings.set_editor_property("name_filter", "XM_")
    settings.set_editor_property("suffix", "")
    settings.set_editor_property("search", "XM_")
    settings.set_editor_property("replace", "M_")
    settings.set_editor_property("match_mode", ui._to_match_enum(1))
    renamed, failed = ui.execute_rename(settings, confirm=False)
    check("referenced rename", len(renamed) == 1 and exists(ROOT + "/M_Base"))
    child = unreal.load_asset(ROOT + "/MI_Child")
    parent = child.get_editor_property("parent")
    check("instance still points at renamed parent", parent and parent.get_name() == "M_Base",
          parent.get_path_name() if parent else "None")
    say("old path on disk after rename (redirector): {}".format(on_disk(ROOT + "/XM_Base")))
    dirty = [p.get_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()]
    check("no dirty packages left (referencer saved by engine)", not dirty, str(dirty))

    # name taken
    settings.set_editor_property("name_filter", "Rock_B")
    settings.set_editor_property("search", "B")
    settings.set_editor_property("replace", "A")
    settings.set_editor_property("match_mode", ui._to_match_enum(0))
    rows = ui.preview_rename(settings)
    check("name taken detected", rows and rows[0].status == core.STATUS_TAKEN,
          rows[0].line() if rows else "")

    # invalid name
    settings.set_editor_property("replace", "A B")
    rows = ui.preview_rename(settings)
    check("invalid name detected", rows and rows[0].status.startswith("invalid"),
          rows[0].line() if rows else "")

    # --- Copy Name ---------------------------------------------------------------
    rock_a = unreal.load_asset(ROOT + "/Rock_A_01")
    rock_b = unreal.load_asset(ROOT + "/Rock_B_01")
    m_base = unreal.load_asset(ROOT + "/M_Base")
    child = unreal.load_asset(ROOT + "/MI_Child")
    settings.set_editor_property("base", [m_base, rock_a])
    settings.set_editor_property("targets", [child, rock_b])
    settings.set_editor_property("copy_prefix", "MI_")
    settings.set_editor_property("copy_suffix", "_copy")
    settings.set_editor_property("copy_search", "_01")
    settings.set_editor_property("copy_replace", "")
    settings.preview_copy()
    say("copy preview: {}".format(list(settings.get_editor_property("copy_preview"))))
    renamed, failed = ui.execute_copy(settings, confirm=False)
    check("copy name count", len(renamed) == 2 and not failed)
    check("MI_M_Base_copy exists", exists(ROOT + "/MI_M_Base_copy"))
    check("MI_Rock_A_copy exists", exists(ROOT + "/MI_Rock_A_copy"))

    # counts differ warning
    settings.set_editor_property("targets", [child])
    rows = ui.preview_copy(settings)
    lines = list(settings.get_editor_property("copy_preview"))
    check("count mismatch warns", lines and lines[0].startswith("[WARN]"), lines[0] if lines else "")

    # state survives a new settings object (= reopening the window)
    again = ui.make_settings()
    check("state persists", again.get_editor_property("copy_prefix") == "MI_"
          and len(again.get_editor_property("base")) == 2)

    # menu entry path: jun_tools.run() -> ui.show(). -unattended returns from the dialog at once.
    import jun_tools
    jun_tools.run("A00530_jun_renamer")
    import sys
    fresh_ui = sys.modules["jun_tools.tools.A00530_jun_renamer.ui"]
    check("DEV_MODE reload re-imported ui", fresh_ui is not ui)
    check("uclass registered once per session (no re-instancing)",
          fresh_ui._types()[0] is ui._types()[0])
    check("show() released its object", not fresh_ui._ALIVE)
    # button on an object made by the OLD module runs the NEW module's code
    called = []
    original = fresh_ui.preview_copy
    fresh_ui.preview_copy = lambda target: called.append(1) or original(target)
    settings.preview_copy()
    fresh_ui.preview_copy = original
    check("button dispatches to reloaded module", called == [1])
    after = ui.make_settings()
    check("state survives show() + DEV_MODE reload", after.get_editor_property("copy_prefix") == "MI_")

    unreal.EditorAssetLibrary.delete_directory(ROOT)


try:
    main()
except Exception:
    RESULTS.append(False)
    say("EXCEPTION\n" + traceback.format_exc())

say("SUMMARY {}/{} passed".format(sum(RESULTS), len(RESULTS)))

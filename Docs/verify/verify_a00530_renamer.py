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

    # one settings object per session (the tab and the dialog share it)
    again = ui.settings()
    check("one settings object per session", again is settings
          and again.get_editor_property("copy_prefix") == "MI_"
          and len(again.get_editor_property("base")) == 2)

    # --- v01.01: EUW tab -------------------------------------------------------
    blueprint = unreal.load_asset(ui.EUW_PATH)
    check("EUW loads", blueprint is not None, ui.EUW_PATH)
    cdo = unreal.get_default_object(blueprint.generated_class())
    check("EUW is an EditorUtilityWidget", isinstance(cdo, unreal.EditorUtilityWidget))
    check("EUW tab title", str(cdo.get_editor_property("tab_display_name")) == "JUN Renamer")
    templates = [w for w in unreal.ObjectIterator(unreal.Widget)
                 if "EUW_JUNRenamer_C:WidgetTree" in w.get_path_name()]
    check("EUW root widget is DetailsView",
          len(templates) == 1 and isinstance(templates[0], unreal.DetailsView)
          and templates[0].get_name() == ui.EUW_DETAILS_VIEW and templates[0].get_parent() is None,
          str([(type(w).__name__, w.get_name()) for w in templates]))
    cdo.get_editor_property(ui.EUW_DETAILS_VIEW)
    check("DetailsView exposed as variable", True)

    # a stand-alone DetailsView stands in for the one inside the tab
    view = unreal.new_object(unreal.DetailsView)
    view.set_object(settings)
    check("set_object takes the settings object", view.get_object() == settings)
    check("bind connects once", ui.bind(view) is True and ui.bind(view) is False)

    settings.set_editor_property("targets", [child, rock_b])
    settings.set_editor_property("copy_prefix", "LIVE_")
    view.get_editor_property("on_property_changed").broadcast("copy_prefix")
    lines = list(settings.get_editor_property("copy_preview"))
    check("editing a Copy Name field refreshes Copy Preview", any("LIVE_" in l for l in lines), str(lines[:1]))

    settings.set_editor_property("name_filter", "")
    settings.set_editor_property("search", "")
    settings.set_editor_property("prefix", "LIVE_")
    view.get_editor_property("on_property_changed").broadcast("prefix")
    lines = list(settings.get_editor_property("rename_preview"))
    check("editing a Rename field refreshes Rename Preview", any("->  LIVE_" in l for l in lines), str(lines[:1]))

    before = list(settings.get_editor_property("rename_preview"))
    settings.set_editor_property("prefix", "")
    ui.on_property_changed("rename_preview")
    check("preview array edits are ignored", list(settings.get_editor_property("rename_preview")) == before)
    settings.set_editor_property("copy_prefix", "MI_")

    # menu entry path: jun_tools.run() -> ui.show(). A commandlet never registers the tab,
    # so show() must fall back to the dialog (which -unattended closes at once).
    import sys
    import jun_tools
    result = jun_tools.run("A00530_jun_renamer")
    check("show() falls back to the dialog when no tab can open", result == "modal", str(result))
    fresh_ui = sys.modules["jun_tools.tools.A00530_jun_renamer.ui"]
    check("DEV_MODE reload re-imported ui", fresh_ui is not ui)
    check("uclass registered once per session (no re-instancing)",
          fresh_ui._types()[0] is ui._types()[0])
    called = []
    original = fresh_ui.preview_copy
    fresh_ui.preview_copy = lambda target: called.append(1) or original(target)
    settings.preview_copy()
    fresh_ui.preview_copy = original
    check("button dispatches to reloaded module", called == [1])
    called = []
    original = fresh_ui.on_property_changed
    fresh_ui.on_property_changed = lambda name: called.append(str(name))
    view.get_editor_property("on_property_changed").broadcast("prefix")
    fresh_ui.on_property_changed = original
    check("field-edit event dispatches to reloaded module", called == ["prefix"], str(called))

    # Tools > JUN > Reload JUN Tools purges every jun_tools module
    jun_tools.reload_all()
    full_ui = __import__("jun_tools.tools.A00530_jun_renamer.ui", fromlist=["ui"])
    check("Reload JUN Tools keeps the class", full_ui._types()[0] is ui._types()[0])
    check("Reload JUN Tools keeps the settings object and values",
          full_ui.settings() is settings and settings.get_editor_property("copy_prefix") == "MI_")

    unreal.EditorAssetLibrary.delete_directory(ROOT)


try:
    main()
except Exception:
    RESULTS.append(False)
    say("EXCEPTION\n" + traceback.format_exc())

say("SUMMARY {}/{} passed".format(sum(RESULTS), len(RESULTS)))

# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-09-01
#
# A00510 v01.03 - "Apply" button verification.
#
# Run headless against a scratch project. This one is non-destructive: it only
# reads and writes UPersonaOptions in memory and restores the original values at the end.
#
#   UnrealEditor-Cmd.exe <Scratch>.uproject -run=pythonscript ^
#       -script="<this file>" -unattended -nosplash -nullrhi ^
#       -AbsLog="verify_a00510.log"
#
# Then grep the log for "[A00510-VERIFY]".
#
# What a headless run can and cannot prove:
#   CAN  - the uclass/uenum still build, the CallInEditor UFUNCTIONs register on the class,
#          and calling them applies / resets the settings the same way the button will.
#   CANNOT - that the button is drawn. `-unattended` makes ShowObjectsDetailsView return
#          false without ever opening a window, so the details panel is never built.
#          The drawing rule itself is engine code we can read instead:
#          PropertyCustomizationHelpers::CanCallFunctionBasedOnParams (5.7) accepts a
#          function when `GetBoolMetaData("CallInEditor") && ParmsSize == 0`, and
#          DetailCustomizations registers FObjectDetails for "Object", so every details
#          view gets those buttons. B6 below checks both conditions we control.

import importlib
import traceback

import unreal

TAG = "[A00510-VERIFY]"

RESULTS = []


def check(identifier, description, function):
    """Run one probe. Never raises - a failed probe is data, not a crash."""
    try:
        value = function()
        passed = value is not False and value is not None
        detail = "" if passed else "returned {!r}".format(value)
    except Exception as error:
        passed = False
        detail = "{}: {}\n{}".format(type(error).__name__, error, traceback.format_exc())

    RESULTS.append((identifier, passed, description, detail))
    unreal.log(
        "{} {} {:<5} {}{}".format(
            TAG, "PASS" if passed else "FAIL", identifier, description,
            "  --  " + detail if detail else "",
        )
    )
    return passed


def run():
    from jun_tools.tools.A00510_bone_viewport import core, ui

    unreal.log("{} ---- start ----".format(TAG))

    saved = (core.get_bone_draw_mode(), core.get_show_bone_colors())
    unreal.log("{} saved live values: {}".format(TAG, saved))

    try:
        # --- B1 : types still build -----------------------------------------
        settings_cls, mode_enum = ui._types()
        check("B1", "uclass + uenum build", lambda: settings_cls is not None)

        settings = settings_cls()
        check("B2", "settings object constructs", lambda: settings is not None)

        # --- B3/B4 : the two CallInEditor entry points exist -----------------
        check("B3", "apply() is callable on the settings object",
              lambda: callable(getattr(settings, "apply", None)))
        check("B4", "reset() is callable on the settings object",
              lambda: callable(getattr(settings, "reset", None)))

        # --- B5 : they are real UFunctions on the generated class ------------
        settings_class = settings.get_class()
        check("B5", "apply/reset exist as UFunctions on the UClass",
              lambda: all(unreal.find_object(settings_class, name) is not None
                          for name in ("apply", "reset")))

        # --- B6 : the details view only draws a button for a 0-parameter function.
        #   `@unreal.uclass()` replaces the python function with a native method bound to the
        #   UFunction, so `inspect.signature` cannot see it - probe the arity instead.
        def takes_no_arguments():
            for name in ("apply", "reset"):
                try:
                    getattr(settings, name)(0)
                except TypeError:
                    continue
                return "{} accepted an argument".format(name)
            return True

        check("B6", "apply/reset take no parameters (ParmsSize == 0)", takes_no_arguments)

        # --- B7 : Apply applies what the dialog is showing --------------------
        start = (core.BoneDrawMode.NONE, False)
        core.apply(bone_draw_mode=start[0], show_bone_colors=start[1])

        ui._write(settings, mode_enum, core.BoneDrawMode.ALL_HIERARCHY, True)
        check("B7a", "unapplied edits are reported as pending",
              lambda: sorted(ui._pending(settings)) == sorted(
                  [core.CHANGE_BONE_DRAW_MODE, core.CHANGE_SHOW_BONE_COLORS]))

        changed = ui.apply_settings(settings)
        check("B7b", "Apply writes both settings",
              lambda: len(changed) == 2
                      and core.get_bone_draw_mode() == core.BoneDrawMode.ALL_HIERARCHY
                      and core.get_show_bone_colors() is True)

        # --- B8 : Apply is idempotent - pressing it twice is a no-op ----------
        check("B8", "second Apply reports nothing changed",
              lambda: ui.apply_settings(settings) == []
                      and ui._pending(settings) == [])

        # --- B9 : Reset goes back to the values the window opened with --------
        ui._ORIGINALS[id(settings)] = start
        ui.reset_settings(settings)
        check("B9", "Reset restores and applies the original values",
              lambda: (core.get_bone_draw_mode(), core.get_show_bone_colors()) == start
                      and ui._read(settings) == start)

        ui._ORIGINALS.pop(id(settings), None)
        check("B9b", "Reset without a remembered original does not raise",
              lambda: ui.reset_settings(settings) == [])

        # --- B10 : show() under -unattended takes the cancel path -------------
        core.apply(bone_draw_mode=start[0], show_bone_colors=start[1])
        check("B10a", "show() returns the cancel result headless",
              lambda: ui.show() == [])
        check("B10b", "show() leaves nothing behind",
              lambda: ui._ALIVE == [] and ui._ORIGINALS == {})
        check("B10c", "cancel applied nothing",
              lambda: (core.get_bone_draw_mode(), core.get_show_bone_colors()) == start)

        # --- B11 : quick action still works -----------------------------------
        check("B11", "quick_show_all sets All Hierarchy",
              lambda: (ui.quick_show_all(),
                       core.get_bone_draw_mode() == core.BoneDrawMode.ALL_HIERARCHY)[1])

        # --- B12 : DEV_MODE reload re-registers the uclass without error -------
        def reload_three_times():
            module = ui
            for _ in range(3):
                module = importlib.reload(module)
                module._TYPES = None
                module._types()
                module.show()
            return True

        check("B12", "module reload x3 re-registers uclass/uenum", reload_three_times)

    finally:
        core.apply(bone_draw_mode=saved[0], show_bone_colors=saved[1])
        unreal.log("{} restored live values: {}".format(TAG, saved))

    failed = [r for r in RESULTS if not r[1]]
    unreal.log("{} ---- {}/{} passed ----".format(TAG, len(RESULTS) - len(failed), len(RESULTS)))
    for identifier, _, description, detail in failed:
        unreal.log_error("{} FAILED {} : {}  {}".format(TAG, identifier, description, detail))


try:
    run()
except Exception:
    unreal.log_error("{} crashed:\n{}".format(TAG, traceback.format_exc()))

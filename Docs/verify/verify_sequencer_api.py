# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-24
#
# A00520 Phase 0 - Sequencer python binding verification.
#
# Run headless against a scratch project. Never run this against a production project:
# it creates assets under VERIFY_ROOT and deletes them again at the end.
#
#   UnrealEditor-Cmd.exe <Scratch>.uproject -run=pythonscript ^
#       -script="<this file>" -unattended -nosplash -nullrhi ^
#       -AbsLog="verify_sequencer.log"
#
# Then grep the log for "[A00520-VERIFY]".
#
# Checks A1..A7 were already answered by the prototype (Docs/Plans/seq_batch_tool_ue57.py);
# they are re-run here so a single log proves the whole surface on this engine build.
# A8..A13 are the ones that were still open when the plan was written.

import traceback

import unreal

TAG = "[A00520-VERIFY]"
VERIFY_ROOT = "/Game/_JUNToolsVerify/A00520"

RESULTS = []


def check(identifier, description, function):
    """Run one probe. Never raises - a failed probe is data, not a crash."""
    try:
        value = function()
        passed = value is not False and value is not None
        detail = "" if passed else "returned {!r}".format(value)
    except Exception as error:
        passed = False
        detail = "{}: {}".format(type(error).__name__, error)

    RESULTS.append((identifier, passed, description, detail))
    unreal.log(
        "{} {} {:<6} {}{}".format(
            TAG, "PASS" if passed else "FAIL", identifier, description,
            "  --  " + detail if detail else "",
        )
    )
    return passed


def make_sequence(name):
    return unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        asset_name=name,
        package_path=VERIFY_ROOT,
        asset_class=unreal.LevelSequence,
        factory=unreal.LevelSequenceFactoryNew(),
    )


def run():
    from jun_tools.tools.A00520_cinematic_sequence_builder import (
        camera, compat, core, naming, plan, spec,
    )

    unreal.log("{} ---- start ----".format(TAG))

    # --- A7 / A4 : directories and asset creation ---------------------------
    check("A7", "EditorAssetLibrary.make_directory",
          lambda: (unreal.EditorAssetLibrary.make_directory(VERIFY_ROOT),
                   unreal.EditorAssetLibrary.does_directory_exist(VERIFY_ROOT))[1])

    parent = make_sequence("VERIFY_Parent")
    child = make_sequence("VERIFY_Child")
    shot = make_sequence("VERIFY_Shot")
    camera_sequence = make_sequence("VERIFY_Cam")

    check("A1", "create_asset(LevelSequence, LevelSequenceFactoryNew)",
          lambda: parent is not None and child is not None)

    # --- A2 : which track-adding binding exists ------------------------------
    extensions = getattr(unreal, "MovieSceneSequenceExtensions", None)
    check("A2a", "unreal.MovieSceneSequenceExtensions exists (SequencerScripting plugin)",
          lambda: extensions is not None)
    check("A2b", "sequence.add_track", lambda: hasattr(parent, "add_track"))
    check("A2c", "sequence.add_master_track (legacy)",
          lambda: hasattr(parent, "add_master_track"))
    sub_track = None

    def add_sub_track():
        nonlocal_holder["track"] = compat.add_sequence_track(parent, unreal.MovieSceneSubTrack)
        return nonlocal_holder["track"] is not None

    nonlocal_holder = {}
    check("A2", "compat.add_sequence_track(MovieSceneSubTrack)", add_sub_track)
    sub_track = nonlocal_holder.get("track")

    # --- A3 : sub section wiring ---------------------------------------------
    section_holder = {}

    def wire_sub_section():
        section = sub_track.add_section()
        section.set_sequence(child)
        compat.set_section_range(section, 0, 120)
        section_holder["section"] = section
        return compat.get_section_sequence(section) is not None

    check("A3", "SubSection.set_sequence + set_range", wire_sub_section)
    check("A11", "SubSection.set_row_index",
          lambda: compat.set_section_row_index(section_holder["section"], 1))

    # --- A8 : cinematic shot track (was open) --------------------------------
    shot_track_class = getattr(unreal, "MovieSceneCinematicShotTrack", None)
    check("A8a", "unreal.MovieSceneCinematicShotTrack exists",
          lambda: shot_track_class is not None)

    def wire_shot():
        track = compat.add_sequence_track(parent, shot_track_class)
        section = track.add_section()
        section.set_sequence(shot)
        compat.set_section_range(section, 0, 120)
        return compat.get_section_sequence(section) is not None

    if shot_track_class is not None:
        check("A8", "CinematicShotTrack section.set_sequence + set_range", wire_shot)
        check("A8b", "CinematicShotSection display name",
              lambda: compat.set_shot_display_name(
                  compat.get_track_sections(
                      compat.find_sequence_tracks(parent, shot_track_class)[0]
                  )[0],
                  "C0010",
              ))

    # --- A9 / A10 : folders and colours (the real risk) ----------------------
    folder_holder = {}

    def add_folder():
        folder_holder["folder"] = compat.add_root_folder(parent, "ANIM")
        return folder_holder["folder"] is not None

    check("A9a", "add_root_folder_to_sequence", add_folder)
    if folder_holder.get("folder") is not None:
        check("A9", "MovieSceneFolder colour",
              lambda: compat.set_folder_color(
                  folder_holder["folder"], compat.color_from_hex("#FF604F")
              ))
        check("A9b", "move a track into a folder",
              lambda: compat.add_track_to_folder(folder_holder["folder"], sub_track))
        check("A9c", "read folder name back",
              lambda: compat.get_folder_name(folder_holder["folder"]) == "ANIM")

    check("A10", "track colour tint",
          lambda: compat.set_track_color(sub_track, compat.color_from_hex("#77474B")))
    check("A10b", "track display name",
          lambda: compat.set_track_display_name(sub_track, "ANIM"))

    # --- A5 : sequence settings ----------------------------------------------
    check("A5a", "set_tick_resolution", lambda: compat.set_tick_resolution(parent, 24000))
    check("A5b", "set_display_rate", lambda: compat.set_display_rate(parent, 30))
    check("A5c", "set_playback_range", lambda: compat.set_playback_range(parent, 0, 1560))

    # --- A12 / A4 / A14 : camera rig -----------------------------------------
    check("A12", "spawn actor through EditorActorSubsystem or EditorLevelLibrary",
          lambda: _spawn_and_destroy(compat))

    def build_camera():
        warnings = camera.setup_camera(
            camera_sequence, "VERIFY_S01_C0010_camera", 120,
            spec.DEFAULT_CONFIG["camera"]["float_tracks"],
        )
        for message in warnings:
            unreal.log_warning("{} camera warning: {}".format(TAG, message))
        return bool(compat.find_sequence_tracks(camera_sequence, unreal.MovieSceneCameraCutTrack))

    check("A4", "camera.setup_camera end to end", build_camera)
    check("A14", "MovieSceneSequenceExtensions.remove_binding exists",
          lambda: hasattr(extensions, "remove_binding") if extensions else False)

    # --- A13 : does a transaction roll back asset creation? -------------------
    rollback_path = "{}/VERIFY_Rollback".format(VERIFY_ROOT)

    def transaction_rollback():
        with unreal.ScopedEditorTransaction("A00520 verify rollback"):
            make_sequence("VERIFY_Rollback")
        # We cannot press ctrl+Z headlessly, so only report that the asset exists.
        # A13 is informational: if the answer is "no rollback", the tool must report
        # what it created when it fails - which build.py already does.
        return unreal.EditorAssetLibrary.does_asset_exist(rollback_path)

    check("A13", "asset creation inside ScopedEditorTransaction (informational)",
          transaction_rollback)

    # --- end to end through the real entry point ------------------------------
    def end_to_end():
        result = core.build_uniform(
            root_path="{}/E2E".format(VERIFY_ROOT),
            stem="VERIFY_TSR_CT01",
            scene_number=1,
            cut_start=10,
            cut_count=2,
            cut_step=10,
            frames_per_cut=60,
            dry_run=False,
        )
        return result is not None and not result.errors and len(result.created_assets) > 0

    check("E2E1", "core.build_uniform creates a scene", end_to_end)

    def idempotent():
        result = core.build_uniform(
            root_path="{}/E2E".format(VERIFY_ROOT),
            stem="VERIFY_TSR_CT01",
            scene_number=1,
            cut_start=10,
            cut_count=2,
            cut_step=10,
            frames_per_cut=60,
            dry_run=False,
        )
        return result is not None and len(result.created_assets) == 0

    check("E2E2", "running it twice creates nothing new (idempotent)", idempotent)

    def validate_runs():
        report = core.validate("{}/E2E/S01".format(VERIFY_ROOT), write_report=False)
        return report is not None and report.count("ERROR") == 0

    check("E2E3", "validate reports a clean scene as clean", validate_runs)

    # --- summary --------------------------------------------------------------
    passed = len([entry for entry in RESULTS if entry[1]])
    unreal.log("{} ---- {} / {} passed ----".format(TAG, passed, len(RESULTS)))
    for identifier, ok, description, detail in RESULTS:
        if not ok:
            unreal.log_warning("{} OPEN {} - {} {}".format(TAG, identifier, description, detail))


def _spawn_and_destroy(compat):
    actor = compat.spawn_actor(unreal.CineCameraActor)
    if actor is None:
        return False
    return compat.destroy_actor(actor)


def cleanup():
    try:
        if unreal.EditorAssetLibrary.does_directory_exist(VERIFY_ROOT):
            unreal.EditorAssetLibrary.delete_directory(VERIFY_ROOT)
            unreal.log("{} cleaned up {}".format(TAG, VERIFY_ROOT))
    except Exception:
        unreal.log_warning("{} could not clean up {}".format(TAG, VERIFY_ROOT))


try:
    run()
except Exception:
    unreal.log_error("{} verification crashed:\n{}".format(TAG, traceback.format_exc()))
finally:
    cleanup()

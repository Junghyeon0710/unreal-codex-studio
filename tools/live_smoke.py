#!/usr/bin/env python3
"""Opt-in fixture test. Creates a uniquely named Blueprint through official MCP."""
import argparse
import datetime as dt
import json
from pathlib import Path
import uuid
from mcp_client import Client, endpoint_lock
from studio import Unreal, ASSET, BLUEPRINT, SCENE, EDITOR, project_path

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--project", required=True)
    p.add_argument("--url", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--allow-fixture-write", action="store_true")
    a = p.parse_args()
    if not a.allow_fixture_write:
        p.error("Use --allow-fixture-write only for a disposable test project.")
    project = project_path(a.project)
    report = {"timestamp_utc": dt.datetime.now(dt.timezone.utc).isoformat(), "status": "failed", "checks": []}
    ue = None
    started_pie = False
    try:
        with endpoint_lock(a.url):
            client = Client(a.url); report["server"] = client.initialize(); ue = Unreal(client)
            ue.bind(project); report["checks"].append("project_binding")
            before = ue.call(EDITOR, "IsPIERunning")
            if before is not False:
                raise RuntimeError("PIE is already active; do not take over an existing session.")
            name = "BP_StudioSmoke_" + uuid.uuid4().hex[:8]
            path = "/Game/StudioSmoke/" + name
            blueprint = ue.call(BLUEPRINT, "create", {"folder_path": "/Game/StudioSmoke",
                "asset_name": name, "asset_type": {"refPath": "/Script/Engine.Actor"}})
            if not isinstance(blueprint, dict) or not blueprint.get("refPath"):
                raise RuntimeError("Blueprint creation returned no object reference.")
            report["asset"] = path; report["checks"].append("blueprint_created")
            ue.call(BLUEPRINT, "compile_blueprint", {"blueprint": blueprint, "warnings_as_errors": True})
            report["checks"].append("blueprint_compiled")
            if ue.call(ASSET, "save_assets", {"asset_paths": [path]}) is not True:
                raise RuntimeError("Asset save failed.")
            if ue.call(ASSET, "exists", {"path": path}) is not True:
                raise RuntimeError("Asset read-back failed.")
            if not (project.parent / "Content/StudioSmoke" / (name + ".uasset")).is_file():
                raise RuntimeError("Saved .uasset is missing from expected project.")
            report["checks"].append("asset_saved_and_read_back")
            actor = ue.call(SCENE, "add_to_scene_from_asset", {"asset_path": path, "name": name,
                "xform": {"location": {"x": 0, "y": 0, "z": 150}}})
            if not actor:
                raise RuntimeError("Actor spawn failed.")
            found = ue.call(SCENE, "find_actors", {"name": name, "tag": "", "collision_channels": []})
            if not found:
                raise RuntimeError("Spawned actor not found.")
            report["checks"].append("actor_spawned_and_found")
            ue.call(EDITOR, "StartPIE", {"options": {"bSimulate": False, "warmupSeconds": 1}})
            started_pie = True
            if ue.call(EDITOR, "IsPIERunning") is not True:
                raise RuntimeError("PIE start was not observed.")
            report["checks"].append("pie_running")
            ue.call(EDITOR, "StopPIE"); started_pie = False
            if ue.call(EDITOR, "IsPIERunning") is not False:
                raise RuntimeError("PIE stop was not observed.")
            report["checks"].append("pie_stopped")
            report["status"] = "passed"
    except Exception as exc:
        report["error"] = str(exc)
    finally:
        if started_pie and ue is not None:
            try:
                with endpoint_lock(a.url):
                    ue.call(EDITOR, "StopPIE")
            except Exception as exc:
                report["cleanup_error"] = str(exc)
        report["events"] = ue.events if ue else []
        output = Path(a.output); output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
        print(json.dumps({k: v for k, v in report.items() if k != "events"}, indent=2))
    return 0 if report["status"] == "passed" else 1

if __name__ == "__main__":
    raise SystemExit(main())

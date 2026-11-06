#!/usr/bin/env python3
"""Unreal Codex Studio: explicit, inspectable local operations (Python 3.11+)."""
from __future__ import annotations
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import tomllib
import uuid
from mcp_client import Client, MCPError, endpoint_lock, validate_url

ROOT = Path(__file__).resolve().parents[1]
ASSET = "editor_toolset.toolsets.asset.AssetTools"
BLUEPRINT = "editor_toolset.toolsets.blueprint.BlueprintTools"
SCENE = "editor_toolset.toolsets.scene.SceneTools"
EDITOR = "EditorToolset.EditorAppToolset"

def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))

def project_path(value):
    p = Path(value).expanduser().resolve(strict=True)
    if p.suffix != ".uproject":
        raise ValueError("Expected an existing .uproject file.")
    read_json(p)
    return p

def scan(project):
    p = project_path(project)
    data = read_json(p)
    return {"project": str(p), "engine_association": data.get("EngineAssociation"),
        "modules": data.get("Modules", []), "plugins": data.get("Plugins", []),
        "targets": [str(f.relative_to(p.parent)) for f in (p.parent / "Source").glob("*.Target.cs")],
        "source_files": sum(1 for f in (p.parent / "Source").rglob("*") if f.is_file()),
        "asset_files": sum(1 for f in (p.parent / "Content").rglob("*.uasset"))}

def engine_info(engine):
    e = Path(engine).resolve(strict=True)
    version = read_json(e / "Engine/Build/Build.version")
    plugins = e / "Engine/Plugins/Experimental"
    return {"engine": str(e), "version": version,
        "official_mcp_installed": (plugins / "ModelContextProtocol/ModelContextProtocol.uplugin").is_file(),
        "all_toolsets_installed": (plugins / "Toolsets/AllToolsets/AllToolsets.uplugin").is_file()}

class Unreal:
    def __init__(self, client):
        self.client = client
        self.schemas = {}
        self.events = []

    def describe(self, toolset):
        if toolset not in self.schemas:
            value = self.client.call("describe_toolset", {"toolset_name": toolset})
            if not isinstance(value, dict) or not isinstance(value.get("tools"), list):
                raise MCPError("Unrecognized toolset schema: " + toolset)
            self.schemas[toolset] = value
        return self.schemas[toolset]

    def call(self, toolset, name, arguments=None):
        args = arguments or {}
        schema = next((t for t in self.describe(toolset)["tools"]
            if t["name"] == toolset + "." + name), None)
        if schema is None:
            raise MCPError("Required tool unavailable: " + toolset + "." + name)
        missing = set(schema["inputSchema"].get("required", [])) - set(args)
        if missing:
            raise MCPError("Missing required arguments: " + ", ".join(sorted(missing)))
        value = self.client.call("call_tool", {"toolset_name": toolset, "tool_name": name, "arguments": args})
        # The official server owns complete JSON-schema validation.
        if isinstance(value, dict) and value.get("isError"):
            raise MCPError(json.dumps(value))
        result = value.get("returnValue", value) if isinstance(value, dict) else value
        self.events.append({"tool": toolset + "." + name, "result": result})
        return result

    def bind(self, project):
        """A random challenge proves this endpoint can read this project's Saved directory."""
        project = project_path(project)
        folder = project.parent / "Saved/UnrealCodexStudio"
        folder.mkdir(parents=True, exist_ok=True)
        token = uuid.uuid4().hex
        marker = folder / ("binding-" + token + ".txt")
        marker.write_text(token, encoding="utf-8")
        try:
            try:
                actual = self.call(ASSET, "read_file", {"file_path": str(marker)})
            except MCPError as exc:
                raise MCPError("Project binding failed: the endpoint refused the expected project's Saved challenge.") from exc
            if actual != token:
                raise MCPError("Editor project binding failed; refusing subsequent operations.")
        finally:
            marker.unlink(missing_ok=True)
        # Do not include the challenge or user path in portable evidence.
        self.events[-1] = {"tool": ASSET + ".read_file", "result": "project challenge matched"}
        return {"project": str(project), "binding": "verified"}

def connect(url):
    validate_url(url)
    path = ROOT / ".codex/config.toml"
    text = path.read_text(encoding="utf-8")
    data = tomllib.loads(text)
    if "unreal" not in data.get("mcp_servers", {}):
        raise ValueError("Missing managed [mcp_servers.unreal] section; merge config manually.")
    pattern = r"(?ms)^\[mcp_servers\.unreal\]\s*\n.*?(?=^\[|\Z)"
    def update_section(match):
        section = match.group(0)
        for key, value in [("url", json.dumps(url)), ("enabled", "true")]:
            line = key + " = " + value
            if re.search(r"(?m)^" + key + r"\s*=", section):
                section = re.sub(r"(?m)^" + key + r"\s*=.*$", lambda _: line, section)
            else:
                section = section.rstrip() + "\n" + line + "\n"
        return section
    updated, count = re.subn(pattern, update_section, text)
    if count != 1:
        raise ValueError("Expected exactly one Unreal MCP configuration section.")
    tomllib.loads(updated)
    path.write_text(updated, encoding="utf-8")
    return {"configured": str(path), "url": url, "next": "Reload Codex in this trusted workspace."}

def make_example(destination):
    dest = Path(destination).resolve()
    if dest.exists() and any(dest.iterdir()):
        raise ValueError("Example destination must be empty.")
    dest.mkdir(parents=True, exist_ok=True)
    p = dest / "StudioLab.uproject"
    p.write_text(json.dumps({"FileVersion": 3, "EngineAssociation": "5.8",
        "Category": "Tests", "Description": "Disposable official MCP studio fixture",
        "Plugins": [{"Name": "ModelContextProtocol", "Enabled": True, "TargetAllowList": ["Editor"]},
                    {"Name": "AllToolsets", "Enabled": True, "TargetAllowList": ["Editor"]}]}, indent=2) + "\n", encoding="utf-8")
    config = dest / "Config"; config.mkdir()
    (config / "DefaultEngine.ini").write_text(
        "[/Script/EngineSettings.GameMapsSettings]\nEditorStartupMap=/Engine/Maps/Templates/Template_Default\n"
        "GameDefaultMap=/Engine/Maps/Templates/Template_Default\n\n"
        "[HTTPServer.Listeners]\nDefaultBindAddress=127.0.0.1\n", encoding="utf-8")
    # AllToolsets loads GameFeatures in the editor/cooker. Its asset-manager rule
    # must not load an editor-only dependency in the packaged game.
    (config / "DefaultGame.ini").write_text(
        "[/Script/Engine.AssetManagerSettings]\n"
        '+PrimaryAssetTypesToScan=(PrimaryAssetType="GameFeatureData",'
        'AssetBaseClass="/Script/GameFeatures.GameFeatureData",bHasBlueprintClasses=False,'
        'bIsEditorOnly=True,Directories=(),SpecificAssets=(),'
        'Rules=(Priority=-1,ChunkId=-1,bApplyRecursively=True,CookRule=AlwaysCook))\n',
        encoding="utf-8")
    return {"project": str(p)}

def command_plan(kind, engine, project, target=None, platform="Win64", configuration="Development",
                 test_filter=None, archive=None, port=8000):
    e = Path(engine).resolve()
    p = project_path(project)
    windows = os.name == "nt"
    if not re.fullmatch(r"[A-Za-z0-9_]+", platform):
        raise ValueError("Invalid target platform name.")
    if not 1 <= port <= 65535:
        raise ValueError("Port must be between 1 and 65535.")
    editor = e / ("Engine/Binaries/Win64/UnrealEditor.exe" if windows else
        "Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor" if sys.platform == "darwin"
        else "Engine/Binaries/Linux/UnrealEditor")
    if kind == "launch":
        return [str(editor), str(p), "-ModelContextProtocolStartServer", f"-ModelContextProtocolPort={port}"]
    if kind == "build":
        if not target or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", target):
            raise ValueError("Supply the actual Target.cs target name with --target.")
        script = e / ("Engine/Build/BatchFiles/Build.bat" if windows else
            "Engine/Build/BatchFiles/Mac/Build.sh" if sys.platform == "darwin" else "Engine/Build/BatchFiles/Linux/Build.sh")
        return [str(script), target, platform, configuration, str(p), "-WaitMutex", "-NoHotReloadFromIDE"]
    if kind == "test":
        if not test_filter or not re.fullmatch(r"[A-Za-z0-9_. +\-]+", test_filter):
            raise ValueError("Supply a named automation test filter; console separators are forbidden.")
        return [str(editor), str(p), "-unattended", "-nop4", "-nosplash", "-NullRHI",
            "-ExecCmds=Automation RunTests " + test_filter, "-TestExit=Automation Test Queue Empty",
            "-ReportExportPath=" + str(p.parent / "Saved/UnrealCodexStudio/Automation"), "-log"]
    if kind == "package":
        if not archive:
            raise ValueError("--archive is required.")
        script = e / ("Engine/Build/BatchFiles/RunUAT.bat" if windows else "Engine/Build/BatchFiles/RunUAT.sh")
        return [str(script), "BuildCookRun", "-project=" + str(p), "-noP4", "-platform=" + platform,
            "-clientconfig=" + configuration, "-build", "-cook", "-stage", "-pak", "-archive",
            "-archivedirectory=" + str(Path(archive).resolve()), "-unattended", "-utf8output"]
    raise ValueError(kind)

def run_command(command, timeout):
    if not Path(command[0]).is_file():
        raise ValueError("Executable not found: " + command[0])
    # Windows .bat files necessarily use cmd.exe. Reject metacharacters in its arguments.
    if os.name == "nt" and command[0].lower().endswith(".bat"):
        if any(re.search(r'[&|<>^%!\r\n"]', arg) for arg in command):
            raise ValueError("Batch command arguments contain unsupported shell metacharacters.")
    folder = ROOT / ".studio"; folder.mkdir(exist_ok=True)
    log = folder / ("run-" + uuid.uuid4().hex[:8] + ".log")
    with log.open("w", encoding="utf-8") as stream:
        result = subprocess.run(command, stdout=stream, stderr=subprocess.STDOUT, timeout=timeout, check=False)
    return {"command": command, "exit_code": result.returncode, "log": str(log),
        "note": "Inspect engine reports; process exit alone does not prove gameplay or test success."}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    s = sub.add_parser("scan"); s.add_argument("--project", required=True)
    s = sub.add_parser("example"); s.add_argument("--destination", required=True)
    s = sub.add_parser("connect"); s.add_argument("--url", required=True)
    s = sub.add_parser("doctor"); s.add_argument("--project", required=True); s.add_argument("--engine", required=True)
    s.add_argument("--url")
    s = sub.add_parser("mcp"); s.add_argument("action", choices=["list", "describe", "call"])
    s.add_argument("--url", required=True); s.add_argument("--toolset"); s.add_argument("--tool")
    s.add_argument("--arguments-file"); s.add_argument("--project")
    for kind in ["launch", "build", "test", "package"]:
        s = sub.add_parser(kind)
        s.add_argument("--engine", required=True); s.add_argument("--project", required=True)
        s.add_argument("--target"); s.add_argument("--platform", default="Win64")
        s.add_argument("--configuration", choices=["Debug", "DebugGame", "Development", "Shipping", "Test"], default="Development")
        s.add_argument("--test-filter"); s.add_argument("--archive"); s.add_argument("--port", type=int, default=8000)
        s.add_argument("--run", action="store_true"); s.add_argument("--timeout", type=int, default=3600)
    args = parser.parse_args()
    try:
        if args.command == "scan":
            result = scan(args.project)
        elif args.command == "example":
            result = make_example(args.destination)
        elif args.command == "connect":
            result = connect(args.url)
        elif args.command == "doctor":
            result = {"project": scan(args.project), "engine": engine_info(args.engine)}
            enabled = {v["Name"] for v in result["project"]["plugins"] if v.get("Enabled")}
            result["explicit_plugins_enabled"] = {"ModelContextProtocol", "AllToolsets"} <= enabled
            if args.url:
                with endpoint_lock(args.url):
                    client = Client(args.url); result["server"] = client.initialize()
                    result["binding"] = Unreal(client).bind(args.project)
            result["ready"] = (result["engine"]["official_mcp_installed"] and
                result["engine"]["all_toolsets_installed"] and result["explicit_plugins_enabled"])
        elif args.command == "mcp":
            with endpoint_lock(args.url):
                client = Client(args.url); client.initialize(); ue = Unreal(client)
                if args.action == "list":
                    result = client.call("list_toolsets")
                elif args.action == "describe":
                    if not args.toolset:
                        raise ValueError("--toolset is required.")
                    result = ue.describe(args.toolset)
                else:
                    if not all([args.project, args.toolset, args.tool]):
                        raise ValueError("Calls require --project, --toolset and --tool.")
                    ue.bind(args.project)
                    result = ue.call(args.toolset, args.tool,
                        read_json(args.arguments_file) if args.arguments_file else {})
        else:
            command = command_plan(args.command, args.engine, args.project, args.target, args.platform,
                args.configuration, args.test_filter, args.archive, args.port)
            result = run_command(command, args.timeout) if args.run else {"command": command, "executed": False}
        print(json.dumps(result, indent=2, ensure_ascii=True))
        if isinstance(result, dict) and (result.get("ready") is False or result.get("exit_code", 0) != 0):
            return 1
        return 0
    except (OSError, ValueError, MCPError, subprocess.TimeoutExpired) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=True), file=sys.stderr)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())

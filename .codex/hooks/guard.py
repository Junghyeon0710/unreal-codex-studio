"""Narrow patch guard and lifecycle audit; not a sandbox or shell security boundary."""
import datetime as dt
import json
from pathlib import Path
import re
import sys

def evaluate(payload):
    event = payload.get("hook_event_name", "")
    tool = payload.get("tool_name", "")
    value = payload.get("tool_input", "")
    if isinstance(value, dict):
        value = value.get("command", value.get("cmd", value.get("patch", value.get("input", ""))))
    if event == "PreToolUse" and tool == "apply_patch" and isinstance(value, str):
        paths = re.findall(r"^\*\*\* (?:Add File|Update File|Delete File|Move to): (.+)$", value, re.M)
        if any(Path(p.strip()).suffix.lower() in {".uasset", ".umap"} for p in paths):
            return {"hookSpecificOutput": {"hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": "Binary Unreal assets must be edited through official MCP."}}
    return {}

def main():
    payload = json.load(sys.stdin)
    if len(sys.argv) > 1:
        payload["hook_event_name"] = sys.argv[1]
    result = evaluate(payload)
    if payload.get("hook_event_name") in {"SubagentStart", "SubagentStop"} or result:
        root = Path(__file__).resolve().parents[2]
        folder = root / ".studio"; folder.mkdir(exist_ok=True)
        entry = {"utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            "event": payload.get("hook_event_name"), "agent_id": payload.get("agent_id"),
            "agent_type": payload.get("agent_type"), "denied": bool(result)}
        with (folder / "hooks.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(entry) + "\n")
    print(json.dumps(result))

if __name__ == "__main__":
    main()

"""Validate distributable configuration and skill structure (no Unreal required)."""
import ast
import json
from pathlib import Path
import re
import tomllib
import yaml

ROOT = Path(__file__).resolve().parents[1]

def main():
    errors = []
    skills = list((ROOT / ".agents/skills").glob("*/SKILL.md"))
    roles = list((ROOT / ".codex/agents").glob("*.toml"))
    for path in skills:
        try:
            raw = path.read_text(encoding="utf-8")
            front = yaml.safe_load(raw.split("---", 2)[1])
            assert front["name"] == path.parent.name
            assert re.fullmatch(r"[a-z0-9-]+", front["name"])
            assert isinstance(front["description"], str) and front["description"].strip()
            interface = yaml.safe_load((path.parent / "agents/openai.yaml").read_text(encoding="utf-8"))["interface"]
            assert "$" + front["name"] in interface["default_prompt"]
        except (ValueError, KeyError, AssertionError, OSError, yaml.YAMLError) as exc:
            errors.append(str(path.relative_to(ROOT)) + ": " + repr(exc))
    for path in roles:
        try:
            data = tomllib.loads(path.read_text(encoding="utf-8"))
            assert data["name"] == path.stem
            assert data["description"] and data["developer_instructions"]
            assert data["model"] == ("gpt-6-astra" if path.stem == "technical-director" else "gpt-6.1-sol")
            assert "sandbox_mode" not in data
        except (ValueError, KeyError, AssertionError) as exc:
            errors.append(str(path.relative_to(ROOT)) + ": " + repr(exc))
    config = tomllib.loads((ROOT / ".codex/config.toml").read_text(encoding="utf-8"))
    assert config["model"] == "gpt-6-astra"
    assert {"code-implementer", "code-reviewer", "editor-engineer", "verification-engineer", "qa-engineer"} <= {p.stem for p in roles}
    json.loads((ROOT / ".codex/hooks.json").read_text(encoding="utf-8"))
    for folder in ["tools", "tests", ".codex/hooks"]:
        for path in (ROOT / folder).rglob("*.py"):
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    assert len(skills) == 15, "Update manifest/docs when changing the skill inventory."
    assert len(roles) == 13, "Update manifest/docs when changing the role inventory."
    print(json.dumps({"skills": len(skills), "roles": len(roles), "errors": errors}, indent=2))
    return bool(errors)

if __name__ == "__main__":
    raise SystemExit(main())

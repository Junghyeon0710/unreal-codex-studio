# Getting started

Use this repository as a separate Codex workspace. Point commands at your actual
.uproject; do not copy over an existing AGENTS.md or .codex directory.

1. Install Python 3.11+ and a Codex host supporting project skills and custom roles.
2. Install your licensed Unreal Engine distribution containing the official MCP
   plugins. See docs/validation-results.md for the exact tested versions.
3. Open this repository in Codex and review/trust the project. Hooks have separate
   trust requirements; inspect .codex/hooks/guard.py before enabling them.
4. Enable official Unreal MCP and All Toolsets in the intended Unreal project and
   restart. Start the server as described in docs/official-mcp.md.
5. Run doctor with the actual engine, project and local endpoint.
6. Run connect and reload Codex. Describe the work normally; skill names are
   optional. Use $ue-start only when you want to select that workflow explicitly.

For source work in a game outside this workspace, add that game directory to your
Codex host's authorized workspace roots. Do not disable the sandbox or copy its
source into this repository as a workaround. Asset operations run inside Unreal's
process and still require the correct project and user scope.

The scripts need no pip packages. Contributor validation uses PyYAML:
`python -m pip install -r requirements-dev.txt`.
Run `python tools/validate.py` and `python -m unittest discover -s tests -v`.

## Choose work to fit the request

The Astra manager chooses the smallest sufficient roster, scopes and useful checks
without asking routine staffing questions. A narrow task may use one expert;
explanations/read-only answers may need no delegation or journal. Editor work needs
one actual owner; code review, builds, packaging and gameplay QA are selected only
when meaningful. See [adaptive management](feature-loop.md). Historical five-worker
examples are optional integration evidence, not the default team size.

## Builds and tests

Commands are plans unless --run is provided. This allows inspection without
launching or mutating anything:

```text
python tools/studio.py build --engine <engine> --project <game.uproject> --target MyGameEditor
python tools/studio.py test --engine <engine> --project <game.uproject> --test-filter MyGame.Inventory
python tools/studio.py package --engine <engine> --project <game.uproject> --archive <output-folder>
```

Use the actual target name, platform, SDK and test filter. Existing Blueprint-only
projects need no invented C++ Editor target. Read the log path returned by --run;
automation execution also requires checking exported report totals. Launch runs
in the foreground until the editor closes; in Windows background automation use
Start-Process with -WindowStyle Hidden and retain only your own process ID.

## Existing project plugin settings

The included fixture enables two plugins in a new empty project only. It does not
edit your game's .uproject. Keep editor tooling excluded from shipping targets using
the plugin/target rules appropriate to your engine. Package support depends on your
project, maps, SDK and enabled plugins; the studio does not certify arbitrary games.

## Troubleshooting

- Missing plugin: inspect the installed engine; this repository supplies no engine port.
- Connection refused: wait for editor startup, check the explicit port and server log.
- Wrong project: close no unrelated editor; select the correct endpoint and rerun doctor.
- Schema mismatch: rediscover the toolset; record the version and unsupported operation.
- Skills/roles absent: check project trust and host support. A sequential fallback
  must be disclosed; do not claim multiagent execution merely from TOML files.
- Native CLI subagents: the tested Codex 0.167 build required a persisted parent
  session. Its --ephemeral mode could not fork a rollout; see validation results.

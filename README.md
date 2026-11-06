English · [한국어](docs/readme/README_ko.md)

# Unreal Codex Studio

[![Validate](https://github.com/Junghyeon0710/unreal-codex-studio/actions/workflows/validate.yml/badge.svg)](https://github.com/Junghyeon0710/unreal-codex-studio/actions/workflows/validate.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**An Unreal development workspace for Codex, powered by Epic's official Unreal MCP.**

Includes 15 skills, 13 role definitions, adaptive Astra management, project binding checks, an MCP client, and
command-line tools for builds, tests, and packaging. Reuse development workflows
across projects and keep evidence of what actually ran in the engine.

This is an independent community project, not an official Epic Games or OpenAI product.

[Read the local door validation report](docs/studio-door-validation.md).
The door test project, generated assets, packaged game and captured media remain
local; only the curated results are published.

> Unreal MCP is Experimental. **MCP operations, C++ builds, and packaged execution
> have been tested on Windows with Unreal Engine 5.8.4.**
> See [validation results](docs/validation-results.md) for the exact scope and Codex runtime evidence.
> Python CI does not run Unreal Engine or a game.

## What's included?

- **Specialist roles:** Astra direction, Sol code implementation/review, editor engineering, verification, QA, plus C++, Blueprints, gameplay, UI, networking, builds and performance.
- **Official editor connection:** ModelContextProtocol + AllToolsets, using Epic's server directly.
- **Project checks:** verify the connected editor belongs to the intended project; assign one owner to editor changes.
- **Reproducible tools:** project scanning, doctor checks, live schema discovery, command planning/execution, and isolated editor smoke tests.
- **Separate evidence:** report source checks, C++ builds, Blueprint compilation, PIE, gameplay, and packaged execution individually.

```mermaid
flowchart LR
  U[User request] --> C[Codex / Technical director]
  C --> S[C++ / Gameplay / Review]
  C --> E[Single editor owner]
  E --> M[Epic official Unreal MCP]
  M --> UE[Unreal Editor]
  S --> V[QA / Verification evidence]
  UE --> V
```

Installing role files does not launch agents. The Astra manager chooses the
smallest sufficient roster for each task, using the requested scope, dependencies,
risk and meaningful checks. It decides routine staffing without asking the user,
and adds or reassigns specialists when findings justify it.

## Adaptive task management

A short explanation may need only the manager or one researcher. A material change
may need one editor specialist. A code defect may warrant an author and independent
reviewer; a larger feature may justify more specialists. These are examples, not a
fixed team size. Select independent review when useful, requested or claimed; its
author cannot serve as its independent reviewer. Editor, build, packaging and
independent gameplay QA work are selected only when meaningful for the task.

```mermaid
flowchart LR
  R[Actual request] --> M[Astra manager]
  M --> P[Select sufficient roles, scopes and checks]
  P --> W[Launch selected Sol workers if useful]
  W --> F[Findings and observed evidence]
  F --> M
  M --> C[Complete selected scope or report limits]
```

`gpt-6-astra` is the root/technical-director default; selected specialist roles
explicitly use `gpt-6.1-sol`. This applies to new compatible sessions and does not
change an existing chat's model, sandbox or approval policy. Actual delegation
uses host calls; role files and journals do not authenticate identities or launch
workers. One designated owner exclusively controls all official MCP calls,
binary assets and PIE whenever editor work is selected.

For tracked multi-step work, optional `tools/studio_pipeline.py` records the selected
roster, scoped snapshot, stages, required checks and reasoned plan changes. It rejects
missing selected checks, stale source/evidence and conflicting editor custody.
Explanation/read-only answers do not need a journal or implementation pipeline.
Historical five-worker journals and an explicit `--profile strict-five` integration
profile remain compatible; they are not mandatory staffing. The optional two-worker
`review_loop.py` retains its own purpose. See [adaptive workflow](docs/feature-loop.md).

The [completed five-worker door experiment](docs/studio-door-validation.md) is
historical evidence for its frozen snapshot. Its recorded 35-test gate does not
validate later adaptive-policy/tool changes.

## Quick start

Requirements: Python 3.11+, Codex, and an Unreal Engine installation containing
the official MCP plugins. **UE 5.8.4** is the tested version. UE 5.7 backports and
other engine versions have not been validated by this repository.

```sh
git clone https://github.com/Junghyeon0710/unreal-codex-studio.git
cd unreal-codex-studio
python tools/studio.py --help
```

1. Open this folder in Codex, review its contents, and trust the project.
2. Enable **Unreal MCP** and **All Toolsets** in your Unreal project, then restart the editor.
3. Run `ModelContextProtocol.StartServer 8000` in the editor console.
4. Check the exact project and engine paths, then enable the Codex connection.

```powershell
python tools/studio.py doctor --engine "D:/Epic Games/UE_5.8" --project "D:/Games/MyGame/MyGame.uproject" --url http://127.0.0.1:8000/mcp
python tools/studio.py connect --url http://127.0.0.1:8000/mcp
```

Reload Codex and ask:

```text
My project is D:/Games/MyGame/MyGame.uproject.
My engine is D:/Epic Games/UE_5.8.
Verify the official MCP connection and explain the current module structure.
```

Skill names are optional. Codex can select a skill when your request matches its
description. You can write "Add a door that opens when the player approaches" or
"Find the cause of this build error"; the workspace instructions guide workflow
and role selection. Use `$ue-feature` or another skill name when you want to select
a workflow explicitly. See [OpenAI's skill invocation documentation](https://learn.chatgpt.com/docs/build-skills).

Open this repository as the Codex workspace so its project skills are available.
Automatic selection follows the request and available host capabilities; it does
not launch every role or expand permission to modify the project.

You can also copy `studio.local.example.json` to `studio.local.json` to record
your paths. That file is ignored by Git. CLI commands still require explicit path
arguments to reduce mistakes. Use this repository as a separate Codex workspace
pointing at your game project.

## Skills

| Skill | Purpose |
|---|---|
| `$ue-start` | Start a project session and route the task |
| `$ue-doctor` | Check the engine, official plugins, and connected project |
| `$ue-project-scan` | Inspect modules, plugins, and targets |
| `$ue-feature` | Implement with task-appropriate roles and checks |
| `$ue-cpp` | Work with C++, UHT, and object lifetimes |
| `$ue-blueprint` | Edit and compile Blueprints through MCP |
| `$ue-ui` | Work with UMG and CommonUI |
| `$ue-data` | Work with DataTables, DataAssets, and source data |
| `$ue-review` | Review changes |
| `$ue-build` | Build with UBT |
| `$ue-test` | Verify Unreal Automation results |
| `$ue-pie-check` | Start, observe, and stop PIE |
| `$ue-package` | Cook and package with UAT |
| `$ue-package-smoke` | Verify packaged startup and behavior |
| `$ue-diagnose` | Diagnose failures from logs and evidence |

For GAS, Niagara, PCG, World Partition, and other features, discover the toolsets
actually installed when the project needs them. Do not assume a fixed tool count
or universal feature support.

## Run a live test

The following test **creates assets in a disposable project**. Use a separate
fixture rather than an existing game.

```powershell
python tools/studio.py example --destination "../StudioLab"
python tools/studio.py launch --engine "D:/Epic Games/UE_5.8" --project "../StudioLab/StudioLab.uproject" --port 8017
```

By default, `launch` prints a command plan. Run the printed command or add
`--run` to launch the editor. Once the editor is ready:

```powershell
python tools/live_smoke.py --project "../StudioLab/StudioLab.uproject" --url http://127.0.0.1:8017/mcp --output ".studio/live-smoke.json" --allow-fixture-write
```

Checks: project binding → Blueprint creation and compilation → selected asset
save and disk verification → actor spawn and discovery → PIE start and stop.
The test leaves its assets in the fixture for inspection and does not save the map.

Use the separate [C++ smoke fixture](examples/cpp-smoke/README.md) to reproduce
C++ builds and Windows packaged execution. The [build, package, and runtime report](docs/build-package-validation.md)
also records failures found and fixed during validation.

## Repository layout

```text
AGENTS.md                  Shared working agreement
.agents/skills/            15 Unreal skills
.codex/agents/             13 Codex roles
.codex/hooks/              Binary patch guard and role lifecycle audit
.codex/config.toml         Roles and MCP settings (connection disabled by default)
tools/                    Python standard-library tooling
tests/                    Standalone toolkit tests
templates/                Feature and verification templates
docs/                     Setup, MCP, compatibility, and validation
docs/readme/README_ko.md   Korean README
```

Read more: [Setup](docs/getting-started.md) · [Official MCP](docs/official-mcp.md) ·
[Verification](docs/verification.md) · [Contributing](CONTRIBUTING.md) · [Lineage and licensing](UPSTREAM.md)

## License

MIT. Adapted for Unreal and Codex from the studio organization in
[Claude Code Game Studios](https://github.com/donchitos/claude-code-game-studios).
The original copyright notice is preserved. Unreal Engine and Epic plugin source
code and binaries are not distributed with this repository.

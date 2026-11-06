# Unreal Codex Studio

This workspace supplies Unreal workflows; the game project may live elsewhere.
Read studio.local.json when present for user-selected paths. Never infer a project from
an open editor or replace a user's engine/model/approval settings.

## Working agreement

- Use Epic's official ModelContextProtocol + AllToolsets plugins. Before operations,
  read docs/official-mcp.md and run tools/studio.py doctor with the exact .uproject,
  engine root and endpoint. Discover live tool schemas; do not assume tool counts.
- One agent owns all editor calls and binary assets at a time. Independent source
  analysis can run in parallel when delegation is authorized and available. Give
  each worker a nonoverlapping scope and return artifact; otherwise work sequentially.
- Native roles live in .codex/agents. Skills live in .agents/skills.
  Role files do not themselves launch agents or grant permissions.
- Use official MCP for assets, graphs, levels and PIE. Never hand-edit .uasset/.umap
  or substitute ad hoc Python execution inside the editor. Normal Python tooling
  outside Unreal for HTTP, builds and reports is supported.
- Check the expected project immediately before mutations. The toolkit's binding
  challenge verifies the server's project Saved directory; native MCP callers must
  also run doctor before their editor sequence.
- Preserve existing work. Do not save every dirty asset, overwrite maps, reset Git,
  or terminate unrelated editors. Honor the user's existing authorization without
  adding repetitive approval gates.
- Shipped root/technical-director defaults are gpt-6-astra; specialist role files
  ship with gpt-6.1-sol. They are configurable defaults, not mandatory identities.
  Respect edited model IDs and omitted model fields; never force the shipped model
  after a user override. Omitted role model inherits host resolution (explicit
  spawn model, then agents.default_subagent_model, then parent). This repository
  ships no default_subagent_model. Omit/comment out model to inherit, not "inherit".
  Root config affects new root sessions; technical-director is a separate spawned
  role, and existing chats keep their models. Preserve sandbox/approval policy.
  Unsupported IDs are host/provider failures, not permission to substitute silently.
- Follow docs/verification.md: instructions loaded, source checks, engine compile,
  Blueprint compile/save, PIE, gameplay and packaged startup are separate results.
- Send short progress updates. Report what changed, actual evidence and remaining
  limitations. Missing tools or SDKs are not passes.

## Natural-language requests

Users can describe work in ordinary language, including Korean, without naming a
skill or role. Select and read the relevant .agents/skills/*/SKILL.md from the
request's intent; do not ask the user to repeat it with a dollar-prefixed command.
Use the smallest applicable workflow, and preserve an explicit skill choice.

| Requested work | Relevant workflow |
|---|---|
| Start work or understand the project | ue-start / ue-project-scan |
| Add gameplay behavior | ue-feature, then the needed C++ / Blueprint / UI skills |
| Diagnose a broken build or editor operation | ue-diagnose; ue-build only if a build is needed |
| Edit a widget, Blueprint, or data asset | ue-ui / ue-blueprint / ue-data |
| Review changes | ue-review |
| Verify behavior in the editor | ue-pie-check / ue-test |
| Produce or check a packaged game | ue-package / ue-package-smoke |
| Investigate the editor connection | ue-doctor |

The Astra manager selects the smallest sufficient roster for each task, using
actual scope, dependencies, risk and meaningful checks. Decide routine staffing
without asking the user. A narrow task may use one expert; explanations/read-only
answers may be handled directly without delegation or a journal. Add or reassign
workers when findings justify it. See docs/feature-loop.md for adaptive planning.

Use actual host calls for selected workers; files/journals do not launch agents.
Record real IDs/model attribution when tracking a run. Never invent workers or
claim independent review by the author. Select an independent reviewer when useful,
requested or claimed; only selected review and verification stages are required.
Editor specialists are needed only for actual editor/asset work; build, packaging
and gameplay QA checks are included only when meaningful for the task. One actual
owner exclusively controls all official MCP calls (including reads), binary assets
and PIE. Preserve safety and project binding without imposing an editor stage on
source-only work.

The manager may use tools/studio_pipeline.py for multi-step tracked work, selecting
participants/stages/checks and recording reasoned plan changes. Previous failed or
unrun checks remain in history; changed acceptance is not a retroactive pass. Route
findings to the responsible author, re-review when selected, and bound repairs
(three cycles by default for tracked tasks). Complete only the selected scope with
current evidence. Missing tools/delegation remain explicit limitations. Do not
expand review-only, explanation or planning requests into implementation. Honor
existing user authorization and explicit choices. Historical five-worker examples
are evidence of those runs, not a mandatory roster for every new request.

## Commands

Python 3.11+; runtime scripts use the standard library only.

```text
python tools/studio.py scan --project <game.uproject>
python tools/studio.py doctor --engine <engine-root> --project <game.uproject> --url http://127.0.0.1:8000/mcp
python tools/studio.py mcp list --url http://127.0.0.1:8000/mcp
```

Use --help for command plans and explicit execution. See docs/getting-started.md.

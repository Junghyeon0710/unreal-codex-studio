# Upstream studio architecture

Inspected `Donchitos/Claude-Code-Game-Studios` on 2026-11-06. This is a source and workflow comparison, not an execution test of upstream. Links follow upstream `main` and may change.

## Yes: upstream already has a studio hierarchy

Upstream organizes directors, department leads, and specialists into three tiers. Its coordination rules describe actual subagent calls through Claude Code's Agent tool, with sequential execution for dependencies and parallel execution for independent tasks. Experimental multi-session Agent Teams are a separate option. [Coordination rules](https://github.com/Donchitos/Claude-Code-Game-Studios/blob/main/.claude/docs/coordination-rules.md)

The model assignments are mixed: three directors use Opus, sixteen agents are pinned to Sonnet, and thirty inherit the calling model. An agent's model and a skill's model are separate settings. It is therefore inaccurate to describe every upstream workflow as one Opus director running an exclusively Sonnet workforce. [Model tiers](https://github.com/Donchitos/Claude-Code-Game-Studios/blob/main/.claude/docs/model-tiers.md)

The technical director's instructions emphasize architecture and delegation, and explicitly exclude direct gameplay implementation. The role is one part of the workflow; the team skills also contain orchestration logic. [Technical director](https://github.com/Donchitos/Claude-Code-Game-Studios/blob/main/.claude/agents/technical-director.md)

## A role catalog does not mean every role runs

Upstream's team workflows select the active roster from configuration. For example, `team-level` defaults to an individual team with the level designer active; larger settings add design, art, QA, narrative, and accessibility roles. It requires announcing which members are actually spawned and which remain consultation targets. That skill has no director gate. [Level team workflow](https://github.com/Donchitos/Claude-Code-Game-Studios/blob/main/.claude/skills/team-level/SKILL.md)

`dev-story` selects programmers and engine specialists from the story's needs. Some configuration-only work needs no delegated implementation. Its instructions distinguish implementation, runtime checks, review, and completion. [Story implementation workflow](https://github.com/Donchitos/Claude-Code-Game-Studios/blob/main/.claude/skills/dev-story/SKILL.md)

The QA team defines real QA roles and evidence requirements, but its manual QA phase requests results from a human tester. These instructions alone do not establish autonomous Unreal editor control or a successful packaged-game test. [QA team workflow](https://github.com/Donchitos/Claude-Code-Game-Studios/blob/main/.claude/skills/team-qa/SKILL.md)

## Current Unreal Codex Studio management

The Astra manager selects the smallest sufficient roster for the actual request,
then assigns scopes, dependencies and meaningful checks. It decides routine
staffing autonomously and adds/reassigns workers when findings justify it. The
requested model defaults remain `gpt-6-astra` for management and `gpt-6.1-sol` for
selected specialists; this does not retroactively change an existing root chat.

| Example task | Possible selected team | Relevant evidence |
|---|---|---|
| Explain behavior | Manager alone or one researcher | Source-backed answer; no mandatory journal |
| Edit a material | One editor specialist | Correct project, assigned asset edit/save/readback |
| Repair a code defect | Code author; reviewer when useful | Relevant tests and selected independent review |
| Implement a larger feature | Sufficient code/editor/build/QA roles | Checks chosen from actual acceptance and risk |

These examples are not fixed templates or a mandatory five-person pipeline.
Independent review is used when relevant, requested or claimed and cannot be
performed independently by the author. Build, packaging and gameplay QA are not
universal requirements. Only one actual owner controls official MCP, binary assets
and PIE when editor work is needed. Selected work still uses real host launches,
not invented journal agents; skipped/unrun checks remain honestly described.

The optional adaptive journal records selected stages/checks and reasoned plan
changes. Native role files do not create agents, and metadata does not authenticate
identities or prove a model by itself. See [adaptive workflow](feature-loop.md).

The [five-worker door experiment](studio-door-validation.md) was a real completed
historical integration run against its own frozen snapshot. It demonstrated one
roster, not a universal staffing policy. Its source review, 35 tests, engine results
and gate are not approval of later adaptive-tool changes. Existing journals remain
readable; `--profile strict-five` deliberately opts into that integration profile.
This comparison is not an upstream execution test or a test certificate.

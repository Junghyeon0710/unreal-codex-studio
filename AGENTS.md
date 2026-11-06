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
- Models, sandbox and approval settings inherit from the host. Do not weaken them.
- Follow docs/verification.md: instructions loaded, source checks, engine compile,
  Blueprint compile/save, PIE, gameplay and packaged startup are separate results.
- Send short progress updates. Report what changed, actual evidence and remaining
  limitations. Missing tools or SDKs are not passes.

## Commands

Python 3.11+; runtime scripts use the standard library only.

```text
python tools/studio.py scan --project <game.uproject>
python tools/studio.py doctor --engine <engine-root> --project <game.uproject> --url http://127.0.0.1:8000/mcp
python tools/studio.py mcp list --url http://127.0.0.1:8000/mcp
```

Use --help for command plans and explicit execution. See docs/getting-started.md.

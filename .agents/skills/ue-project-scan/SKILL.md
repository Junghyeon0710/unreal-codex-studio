---
name: ue-project-scan
description: "Inventory an Unreal project without editing code or assets."
---

# ue-project-scan

Run python tools/studio.py scan --project with the exact .uproject. Inspect Source/*.Target.cs, module .Build.cs, Config and enabled project plugins. Summarize engine association, module boundaries, runtime/editor separation, target platforms and likely feature owners. Do not load all binary assets to produce a source inventory. Keep generated/local engine artifacts out of Git.

Follow the workspace AGENTS.md and current user authorization. Use tools actually available in this session. Report observed results and material limits.

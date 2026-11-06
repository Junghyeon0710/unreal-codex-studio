---
name: ue-review
description: "Review Unreal source and asset changes for actionable correctness issues."
---

# ue-review

Inspect the actual diff and surrounding call sites. Check lifetime, authority, UHT, async/game-thread usage, assets/references, module dependencies and test evidence. Coordinate any official MCP binary inspection through the selected single editor owner; otherwise mark asset behavior unverified. Report concrete trigger, consequence and location. Avoid speculative findings or treating style preferences as bugs.

When assigned as the independent reviewer in [the feature loop](../../../docs/feature-loop.md),
do not edit the implementation or approve your own changes. Review the supplied
acceptance criteria and exact source snapshot; include its digest in the report.
Return approve with no unresolved findings, or request_changes with stable finding
IDs, severity, location, trigger, consequence and evidence. The coordinator sends
repairs to the implementation worker. On re-review, confirm each previous finding
against the actual changed files and check for regressions; a claimed fix is not
evidence. A review-only user request remains review-only. This skill applies to selected/requested review; it does not require an independent reviewer for every task.

Follow the workspace AGENTS.md and current user authorization. Use tools actually available in this session. Report observed results and material limits.

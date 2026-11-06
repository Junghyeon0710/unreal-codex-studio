---
name: ue-package-smoke
description: "Test startup of a built Unreal game separately from packaging success."
---

# ue-package-smoke

Read docs/verification.md. Select the exact produced executable and run it with a bounded, task-owned process and log path. Verify entry map, initialization and the requested interaction or automated assertion. Retain crash/exit evidence. A process that survives briefly or produces a screenshot is only startup evidence, not complete gameplay validation. Stop only the process created for this test.

Follow the workspace AGENTS.md and current user authorization. Use tools actually available in this session. Report observed results and material limits.

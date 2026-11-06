# Evidence levels

| Stage | Required observation | Does not prove |
|---|---|---|
| Configuration | TOML/skill validation and actual host loading | Engine behavior |
| Source/tool tests | Assertions and test counts | Unreal compilation |
| Engine build | Correct target/configuration, successful UBT log | Gameplay |
| Blueprint | Compile outcome, selected save and read-back | Interaction correctness |
| PIE | Start acknowledged, running state observed, stop observed | Full game feature |
| Gameplay | Concrete input/state/output assertions | Other devices or networking |
| Automation | Nonzero executed count, completed report, failures checked | Visual quality |
| Package | Successful UAT/cook, expected output files | Packaged startup |
| Packaged smoke | Task-owned process, startup/map/behavior evidence | Long playthrough |

Use passed, failed or not_run for each stage. Keep the actual command/tool, engine
version, environment and evidence path. Do not silently downgrade a failed test to
not_run. A later successful rerun should preserve the reason for the earlier failure.

tools/live_smoke.py creates a unique empty Actor Blueprint, compiles it, saves its
.uasset, spawns an instance and verifies PIE start/stop. It does not implement
gameplay, save the test map, test multiplayer, package a game or test every toolset.

Tests may leave uniquely named fixture assets for inspection. Never use blanket
save-all or delete-all cleanup in a user's project. An interrupted/failed request
may have completed in the editor; inspect state before retrying a mutation.

## Recording runtime evidence

Use templates/verification.md for human-readable results. Runtime logs belong in
.studio or the test project's Saved directory. Before publishing curated evidence,
remove personal paths, tokens, unrelated project data and large binary output.
Keep the test script and exact assertion outcomes so another user can reproduce it.

# Door implementation and independent review

English · [한국어](ko/door-demo.md)

[Machine-readable results](evidence/door-demo.json)

This is a historical local test report. The door source project, generated assets,
packaged game, original logs, screenshots and video remain local and are not
distributed. The local 60-second video used actual engine frames at fixed 30 fps;
it was not a performance benchmark.

## Actual agent collaboration

The Codex desktop host started distinct workers. The coordinator defined the
criteria, assigned source ownership and remained the only editor/MCP owner.

| Host worker | Work actually performed |
|---|---|
| `/root/door_implementer` | Authored the native C++ door, scene, demo pawns, HUD and gameplay assertions |
| `/root/door_reviewer` | Independently reviewed source and later the raw build, PIE, package and capture evidence |
| `/root/workflow_implementer` | Implemented the collaboration instructions and journal gate; repaired the reviewer's finding |

The door itself passed initial independent source review without an actionable
finding. We did not insert a bug to manufacture a repair demonstration. During
review of the collaboration tooling, the reviewer independently reproduced **W1**:
changing source after submission but before review blocked both review and
resubmission. The same workflow author added explicit bounded stale-pending
supersession, preserving the old record and requiring fresh review and evidence.
The independent reviewer re-tested and approved the repair. The
[recorded review loop](evidence/feature-loop.json) retains both rounds and findings.

This test used real host collaboration sessions with assigned roles. It does not
claim that all nine native TOML roles ran, or that the journal authenticates worker
identity. See [the reusable workflow](feature-loop.md).

## Observed results — 2026-11-06

Windows / Unreal Engine 5.8.4 / Win64 Development / D3D12. The fixture was copied to
a disposable location. The user's existing game was not changed.

| Stage | Observed result |
|---|---|
| Python toolkit | 28 tests passed, including 12 review-loop tests |
| Configuration | 15 skills and 9 role definitions valid |
| C++ editor build | Passed, 12 actions; wrapper elapsed 104.72 seconds |
| Official MCP | Expected-project binding; door Blueprint subclass create/compile/save/read-back; PIE start/stop |
| PIE gameplay | All 12 named assertions passed |
| UAT packaging | Passed; wrapper elapsed 206.77 seconds |
| Normal packaged run | All 12 assertions passed, exit 0, zero error logs; one NVIDIA TSR driver warning |
| Frame capture | All 12 assertions passed, exit 0, 557 engine frames |
| Completion gates | Door round 1 and workflow round 2 both complete |

The normal scenario advances for 18.50 game seconds; launch-through-exit wall time
was 75.03 seconds. Capture wall time was 68.62 seconds. These are observed run
durations, not speed claims. The independent reviewer checked raw results, source
hashes, run identifiers, logs and representative motion frames; see the
[final review](evidence/door-runtime-review.json).

The twelve assertions check initial closure, ignoring a non-pawn, opening for a
pawn, retaining a pawn when one overlap component leaves, deduplicating two pawns,
remaining open while one occupant stays, closing after the last occupant is
destroyed, opening for another pawn, entering the middle of a close, continuous
reversal, reopening fully and closing after everyone leaves. The scenario moves
real `APawn` objects through actual engine overlap detection and reads the hinge's
actual rotation. It is a scripted standalone test, not a manual player-input test.

## Scope and reproduction

The exact door fixture is local-only, so this report is not a downloadable
reproduction kit. Normal runs required a fresh `DoorRunId`, the
expected JSON report, screenshot, every assertion passing, a normal exit and log
inspection. A successful compiler or process exit alone is insufficient.

For capture, use `-DoorCapture -DumpMovie -usefixedtimestep -fps=30` and set a
temporary `GameScreenshotSaveDirectory` through an engine INI command-line
override. Capture skips the single screenshot-name assertion because DumpMovie
uses numbered frame names; the separate normal runtime requires that screenshot.

MCP creates and validates a Blueprint subclass of the door. The gameplay sequence
uses the native C++ actor spawned by the game mode; these are distinct checks.
The editor generated local Android File Server settings in the runtime copy.
Those settings are excluded from the source example and public evidence; full
runtime INI files are not claimed byte-identical to the clean source template.
The published executable hash identifies the top-level launcher only.

Not tested: multiplayer, Shipping, manual keyboard/controller input, save/load,
long playthroughs, other engine versions or a full Unreal Automation suite.
The video, screenshots, original C++ fixture and generated game assets remain
local. Epic engine/plugin source and packaged binaries are not distributed.


Current Astra/Sol five-specialist placed-Blueprint validation is documented in the [new run report](studio-door-validation.md). The locally retained video is historical and does not depict that run.

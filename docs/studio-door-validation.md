English · [한국어](ko/studio-door-validation.md)

# Astra studio: placed Blueprint door validation

> Historical five-worker integration experiment. Results below apply only to its recorded frozen snapshot, before the adaptive-management correction. The old 35-test result and gate do not validate the current changed source. Current staffing policy is [adaptive](feature-loop.md); there is no universal five-worker requirement.

Run date: 2026-11-06. **Complete: independent review, editor work, technical verification and gameplay QA
passed; the current round-2 gate returned exit 0.** Source approval and a successful C++ rebuild
do not establish completion of the five-specialist pipeline.

## Actual sessions and model attribution

The existing root chat was not retroactively switched to another model. It
launched a separate director session, `/root/astra_director`, explicitly using
`gpt-6-astra`. That director used actual host calls to assign five distinct
`gpt-6.1-sol` specialist sessions:

| Responsibility | Actual host session ID | Explicit model |
|---|---|---|
| Director | `/root/astra_director` | `gpt-6-astra` |
| Code implementation and repairs | `/root/astra_director/sol_code` | `gpt-6.1-sol` |
| Independent source review | `/root/astra_director/sol_review` | `gpt-6.1-sol` |
| Exclusive editor/asset operations | `/root/astra_director/sol_editor` | `gpt-6.1-sol` |
| Technical verification | `/root/astra_director/sol_verification` | `gpt-6.1-sol` |
| Independent gameplay QA | `/root/astra_director/sol_qa` | `gpt-6.1-sol` |

Work was staged within the host's concurrency limit; all six sessions need not run
simultaneously. The director coordinates handoffs instead of silently performing
missing specialist stages. These identifiers and model fields are host-session
attribution, not cryptographic identity verification. Installing TOML roles alone
would not demonstrate this execution.

## What changed in the reused fixture

This run extends the local-only `examples/door-demo` fixture (excluded from Git). It does not claim a
new game built from scratch. The mode now selects exactly one level-placed
`AStudioDoorActor`, including a Blueprint subclass, and explicitly rejects multiple
placed doors. With none present it retains the native fallback. Scripted pawns
exercise positive local X entry and then actual negative local X entry/reentry.
Fixture geometry, pawn paths and camera follow the selected door transform.

The new report fields identify the actual map and selected instance:
`map_package`, `door_selection`, `door_class`, `door_actor_path`, `door_origin` and
`door_is_blueprint`. The editor specialist compiled/saved `/Game/StudioDoor/BP_StudioDoor` derived from
`/Script/StudioDoor.StudioDoorActor`, saved `/Game/StudioDoor/StudioDoorValidation`
and confirmed exactly one placed instance. PIE selected
`/Game/StudioDoor/BP_StudioDoor.BP_StudioDoor_C` with `door_selection: level_placed`,
`door_is_blueprint: true` and map package
`/Game/StudioDoor/UEDPIE_0_StudioDoorValidation`. A native fallback cannot establish
this placed Blueprint coverage.

## Independent finding and same-author repair

The independent reviewer returned **R1 / P2**, an actual geometry regression:
`AddBox` applied the requested mesh scale and then replaced root scale while
setting the actor transform. Floors, walls and other differently sized fixture
boxes would become default-sized cubes. The director sent R1 to the original
implementation session. That author changed the final actor transform to apply
`Scale * DoorTransform.GetScale3D()` and removed the overwritten scale assignment.

The reviewer independently approved the repaired snapshot with no remaining
source findings. Only `StudioDoorMode.cpp` changed between these two submissions.
No defect was intentionally introduced to manufacture a repair example.

| Source round | Digest | Independent outcome |
|---|---|---|
| Initial | `0e3fd7137183bdc2e758da0dd9c1a13f9cf7cb3adc228ee333f13941f45feffd` | R1 requested changes |
| Repaired | `fc2de0a948b9cf3731201cbee7c7d5d11ade005d6f6c0988c3bf8f8ae2a51189` | Approved; R1 closed |

## Current evidence status

| Stage | Current result | Evidence still required for completion |
|---|---|---|
| Implementation | Submitted; R1 repaired | Preserve reviewed source digest |
| Independent code review | Approved repaired snapshot | Any source change requires new review |
| Preparatory C++ build | Rebuild passed, per verification specialist | Does not replace final aggregate verification |
| Source checks | 35 tests passed; 15 skills/13 roles validated | Retain current command outputs |
| Editor engineering | Passed | Official project binding, BP compile/save, saved map, one placed door, PIE 12/12; PIE stopped and editor exited |
| Final technical verification | Passed | Repaired C++ rebuild, 35 tests, validator, Win64 package and fresh payload runtime 12/12; exit 0 and no log errors |
| Independent gameplay QA | Passed | Fresh run, 12 independently checked numeric scenarios, final screenshot personally viewed |
| Pipeline completion gate | Complete | Exit 0, ready=true, round 2; current source/evidence and custody released |

Raw evidence remains in the local `studio-session` directory. The
[sanitized editor report](evidence/studio-door/editor.json) includes official MCP
actions, all 12 PIE assertions, run ID and saved Blueprint/map SHA256 hashes. No
binary assets are copied into the repository. The [technical report](evidence/studio-door/technical.json) independently compares
these hashes with packaging-source assets; both match. It includes the full relative
package inventory, payload hash and raw manifest hash. Independent [QA](evidence/studio-door/qa.json) and the [gate](evidence/studio-door/gate.json) subsequently passed.
The [sanitized pipeline](evidence/studio-door/pipeline.json) preserves scopes, rounds,
actual actors/models, R1 repair, raw report hashes and custody events.

## Technical verification

The Sol verifier rebuilt the repaired editor target (exit 0, 101.22 seconds), ran
35 repository tests and validated 15 skills/13 roles. Win64 Development
BuildCookRun completed with exit 0 in 123.97 seconds. A recovered Zen staging
readiness retry was retained as an observation, not concealed as a clean first attempt.

Fresh packaged run `6416d533d5024c0080d436640019545b` directly launched the actual
payload executable and passed 12/12 assertions in 18.50 game seconds (72.81 wall
seconds), selected the authored map and placed BP, used D3D12, wrote a screenshot,
ended closed/empty and exited 0 with no detected Error/Fatal/Ensure log entries.
The payload SHA256 is
`910c33e9f75ce14d4ec10a28ceb5ecacf23e86ef7d16b257986084ecdb66f651`.
The raw full-manifest SHA256 is
`1180679ffd7ac3385759a806e8dc8fc8dd37f93cdf7e064c60f027be6b74e01b`.
The bootstrap is inventoried; direct payload startup does not prove bootstrap startup.
Independent QA subsequently passed in its own fresh run below.

The initial sandbox UBT-cache failure and pre-R1 successful build remain historical
attempts; only the repaired rebuild supports the current result.

## Independent gameplay QA and final gate

QA run `fc4315d66ff74af9b5bfdf7c6ad06ec3` launched the same actual payload afresh,
exited naturally with code 0 in 69.515 wall seconds and passed 12 independently
checked numeric scenarios. It selected the authored map and placed Blueprint in a
D3D12 packaged game world, finishing at angle 0 with no occupants. The QA specialist
personally opened the fresh final screenshot and found the closed door, walls,
markers and readable HUD consistent with final values. No player-facing defects
were reported within this scope.

The inspected screenshot is retained locally; its hash remains in the curated QA
report. Screenshots, video, game source and generated game artifacts are excluded
from this publication.

The original 48 package entries and payload hash all matched the technical manifest.
The whole directory inventory was **not identical**: three runtime-generated Saved
configuration files had been added. The initial strict inventory check stopped
before launch; QA retained and documented the additions before confirming original
package-content equality. SSL certificate-store and GPU TSR driver-fallback warnings
remained; no Error/Fatal/Ensure entries were detected in this offline scenario.

QA independently checked reversal samples: 49.6482 degrees while empty at 12.2519
seconds, 63.5549 degrees with one occupant at 12.4042 seconds, then 90 degrees at
13.6023 seconds. These relationships support the scripted reversal test; the final
static screenshot does not establish per-frame visual motion continuity.

The director recorded the distinct QA report and ran the current completion gate:
`exit_code: 0`, `ready: true`, `state: complete`, `round: 2`, no reasons. Its digest
is the repaired round-2 digest above; editor custody was released. This completes
the declared fixture workflow with the scope limits below.

## Editor result and recoverable attempts

PIE run `36f4decc51904200a16df1c76155977a` passed **12/12 named assertions** with
D3D12 in a game world, including opposite-side reopening and continuous reversal.
It ended with angle 0 and no occupants. The editor owner stopped PIE, closed the
task editor gracefully and released custody. This is an editor-stage result,
separate from independent final gameplay QA.

Three failed attempts were preserved: unwritable DDC nodes (retried with a memory
cache), a dirty startup Entry level preventing loading (the task-owned attempt was
stopped), and a duplicated map not yet saved (corrected with explicit saving and
file verification). They are not relabeled as passes. Only the disposable project's
two default-map keys changed; full configuration and security tokens are excluded
from curated evidence. This positive PIE used a door at the origin; translated or
scaled placement, duplicate-door rejection and native fallback are not validated
by this run.

## Boundaries

The locally retained door video is
historical evidence from the earlier demonstration. It does not show the current
placed Blueprint fixture, repaired source or this five-specialist execution.
This small scripted fixture does not verify player controls, networking,
persistence, production-scale levels or every defined TOML role.

See [the studio workflow](feature-loop.md) and [the upstream comparison](upstream-studio-comparison.md)
for the project structure and its comparison with the referenced studio approach.

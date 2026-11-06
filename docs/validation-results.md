# Validation results — 2026-11-06

Tested with Windows, Unreal Engine **5.8.4 / changelist 58902052** installed through
Epic's distribution, Python 3.12.14, and Codex **0.167.0-alpha.3.2**.
Live Unreal work used new disposable StudioLab and StudioBuild projects, not an existing game.

| Check | Result | Evidence |
|---|---|---|
| Skill structure | 15 valid | Bundled skill-creator quick_validate plus tools/validate.py |
| Native role configuration | 9 valid | tools/validate.py |
| Python toolkit tests | 16 passed | tests/test_studio.py; CI below |
| Official MCP initialization | Passed | [Live smoke JSON](evidence/live-smoke.json) |
| Exact project binding | Passed | Saved-directory random challenge matched |
| Wrong project rejection | Passed | [Negative test](evidence/wrong-project.json) |
| Blueprint create / compile / save | Passed | New unique Actor Blueprint; warnings_as_errors enabled |
| Asset read-back / disk file | Passed | exists returned true and expected .uasset existed |
| Actor spawn / discovery | Passed | Spawned Blueprint instance returned by scene query |
| PIE start / running / stop | Passed | Running state true after start and false after stop |
| Native Codex MCP | Passed | [3 native calls](evidence/codex-runtime.json) |
| Native Codex roles | Passed for 2 roles | cpp-engineer and qa-engineer start/stop IDs in evidence |
| Binary patch hook | Passed after fix | Real apply_patch denied; probe file absent |
| C++ engine compilation | Passed | Separate StudioBuild C++ fixture; editor DLL and game executable |
| Unreal Automation suite | Not run | Python tests are a different layer |
| Game-specific interactions / networking | Not run | Fixture is an empty Actor Blueprint |
| UAT packaging / packaged startup | Passed | Win64 Development, D3D12, 90 ticks, exit 0, no error logs |
| Other Unreal versions / operating systems | Not run for Unreal | Cross-platform CI covers Python tooling only |

## Native Codex execution

Follow-up: [C++ build and packaged runtime verification](build-package-validation.md)
records the separate source fixture, actual package execution, fixes and evidence.
The original Blueprint-only MCP fixture remains a separate test.

A separate copy of the repository was opened in a persisted Codex test session
with workspace-write sandboxing. The exact disposable project was an additional
authorized workspace root. The model was inherited. Reviewed fixture hooks were
trusted for that invocation only; global configuration was not changed.

The parent loaded $ue-doctor, verified project binding, used native Unreal MCP
list_toolsets, describe_toolset and call_tool to read the current level
(`/Temp/Untitled_1`). It delegated source-planner inspection and Python tests to
the cpp-engineer and qa-engineer roles and waited for both. Lifecycle hook IDs,
native MCP completion events and the denied binary patch were independently
checked from runtime output, rather than relying only on the assistant's report.

The role test proves these two native role invocations, not all nine roles'
domain expertise. Role/skill validation proves file structure, not game quality.
No desktop sidebar chats were created for these disposable CLI tests.

## Failures found and resolved

1. The initial patch guard only read string/patch-shaped input. Actual Codex sent
   the patch in tool_input.command, so the first probe created a text .uasset in
   the disposable fixture. That probe was removed. The guard was corrected,
   a regression test was added, and a fresh real invocation was denied.
2. The first native MCP test used a noninteractive never-approval harness.
   Required MCP approval could not be serviced. The rerun used normal on-request
   approval with the automatic reviewer; all three native MCP calls completed.
   No global tool auto-approval or sandbox bypass was added.
3. Epic documentation describes the server name unreal-mcp, but the actual
   installed 5.8.4 build returned blank serverInfo fields. The client handles this
   observed version while requiring independent project binding.

For normal use, approve requested MCP operations through your Codex host's normal
approval UI/reviewer. A never-approval noninteractive host can refuse native calls
even when the server is connected.

## Reproduce

Create a new fixture with tools/studio.py example. Launch its editor with the
official plugins and an isolated local port. Run doctor and tools/live_smoke.py as
shown in README.md. The smoke script exits nonzero on failure and writes its
assertion outcomes. It leaves named test assets for inspection without saving
the map. No engine/plugin source or generated asset binaries are committed here.

For native Codex validation, open a separate trusted clone, connect its MCP config
to the fixture port, and request: use $ue-doctor; delegate planner review and Python
tests to cpp-engineer/qa-engineer; use native MCP to get_current_level; make one
guard-probe apply_patch attempt in the fixture and verify denial. Only use this
guard probe in disposable projects, since a broken/untrusted hook can permit it.
Use a persisted session; the tested host's ephemeral session could not fork a
native subagent rollout in an earlier host investigation.

## Continuous integration

[Validate workflow](https://github.com/Junghyeon0710/unreal-codex-studio/actions/workflows/validate.yml)
runs Python 3.11 configuration checks and the toolkit tests on Ubuntu, Windows and
macOS. It does not install or execute Unreal Engine. See the linked run for the
exact commit and platform results.

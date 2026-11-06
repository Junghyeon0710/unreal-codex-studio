# C++ build and packaged-runtime fixture

Original source-only UE 5.8 fixture for validating the studio build/package tools.
Copy this directory to a disposable location before building. Engine assets and
Epic plugin code/binaries are not included.

The game mode spawns a cube actor, camera and directional light. The actor exposes
a reflected damage function and a reflected health property. With StudioEvidence
and StudioRunId command-line arguments, it applies 25 damage, advances 300 cm over
60 ticks, captures a screenshot and writes a result after 90 ticks, then exits.

The runtime assertion requires a game world, registered/loaded mesh, health 75,
movement 300, a non-null rendering backend, a screenshot and a fresh run ID.
run-packaged.ps1 also checks the process exit code and rejects error/ensure logs.

## Run from the studio root

Use a copy outside the repository, for example ../StudioBuild:

```powershell
python tools/studio.py build --engine "D:/Epic Games/UE_5.8" --project "../StudioBuild/StudioBuild.uproject" --target StudioBuildEditor --run
python tools/studio.py package --engine "D:/Epic Games/UE_5.8" --project "../StudioBuild/StudioBuild.uproject" --archive "../PackagedStudioBuild" --run
& "../StudioBuild/run-packaged.ps1" -Executable "../PackagedStudioBuild/Windows/StudioBuild.exe" -EvidenceDirectory "../PackagedEvidence"
```

The packaged smoke uses a hidden window with a real graphics backend; it is not
a NullRHI test. Inspect the captured screenshot as well as the JSON and log.

## Official MCP and packaging

ModelContextProtocol and AllToolsets are enabled only for Editor targets.
AllToolsets brings in the GameFeatures editor dependency. The fixture therefore
defines a GameFeatureData primary-asset rule with bIsEditorOnly=True. This avoids
both a cooker error for a missing rule and a packaged startup ensure for a class
that is absent from the game target.

This rule is specific to a fixture with no runtime Game Features. Do not change a
real game's existing GameFeatureData rule to editor-only if its gameplay uses it.

Verified on Windows / UE 5.8.4 / Development. Shipping, input handling, multiplayer
and Unreal Automation are outside this fixture's tested scope.

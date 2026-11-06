English · [한국어](ko/build-package-validation.md)

# C++ build, packaging, and packaged runtime validation

Validated on 2026-11-06 using Windows, Unreal Engine 5.8.4 (CL 58902052), and
Win64 Development with a separate C++ fixture named StudioBuild.

| Check | Final result | Observed evidence |
|---|---|---|
| C++ editor target | Passed | 10 build actions, module DLL linked, exit code 0, approximately 99 seconds |
| C++ game target | Passed | UAT built StudioBuild.exe |
| Cook, package, and archive | Passed | exe/pak/utoc/ucas generated, exit code 0, final run approximately 68 seconds |
| Top-level packaged launcher | Passed | Game launched from Windows/StudioBuild.exe |
| Rendering | Passed | D3D12 initialized; screenshot saved and visually inspected |
| C++ runtime assertions | Passed | 90 frames, health 75, X movement 300 cm, mesh loaded and registered |
| Exit and log checks | Passed | Normal exit code 0; zero Error/Ensure log entries |

The final runtime test took approximately 7.57 seconds. The archive contains
56 files totaling approximately 1.02 GB. The game target receipt also confirms
that ModelContextProtocol and AllToolsets are excluded.

## Failures found and fixed

1. The first cook failed with exit code 25. GameFeatures, an editor dependency of
   AllToolsets, required a GameFeatureData Asset Manager rule that the empty
   fixture did not define.
2. Adding a normal runtime rule allowed packaging to complete, but the packaged
   game raised a handled ensure because the class was absent from the game
   target. Successful runtime assertions and exit code 0 did not count as
   passing the log audit.
3. This fixture does not use runtime Game Features, so its rule was restricted
   with bIsEditorOnly=True. After packaging again and launching through the
   top-level executable, the final log contained zero error entries.
4. The fixture's Enhanced Input default classes were configured to resolve an
   initialization warning. This does not establish that input behavior was tested.

One warning remains: the NVIDIA driver version causes TSR 16-bit VALU to be
disabled. No driver changes were made, and this is not a performance benchmark.

## Evidence and reproduction

- [Machine-readable results and earlier failures](evidence/build-package-runtime.json)
- [Reproducible C++ source and instructions](../examples/cpp-smoke/README.md)
- [Packaged screenshot](evidence/packaged-smoke.png)

![Test actor rendered by the packaged game](evidence/packaged-smoke.png)

Validation is limited to the C++ fixture. It does not cover the Araland game,
Shipping builds, multiplayer, user input, or the full Unreal Automation suite.

Packaging used the studio's package command following
[Epic's BuildCookRun workflow](https://dev.epicgames.com/documentation/en-us/unreal-engine/build-operations-cooking-packaging-deploying-and-running-projects-in-unreal-engine).
Engine source and generated game binaries are not distributed under this
repository's MIT license.

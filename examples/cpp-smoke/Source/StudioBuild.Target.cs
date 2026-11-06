using UnrealBuildTool;
public class StudioBuildTarget : TargetRules
{
    public StudioBuildTarget(TargetInfo Target) : base(Target)
    {
        Type = TargetType.Game;
        DefaultBuildSettings = BuildSettingsVersion.Latest;
        IncludeOrderVersion = EngineIncludeOrderVersion.Latest;
        ExtraModuleNames.Add("StudioBuild");
    }
}

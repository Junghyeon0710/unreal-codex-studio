using UnrealBuildTool;
public class StudioBuildEditorTarget : TargetRules
{
    public StudioBuildEditorTarget(TargetInfo Target) : base(Target)
    {
        Type = TargetType.Editor;
        DefaultBuildSettings = BuildSettingsVersion.Latest;
        IncludeOrderVersion = EngineIncludeOrderVersion.Latest;
        ExtraModuleNames.Add("StudioBuild");
    }
}

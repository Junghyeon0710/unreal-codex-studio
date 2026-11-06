#include "StudioBuildMode.h"
#include "StudioProbeActor.h"
#include "Camera/CameraActor.h"
#include "Engine/DirectionalLight.h"
#include "Engine/World.h"
#include "GameFramework/PlayerController.h"

AStudioBuildMode::AStudioBuildMode()
{
    DefaultPawnClass = nullptr;
}
void AStudioBuildMode::StartPlay()
{
    Super::StartPlay();
    GetWorld()->SpawnActor<AStudioProbeActor>();
    GetWorld()->SpawnActor<ADirectionalLight>(FVector(0, 0, 300), FRotator(-45, -45, 0));
    ACameraActor* Camera = GetWorld()->SpawnActor<ACameraActor>(
        FVector(650, -650, 400), FRotator(-22, 135, 0));
    if (APlayerController* PC = GetWorld()->GetFirstPlayerController())
    {
        PC->SetViewTarget(Camera);
    }
}

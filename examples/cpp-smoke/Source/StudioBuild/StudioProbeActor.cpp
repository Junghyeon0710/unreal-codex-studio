#include "StudioProbeActor.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "Engine/GameViewportClient.h"
#include "DynamicRHI.h"
#include "HAL/FileManager.h"
#include "HAL/PlatformMisc.h"
#include "Misc/CommandLine.h"
#include "Misc/FileHelper.h"
#include "Misc/Parse.h"
#include "Misc/Paths.h"
#include "Serialization/JsonSerializer.h"
#include "UObject/ConstructorHelpers.h"

AStudioProbeActor::AStudioProbeActor()
{
    PrimaryActorTick.bCanEverTick = true;
    Mesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("ProbeMesh"));
    SetRootComponent(Mesh);
    Mesh->SetMobility(EComponentMobility::Movable);
    static ConstructorHelpers::FObjectFinder<UStaticMesh> Cube(TEXT("/Engine/BasicShapes/Cube.Cube"));
    if (Cube.Succeeded()) { Mesh->SetStaticMesh(Cube.Object); }
}
void AStudioProbeActor::ApplyProbeDamage(float Amount)
{
    Health = FMath::Clamp(Health - FMath::Max(0.0f, Amount), 0.0f, 100.0f);
}
void AStudioProbeActor::BeginPlay()
{
    Super::BeginPlay();
    StartLocation = GetActorLocation();
    ApplyProbeDamage(25.0f);
    bSmoke = FParse::Value(FCommandLine::Get(), TEXT("StudioEvidence="), EvidencePath);
    FParse::Value(FCommandLine::Get(), TEXT("StudioRunId="), RunId);
    if (bSmoke)
    {
        IFileManager::Get().MakeDirectory(*FPaths::GetPath(EvidencePath), true);
        UE_LOG(LogTemp, Display, TEXT("STUDIO_SMOKE_BEGIN run=%s map=%s"), *RunId, *GetWorld()->GetMapName());
    }
}
void AStudioProbeActor::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    if (!bSmoke) { return; }
    ++Frames;
    if (Frames <= 60) { AddActorWorldOffset(FVector(5.0, 0.0, 0.0)); }
    const FString Screenshot = FPaths::ChangeExtension(EvidencePath, TEXT("png"));
    if (Frames == 60)
    {
        FScreenshotRequest::RequestScreenshot(Screenshot, false, false);
    }
    if (Frames != 90) { return; }
    const double Distance = GetActorLocation().X - StartLocation.X;
    const FString RHIName = GDynamicRHI ? FString(GDynamicRHI->GetName()) : TEXT("none");
    const bool bScreenshot = IFileManager::Get().FileExists(*Screenshot);
    const bool bPassed = !GIsEditor && !IsRunningCommandlet() && GetWorld()->IsGameWorld()
        && Mesh->IsRegistered() && Mesh->GetStaticMesh() && FMath::IsNearlyEqual(Health, 75.0f)
        && FMath::IsNearlyEqual(Distance, 300.0) && RHIName != TEXT("Null")
        && RHIName != TEXT("none") && bScreenshot && !RunId.IsEmpty();
    TSharedRef<FJsonObject> Result = MakeShared<FJsonObject>();
    Result->SetStringField(TEXT("status"), bPassed ? TEXT("passed") : TEXT("failed"));
    Result->SetStringField(TEXT("run_id"), RunId);
    Result->SetStringField(TEXT("map"), GetWorld()->GetMapName());
    Result->SetStringField(TEXT("rhi"), RHIName);
    Result->SetBoolField(TEXT("is_editor"), GIsEditor);
    Result->SetBoolField(TEXT("is_commandlet"), IsRunningCommandlet());
    Result->SetBoolField(TEXT("game_world"), GetWorld()->IsGameWorld());
    Result->SetBoolField(TEXT("mesh_registered"), Mesh->IsRegistered());
    Result->SetBoolField(TEXT("mesh_loaded"), Mesh->GetStaticMesh() != nullptr);
    Result->SetBoolField(TEXT("screenshot_written"), bScreenshot);
    Result->SetNumberField(TEXT("frames"), Frames);
    Result->SetNumberField(TEXT("health"), Health);
    Result->SetNumberField(TEXT("movement_x"), Distance);
    FString Json;
    FJsonSerializer::Serialize(Result, TJsonWriterFactory<>::Create(&Json));
    const bool bWritten = FFileHelper::SaveStringToFile(Json, *EvidencePath);
    UE_LOG(LogTemp, Display, TEXT("STUDIO_SMOKE_END run=%s passed=%d report=%d frames=%d health=%.1f x=%.1f rhi=%s"),
        *RunId, bPassed, bWritten, Frames, Health, Distance, *RHIName);
    FPlatformMisc::RequestExitWithStatus(false, bPassed && bWritten ? 0 : 3);
}

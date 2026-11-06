#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "StudioProbeActor.generated.h"

class UStaticMeshComponent;

UCLASS()
class STUDIOBUILD_API AStudioProbeActor : public AActor
{
    GENERATED_BODY()
public:
    AStudioProbeActor();
    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;
    UFUNCTION(BlueprintCallable, Category="Studio")
    void ApplyProbeDamage(float Amount);
private:
    UPROPERTY(VisibleAnywhere)
    TObjectPtr<UStaticMeshComponent> Mesh;
    UPROPERTY(VisibleAnywhere)
    float Health = 100.0f;
    int32 Frames = 0;
    bool bSmoke = false;
    FString EvidencePath;
    FString RunId;
    FVector StartLocation;
};

#pragma once
#include "CoreMinimal.h"
#include "GameFramework/GameModeBase.h"
#include "StudioBuildMode.generated.h"

UCLASS()
class STUDIOBUILD_API AStudioBuildMode : public AGameModeBase
{
    GENERATED_BODY()
public:
    AStudioBuildMode();
    virtual void StartPlay() override;
};

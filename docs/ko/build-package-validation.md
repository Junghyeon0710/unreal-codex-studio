[English](../build-package-validation.md) · 한국어

# C++ 빌드 · 패키징 · 패키지 실행 검증

2026-11-06, Windows / Unreal Engine 5.8.4 (CL 58902052) /
Win64 Development 환경에서 별도 C++ 테스트 프로젝트 StudioBuild를 검증했습니다.

| 항목 | 최종 결과 | 실제 확인 |
|---|---|---|
| C++ 에디터 타깃 | 통과 | 10개 빌드 작업, 모듈 DLL 링크, 종료 코드 0, 약 99초 |
| C++ 게임 타깃 | 통과 | UAT가 StudioBuild.exe 빌드 |
| 쿠킹·패키징·아카이브 | 통과 | exe/pak/utoc/ucas 생성, 종료 코드 0, 최종 약 68초 |
| 최상위 패키지 런처 | 통과 | Windows/StudioBuild.exe에서 게임 시작 |
| 실제 렌더링 | 통과 | D3D12, 스크린샷 저장 및 이미지 확인 |
| C++ 런타임 검사 | 통과 | 90프레임, 체력 75, X축 이동 300cm, 메시 로드·등록 |
| 종료·로그 검사 | 통과 | 정상 종료 코드 0, Error/Ensure 로그 0건 |

최종 실행은 약 7.57초 걸렸습니다. 배포 폴더에는 56개 파일, 약 1.02GB가 생성됐습니다.
게임 타깃 receipt에서 ModelContextProtocol과 AllToolsets가 제외된 것도 확인했습니다.

## 실패를 발견하고 수정한 내용

1. 첫 쿠킹은 종료 코드 25로 실패했습니다. AllToolsets의 에디터 의존성인
   GameFeatures에 필요한 GameFeatureData Asset Manager 규칙이 없었습니다.
2. 규칙을 일반 런타임 규칙으로 추가하자 패키징은 성공했지만, 패키지에서
   해당 클래스가 없다는 handled ensure가 발생했습니다. 실행 코드가 성공하고
   종료 코드가 0이어도 이 로그 검사를 통과한 것으로 취급하지 않았습니다.
3. 이 테스트 프로젝트는 런타임 Game Features를 사용하지 않으므로 규칙을
   bIsEditorOnly=True로 제한했습니다. 다시 패키징하고 최상위 런처로 실행한
   최종 결과에서 오류 로그 0건을 확인했습니다.
4. 샘플의 Enhanced Input 기본 클래스 설정을 추가해 초기화 경고를 해결했습니다.
   입력 기능 자체를 테스트했다는 의미는 아닙니다.

최종 로그에는 NVIDIA 드라이버 버전 때문에 TSR 16-bit VALU가 비활성화된다는
경고 1건이 남았습니다. 드라이버는 변경하지 않았으며, 성능 검증 결과는 아닙니다.

## 증거와 재현

- [기계 판독 결과와 이전 실패 기록](../evidence/build-package-runtime.json)
- [재현용 C++ 소스와 실행 방법](../../examples/cpp-smoke/README.md)
- [패키지 스크린샷](../evidence/packaged-smoke.png)

![패키지에서 실제 렌더링된 테스트 액터](../evidence/packaged-smoke.png)

검증은 테스트용 C++ 프로젝트 범위입니다. Araland 게임, Shipping 빌드,
멀티플레이, 사용자 입력, Unreal Automation 전체 테스트는 포함하지 않습니다.

패키징은 [Epic의 BuildCookRun 절차](https://dev.epicgames.com/documentation/en-us/unreal-engine/build-operations-cooking-packaging-deploying-and-running-projects-in-unreal-engine)에 따라
스튜디오의 package 명령으로 수행했습니다. 엔진 소스나 생성된 게임 바이너리를
이 저장소의 MIT 라이선스로 배포하지 않습니다.

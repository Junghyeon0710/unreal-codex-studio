[English](../../README.md) · 한국어

# Unreal Codex Studio

[![Validate](https://github.com/Junghyeon0710/unreal-codex-studio/actions/workflows/validate.yml/badge.svg)](https://github.com/Junghyeon0710/unreal-codex-studio/actions/workflows/validate.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](../../LICENSE)

**Epic 공식 Unreal MCP를 사용하는 Codex용 Unreal 개발 워크스페이스.**

15개 스킬, 13개 역할 정의, 작업별 적정 인원을 선택하는 Astra 협업 절차, 프로젝트 연결 검사, MCP 클라이언트, 빌드·테스트·패키징 명령 도구를 제공합니다.
게임마다 반복하는 작업 규칙을 재사용하고, 실제 엔진 검증 결과를 남기는 것이 목적입니다.
독립적인 커뮤니티 프로젝트이며 Epic Games나 OpenAI의 공식 제품은 아닙니다.

[로컬 문 테스트 결과](../ko/studio-door-validation.md)를 공개합니다.
문 테스트 프로젝트·생성 에셋·실행 패키지·영상과 스크린샷은 로컬에만 보관합니다.

> 공식 MCP는 Unreal의 Experimental 기능입니다. **Windows / Unreal 5.8.4에서 MCP·C++ 빌드·패키지 실행 테스트**를 수행했습니다.
> 검증 범위와 Codex 실행 결과는 [검증 기록](../../docs/validation-results.md)을 확인하세요.
> Python CI는 Unreal Engine이나 게임을 실행하지 않습니다.

## 무엇이 들어 있나요?

- **역할 분담:** 기술 총괄, C++, Blueprint, 게임플레이, UI, 네트워크, 빌드, QA, 성능.
- **공식 에디터 연결:** ModelContextProtocol + AllToolsets. 별도 서드파티 Unreal 브리지 없이 연결합니다.
- **오작업 방지:** 연결된 에디터가 지정한 프로젝트인지 확인하고, 에디터 변경은 담당자 한 명이 순차 수행합니다.
- **재현 가능한 도구:** 프로젝트 스캔, doctor, 도구 스키마 탐색, 명령 계획/실행, 격리 프로젝트 실동작 테스트.
- **검증 구분:** 소스 검사, C++ 빌드, Blueprint 컴파일, PIE, 게임플레이, 패키지 실행을 각각 보고합니다.

```mermaid
flowchart LR
  U[사용자 요청] --> C[Codex / 기술 총괄]
  C --> S[C++ · 게임플레이 · 리뷰]
  C --> E[단일 에디터 담당]
  E --> M[Epic 공식 Unreal MCP]
  M --> UE[Unreal Editor]
  S --> V[QA / 검증 기록]
  UE --> V
```

역할 파일 설치만으로 에이전트가 실행되지는 않습니다. Astra 총괄이 실제 요청의
범위·의존성·위험·의미 있는 검증을 보고 필요한 최소 역할과 인원을 스스로 정합니다.
일상적인 인원 배치를 사용자에게 되묻지 않으며 발견한 문제에 따라 추가·재배치합니다.

## 작업에 맞춘 팀 구성

짧은 설명은 총괄 혼자 또는 조사 담당 한 명으로 충분할 수 있습니다. 머티리얼 변경은
에디터 전문가 한 명, 코드 결함은 필요할 때 작성자와 독립 검토자, 큰 기능은 더 많은
전문가를 선택할 수 있습니다. 예시이지 고정 인원표가 아닙니다. 독립 검토는 유용하거나
요청·주장하는 경우 선택하며 작성자가 자기 작업의 독립 검토자가 될 수 없습니다.
에디터·빌드·패키징·게임플레이 QA도 해당 작업에 의미가 있을 때만 포함합니다.

```mermaid
flowchart LR
  R[실제 요청] --> M[Astra 총괄]
  M --> P[필요한 역할·범위·검증 선택]
  P --> W[필요한 Sol 담당만 실제 실행]
  W --> F[발견 사항·관찰 증거]
  F --> M
  M --> C[선택 범위 완료 또는 한계 보고]
```

루트·기술 총괄의 기본 모델은 `gpt-6-astra`, 선택한 전문 역할은 `gpt-6.1-sol`입니다.
새 세션 기본값이며 기존 대화의 모델·샌드박스·승인 정책을 바꾸지 않습니다. 위임은
실제 호스트 호출로 수행합니다. 파일·저널은 담당자를 실행하거나 신원을 인증하지 않습니다.
에디터 작업이 있으면 지정한 한 명만 공식 MCP의 조회·변경, 바이너리 에셋과 PIE를
독점 제어합니다.

여러 단계의 추적이 도움이 될 때 `tools/studio_pipeline.py`를 선택적으로 사용해
실제 인원·스코프 해시·선택 단계와 필수 검사·이유 있는 계획 변경을 기록합니다.
선택한 검증 누락, 오래된 소스·증거, 에디터 소유권 충돌은 완료로 처리하지 않습니다.
설명·읽기 전용 답변에는 저널이나 구현 파이프라인이 필요하지 않습니다.
기존 5인 실행 기록과 명시적인 `--profile strict-five` 통합 테스트는 호환되지만
모든 작업의 기본 인원 규칙은 아닙니다. `review_loop.py`도 선택적 2인 검토 도구로 유지합니다.
[가변 팀 구성 절차](../feature-loop.md)를 참고하세요.

[완료된 5인 문 실험](../ko/studio-door-validation.md)은 해당 고정 스냅샷의 과거 증거입니다.
당시 테스트 35개·게이트 결과로 이후 가변 정책·도구 변경을 검증했다고 하지 않습니다.

## 빠른 시작

필요 환경: Python 3.11+, Codex, 공식 MCP가 포함된 Unreal Engine.
실제 검증 엔진은 **UE 5.8.4**입니다. 5.7 백포트나 다른 버전은 이 저장소의 검증 대상이 아닙니다.

```sh
git clone https://github.com/Junghyeon0710/unreal-codex-studio.git
cd unreal-codex-studio
python tools/studio.py --help
```

1. 이 폴더를 Codex에서 열고 내용을 검토한 뒤 프로젝트를 신뢰합니다.
2. Unreal 프로젝트에서 **Unreal MCP**와 **All Toolsets**를 활성화하고 에디터를 재시작합니다.
3. 에디터 콘솔에서 `ModelContextProtocol.StartServer 8000`을 실행합니다.
4. 정확한 프로젝트와 엔진 경로로 확인하고 Codex 연결을 활성화합니다.

```powershell
python tools/studio.py doctor --engine "D:/Epic Games/UE_5.8" --project "D:/Games/MyGame/MyGame.uproject" --url http://127.0.0.1:8000/mcp
python tools/studio.py connect --url http://127.0.0.1:8000/mcp
```

Codex를 다시 열고 다음처럼 요청합니다.

```text
프로젝트는 D:/Games/MyGame/MyGame.uproject,
엔진은 D:/Epic Games/UE_5.8 이야.
공식 MCP 연결을 확인하고 현재 모듈 구조를 설명해줘.
```

스킬 이름은 생략해도 됩니다. "플레이어가 가까이 오면 열리는 문을 만들어줘",
"이 빌드 오류 원인을 찾아줘"처럼 요청하면, Codex가 요청 내용과 스킬 설명을
바탕으로 적절한 작업 절차를 선택합니다. 특정 절차를 직접 지정하고 싶을 때만
`$ue-feature` 같은 이름을 사용하면 됩니다.
[OpenAI의 스킬 호출 안내](https://learn.chatgpt.com/docs/build-skills)를 참고하세요.

이 저장소를 Codex 작업 폴더로 열어 프로젝트 스킬이 보이도록 해야 합니다.
자동 선택은 요청 범위와 호스트 기능을 따르며, 모든 에이전트를 실행하거나
프로젝트 수정 권한을 추가로 부여하는 기능은 아닙니다.

경로는 `studio.local.example.json`을 `studio.local.json`으로 복사해서 관리할 수도 있습니다.
이 파일은 Git에서 제외됩니다. CLI는 실수를 줄이기 위해 경로 인자를 명시적으로 받습니다.
기존 게임에 이 저장소를 덮어쓸 필요 없이 별도 Codex 작업 폴더로 사용할 수 있습니다.

## 스킬

| 스킬 | 용도 |
|---|---|
| `$ue-start` | 프로젝트 시작·작업 분류 |
| `$ue-doctor` | 엔진·공식 플러그인·연결 대상 검사 |
| `$ue-project-scan` | 모듈·플러그인·타깃 조사 |
| `$ue-feature` | 기능 구현과 역할 배분 |
| `$ue-cpp` | C++·UHT·수명 관리 |
| `$ue-blueprint` | MCP 기반 Blueprint 편집·컴파일 |
| `$ue-ui` | UMG·CommonUI 작업 |
| `$ue-data` | DataTable·DataAsset·원본 데이터 |
| `$ue-review` | 변경 사항 검토 |
| `$ue-build` | UBT 빌드 |
| `$ue-test` | Unreal Automation 검증 |
| `$ue-pie-check` | PIE 실행·관찰·종료 |
| `$ue-package` | UAT 쿠킹·패키징 |
| `$ue-package-smoke` | 패키지 시작·동작 확인 |
| `$ue-diagnose` | 로그·실패 원인 분석 |

GAS, Niagara, PCG, World Partition 등은 프로젝트에서 필요할 때 실제 설치된 도구셋을 탐색합니다.
도구 개수나 기능 지원을 고정해서 가정하지 않습니다.

## 직접 테스트하기

아래 테스트는 **빈 테스트 프로젝트에 새 에셋을 생성합니다.**
기존 게임에는 실행하지 말고 별도 fixture를 사용하세요.

```powershell
python tools/studio.py example --destination "../StudioLab"
python tools/studio.py launch --engine "D:/Epic Games/UE_5.8" --project "../StudioLab/StudioLab.uproject" --port 8017
```

`launch`는 기본적으로 실행 명령을 출력합니다. 출력된 명령으로 에디터를 실행하거나 `--run`을 추가합니다.
에디터가 준비되면:

```powershell
python tools/live_smoke.py --project "../StudioLab/StudioLab.uproject" --url http://127.0.0.1:8017/mcp --output ".studio/live-smoke.json" --allow-fixture-write
```

검증: 프로젝트 연결 → Blueprint 생성·컴파일 → 지정 에셋 저장·디스크 확인 → 액터 배치·조회 → PIE 실행·종료.
에셋은 검사할 수 있도록 fixture에 남깁니다. 레벨은 저장하지 않습니다.

C++ 빌드와 Windows 패키지 실행은 별도의 [C++ 테스트 샘플](../../examples/cpp-smoke/README.md)로 재현할 수 있습니다.
[실제 빌드·패키징·실행 결과](../ko/build-package-validation.md)에는 실패 원인과 수정 내역도 기록했습니다.

## 구조

```text
AGENTS.md                  공통 작업 원칙
.agents/skills/            15개 Unreal 스킬
.codex/agents/             13개 Codex 역할
.codex/hooks/              바이너리 패치 방지·역할 실행 기록
.codex/config.toml         역할 및 MCP 설정 (연결은 기본 비활성)
tools/                    Python 표준 라이브러리 기반 실행 도구
tests/                    독립 실행 가능한 도구 테스트
templates/                기능·검증 기록 양식
docs/                     설치, MCP, 호환성, 검증 기록
docs/readme/README_ko.md   한국어 README
```

자세한 내용: [설치](../../docs/getting-started.md) · [공식 MCP](../../docs/official-mcp.md) ·
[검증 기준](../../docs/verification.md) · [기여](../../CONTRIBUTING.md) · [원본과 라이선스](../../UPSTREAM.md)

## License

MIT. [Claude Code Game Studios](https://github.com/donchitos/claude-code-game-studios)의
스튜디오 구조를 바탕으로 Unreal과 Codex에 맞게 새로 구성했습니다.
원본 저작권 고지를 보존합니다. Unreal Engine 및 Epic 플러그인 소스·바이너리는 배포하지 않습니다.

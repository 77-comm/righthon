---
applyTo: "**"
---

# Aspire — 쓰지 마라

**결론: 안 쓴다.** 서비스 하나·DB/큐 없음. Aspire 가치는 다중 오케스트레이션이고, 공식 배포 경로는 기존 B1 zip URL을 버린다.

현장 한 줄: "키노트 권고는 여러 서비스를 묶을 때다. 우리는 프로세스 하나다. 필수·심사표에 Aspire가 없고, Azure 항목은 형식적 추가를 감점한다."

## 확인됨 (2026-08-22)

- 명칭: ".NET Aspire" → **Aspire**. 현행 **13.5.0**(2026-08-18). 지원은 이 버전만.
- Python: 1등 시민. `AddPythonApp` / `AddUvicornApp`(FastAPI). AppHost는 **C# 또는 TypeScript**(TS는 13.4 GA). C# AppHost만 .NET 10 SDK. TS는 Node 20.19+/22.13+/24+(C# 프로젝트 불필요).
- CLI: `brew install --cask microsoft/aspire/aspire` 또는 `curl -sSL https://aspire.dev/install.sh | bash` → `aspire --version`.
- `azd`/`aspire deploy`는 AppHost 환경 리소스를 따른다. `AddAzureAppServiceEnvironment`면 App Service로도 간다. **기본은 신규 RG·Plan(문서: Linux P0V3)·ACR·컨테이너·새 웹앱**. 기존 `righthon-hale` B1 zip을 재사용하지 않는다. App Service 경로는 **Preview**.
- 로컬만: `aspire init` → `aspire run`은 배포와 분리 가능(공식 점진 도입).

## 불확실

- `AddUvicornApp`이 App Service 자동 타겟인지: 공식은 **project + Dockerfile**만 명시.
- 기존 B1을 `AsExisting`으로 붙이기: 13.5에 계열 API는 있으나 이 레포로 미검증.

## 심사

필수 = 웹앱 + Microsoft Agent Framework + GitHub Copilot SDK + Azure 배포. Aspire **없음**.
Azure 18%: "필요 이상의 서비스를 형식적으로 추가한 경우에는 감점." 혁신 5%는 생산성 AI이지 인프라 가점이 아님. → **가점 근거 없음. 시간낭비.**

## 비상 (필수로 바뀌면)

배포는 `./deploy.sh` 유지. `aspire deploy`/`azd up` 금지(URL·SKU 파괴).
`brew install --cask microsoft/aspire/aspire` → `aspire init --language typescript --non-interactive` → `aspire add python` → AppHost에 `AddUvicornApp("api",".","main:app").WithExternalHttpEndpoints()` → `aspire run`(로컬 대시보드만).
깨지는 지점: CLI/SDK 설치, `aspire init`이 루트 `package.json` 변경, zip 화이트리스트 밖 파일, Preview가 새 P0V3 생성.

출처: https://aspire.dev/whats-new/aspire-13-5/ · https://aspire.dev/support/ · https://aspire.dev/integrations/frameworks/python/ · https://aspire.dev/get-started/install-cli/ · https://aspire.dev/get-started/prerequisites/ · https://aspire.dev/get-started/add-aspire-existing-app/ · https://aspire.dev/deployment/azure/app-service/ · https://learn.microsoft.com/azure/app-service/quickstart-dotnet-aspire · https://github.com/matdaaiga-kr/matdathon-2026/blob/main/README.md · https://github.com/matdaaiga-kr/matdathon-2026/blob/main/judgement/judgement-criteria.md

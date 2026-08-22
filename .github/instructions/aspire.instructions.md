---
applyTo: "**"
---

# Aspire — 쓰지 마라

**결론: 안 쓴다.** AppHost·`aspire deploy`는 금지. 관찰 가능성은 App Insights(+ MAF OTel)로 채운다.

현장 한 줄: "키노트 권고 ≠ 심사표. 필수·배점을 쓴 사람이 Justin Yoo이고 Aspire는 없다. 25%의 오케스트레이션은 MAF 에이전트이지 Aspire가 아니다."

## 재조사 2026-08-22 11:05 — 왜 안 뒤집혔는가

- **Q3(확인됨, 뒤집힘 없음).** 공식 MAF↔Aspire는 `Aspire.Hosting.AgentFramework.DevUI`(.NET prerelease, 다중 에이전트 DevUI). Python은 `agent-framework-devui`(Aspire 없음). Copilot SDK↔Aspire **못 찾음**. MAF 관측 공식 경로 = OTel → 로컬 Aspire Dashboard **standalone** 또는 Azure App Insights. AppHost 불필요.
- **Q4(확인됨).** 필수 = 웹앱+MAF+Copilot SDK+Azure. 심사표·Discussions(#1,#2,#7–#12)·랜딩(ticketa)에 Aspire **없음**. 키노트 슬라이드 **못 찾음**. 필수·배점 커밋 작성자 = Justin Yoo(03:21–03:23 KST). 10:50 이후 공식 레포 커밋 0. 무대 구두 강조는 **불확실**.
- 기존 유지(확인됨): Aspire **13.5**. `azd`/`aspire deploy`는 신규 P0V3·ACR·컨테이너. 기존 B1 zip URL을 버린다.

## 관찰 가능성 — Azure 18% 수확 (Aspire와 무관)

채점: "반복 가능한 배포, 안정성 및 **관찰 가능성**" / "필요 이상의 서비스를 **형식적으로** 추가하면 감점."

| 수단 | 판정 |
|---|---|
| App Insights (App Service Python 자동계측 `ApplicationInsightsAgent_EXTENSION_VERSION=~3` 또는 MAF `configure_azure_monitor`) | **정당.** 칸 이름과 일치. 리소스 1~2개(App Insights±Log Analytics)이나 에이전트 스팬이 보이면 형식적이 아님. 비용: Log Analytics **계정당 5GB/월 무료**. 소요 ~5–15분. **앱 200 확인 뒤에** 붙여라. TRD에 적을 것. |
| Aspire Dashboard standalone (`docker run mcr.microsoft.com/dotnet/aspire-dashboard:latest`, UI :18888 / OTLP :4317) | **확인됨·로컬만.** MAF Python 문서 경로. AppHost 없음. Azure에 올리면 형식적 추가. |
| `opentelemetry-instrumentation-fastapi`만 | **확인됨.** 오케스트레이션 없이 동일 OTel. 채점용 백엔드는 App Insights. |
| Aspire AppHost / ACA 대시보드 / 큐·Redis | **금지.** 그게 "형식적 추가". |

빈 App Insights만 만들고 트레이스가 없으면 감점. `/healthz`만으로도 관찰 가능성은 주장 가능하나, MAF 스팬이 있으면 18%가 단단해진다.

## 로컬만 `aspire run`? — 가능, 가치 없음

- **가능(확인됨).** `aspire init`→`aspire run`은 배포와 분리. `./deploy.sh` 유지.
- 산출물: `aspire.config.json` + TS면 `aspire-apphost/` **및 루트 `package.json`에 `aspire:*` 스크립트**(모듈 설정은 안 건드림) / C#이면 `apphost.cs`(.NET 10 SDK). 현재 zip 화이트리스트엔 AppHost 미포함. 소요 10–20분(Docker 없음 30–60분+).
- 레포만 보면 심사 에이전트가 "Aspire 씀"을 **인식할 수는 있음**. 점수는 배포·MAF 깊이라 연극. 시간 대비 점수 없음.

## 비상 (필수로 바뀌면)

`aspire deploy` 금지. 최소 인정: 로컬 dashboard 컨테이너 + `OTEL_EXPORTER_OTLP_ENDPOINT`. AppHost 강제 시에만 `aspire init --language typescript --non-interactive`.

출처: https://github.com/matdaaiga-kr/matdathon-2026/blob/main/README.md · https://github.com/matdaaiga-kr/matdathon-2026/blob/main/judgement/judgement-criteria.md · https://learn.microsoft.com/agent-framework/agents/observability · https://learn.microsoft.com/agent-framework/integrations/by-component/ui/devui/ · https://aspire.dev/dashboard/standalone/ · https://aspire.dev/get-started/add-aspire-existing-app/ · https://learn.microsoft.com/azure/app-service/monitor-app-service · https://azure.microsoft.com/pricing/details/monitor/ · https://ticketa.co/event/jxxdbwmn

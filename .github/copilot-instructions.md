# righthon — Copilot 현장 지시

이 파일을 항상 따른다. 추측으로 새 스택을 열지 않는다.

## 허용 도구 (주최 규칙)

- **VS Code + GitHub Copilot Chat/Agent**, 보조로 **GitHub Copilot CLI**.
- 타사 AI 코딩 도구는 사용하지 않는다. 퇴장 사유다.

## 계정·레포

- IDE·Copilot 로그인: **`hale-righthon`** (Max는 여기만).
- 코드 집: **`77-comm/righthon`**. 새 레포·포크 만들지 마.
- Azure 구독: 이미 로그인된 **Azure for Students** (`hale_knu@office.knu.ac.kr`). 새 구독 생성 금지.
- 리소스: `rg-matdathon` / `aif-matdathon-hale` / deployment **`gpt-5-mini`**. 새 AI 계정 파지 마.

## 아키텍처 (변경 금지)

> **2026-08-21 개정 — Static Web Apps는 이 구독에서 생성 불가라 App Service로 확정.**
> `az staticwebapp create` → **`RequestDisallowedByAzure`**. 구독 정책 `Allowed resource deployment regions`
> 허용값(`centralindia·uaenorth·koreacentral·indonesiacentral·malaysiawest`)과 SWA 지원 리전
> (`Central US·East US 2·West US 2·West Europe·East Asia`)의 **교집합이 공집합**이다.
> **SWA·`api/` 폴더·`staticwebapp.config.json`을 되살리려 하지 마.** 시간만 버린다.

- 웹앱만. 네이티브·VM·AKS·Container Apps 금지.
- **Azure App Service** (Linux, `NODE:22-lts`, F1 Free). IaaS 금지. ⚠️Node 20은 런타임 목록에서 제공 종료.
- **`server.js` 단일 파일, 의존성 0개** (Node 22 내장 `fetch`). `npm install` 실패는 배포 실패 최다 원인이니
  **패키지를 추가하지 마.** 정적 서빙 + `POST /api/chat` + `/healthz` 가 전부다.
- 키는 App Service **애플리케이션 설정**만. `index.html`·프론트 JS·채팅 로그에 키·endpoint 금지.
- `gpt-5-mini`는 `max_tokens` 금지 → **`max_completion_tokens`** (수천). 낮으면 HTTP 200에 `content` 빈 문자열.

## Azure: CLI 먼저, MCP는 조회만

| | 써라 | 쓰지 마라 |
|---|---|---|
| 생성·배포·설정·키 | **`az` / `azd`** (이미 설치됨) | MCP에 “만들어 줘” |
| 구독에 뭐가 있나 | Azure MCP 또는 `az` | 서버 6개 동시 |
| 로컬 확인 | `node server.js` 후 `curl localhost:8080/healthz` | `swa`/`func` 설치하지 마. 이제 안 쓴다 |

**배포는 이미 만들어져 있다. 다시 만들지 마.**

```bash
./deploy.sh          # zip → az webapp deploy → 헬스체크. 약 40초
```

- 앱 `righthon-hale` / 플랜 `asp-matdathon`(F1 Free) / RG `rg-matdathon`, koreacentral
- 라이브: **`https://righthon-hale.azurewebsites.net`** (2026-08-21 종단 검증 완료)
- 앱 설정 6개 주입 완료(`AZURE_OPENAI_*` 4 + `SCM_DO_BUILD_DURING_DEPLOYMENT=false` + `WEBSITE_NODE_DEFAULT_VERSION=~22`).
  **다시 넣지 마.** 값을 stdout에 찍지도 마.
- GitHub Actions 쓰지 마 — CI 왕복 2~3분이라 30분 배포 리듬에 안 맞고 실패 지점만 는다.
- ⚠️ **`az webapp deploy`가 `RuntimeSuccessful`을 반환해도 동작 증명이 아니다.**
  배포 후 반드시 `/healthz` + 실제 `/api/chat` 200을 확인할 것.

## MCP — 적게 (컨텍스트 부패)

토큰·도구 목록이 매 턴 붙는다. **당일 켜둘 MCP는 최대 2.**

- 켜도 됨: **Azure MCP** (이미 확장), 필요 시 **GitHub MCP**
- 켜지 마: Microsoft Learn, Playwright, MarkItDown, Awesome Copilot, 그 외 탐색용
- 새 MCP를 주제에 맞춰 추가하지 마. 도구 검색이 답을 잡아먹는다.

`.vscode/mcp.json`이 비어 있으면 빈 채로 둬라. 확장 Azure MCP면 충분하다.

## 감독 — Copilot은 감독자가 아니다

VS Agent / Copilot CLI에는 77단식 별도 감독 에이전트가 없다. **감독은 hale.**

현장 확인:

1. 터미널·`az`는 **명령마다 승인**이 뜨는지.
2. **Always allow / YOLO / --allow-all / --yolo** 켜지 마. `az group delete`, 키 출력, 구독 변경이 그대로 나간다.
3. Auto-approve가 기본이면 위험한 명령(`delete`, `purge`, `account set`)만 수동으로 되돌릴 수 있는지 첫 30분에 테스트.
4. 같은 명령을 세 번 실패하면 도구를 바꾸거나 멈춰라. 루프가 쿼터를 먹는다.

MCP는 2개 초과 금지. `az group delete` 류는 실행 전 한 줄로 hale에게 확인.

## 당일 순서

주제는 **개인 생산성 향상 에이전트 앱**(참가 메일). 세부는 당일 공개. 껍데기는 그 주제로 두고, 당일 필수요소만 맞춰 살을 붙여.

1. 기능 **3개 이하**로 자른다.
2. 껍데기 이름만 바꿔 **먼저 배포**. 링크가 있어야 채점된다.
3. 30분마다 push → 배포 확인.
4. 기능 동결 시각을 지킨다. 마지막 push 여유.

새 프레임워크·새 Functions 언어·새 모델 공급자를 “더 좋아서” 들이지 마.

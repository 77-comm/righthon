# righthon

맞다톤 2026 참가작. **Azure App Service** (Linux · Node 22 · F1 Free) 최소 구성.

주제: 개인 생산성 향상 에이전트 앱 (세부 요구사항은 행사 당일 공개)

**라이브: <https://righthon-hale.azurewebsites.net>**

현장 Copilot 지시: [`.github/copilot-instructions.md`](.github/copilot-instructions.md) (Agent가 자동 첨부).

## 구조

```
index.html      프론트 (빌드 없음)
server.js       node:http 단일 프로세스 — 정적 서빙 + /api/chat + /healthz
package.json    start=node server.js, 의존성 0개
deploy.sh       zip → az webapp deploy → 헬스체크 (약 40초)
```

**의존성을 0개로 유지한다.** `npm install` 실패는 배포 실패의 가장 흔한 원인이고,
현장 네트워크에서 그걸 디버깅할 시간이 없다. Node 22 내장 `fetch`로 충분하다.

**API 키는 App Service 애플리케이션 설정에만 둔다.** 프론트 JS에 넣으면 개발자도구에 그대로 노출된다.

## 🔴 왜 Static Web Apps가 아닌가 (2026-08-21 실측)

`az staticwebapp create` → **`RequestDisallowedByAzure`**

| | |
|---|---|
| 구독 정책 `Allowed resource deployment regions` | `centralindia` `uaenorth` `koreacentral` `indonesiacentral` `malaysiawest` |
| SWA 지원 리전 (`Microsoft.Web/staticSites`) | `Central US` `East US 2` `West US 2` `West Europe` `East Asia` |
| 교집합 | **없음 → 어느 리전으로도 생성 불가** |

Azure for Students 구독의 리전 정책이 SWA 지원 리전을 전부 차단한다. 지원에 요청해도 풀어주지 않는다는
보고가 다수. 대회 규칙(`policies/policy-rules.md`)은 *"Azure 클라우드에 배포한 앱의 주소"* 만 요구하고
SWA를 특정하지 않으므로 App Service로 충족한다.

## 배포

```bash
./deploy.sh
```

Azure 리소스 (이미 생성됨 — 다시 만들지 말 것):

| | |
|---|---|
| 리소스 그룹 | `rg-matdathon` (koreacentral) |
| App Service 플랜 | `asp-matdathon` — F1 Free, Linux |
| 웹앱 | `righthon-hale` — `NODE:22-lts` |
| 모델 | `aif-matdathon-hale` / `gpt-5-mini` |

애플리케이션 설정 6개 주입 완료: `AZURE_OPENAI_ENDPOINT` · `AZURE_OPENAI_KEY` ·
`AZURE_OPENAI_DEPLOYMENT` · `AZURE_OPENAI_API_VERSION` · `SCM_DO_BUILD_DURING_DEPLOYMENT=false` ·
`WEBSITE_NODE_DEFAULT_VERSION=~22`.

## 로컬 실행

```bash
export AZURE_OPENAI_ENDPOINT="https://aif-matdathon-hale.cognitiveservices.azure.com/"
export AZURE_OPENAI_KEY=$(az cognitiveservices account keys list \
  -n aif-matdathon-hale -g rg-matdathon --query key1 -o tsv)
node server.js
curl localhost:8080/healthz
```

## 검증된 함정 (2026-08-21 실측)

- **`gpt-5` 계열은 `max_tokens`를 거부한다** → `max_completion_tokens`를 쓸 것.
- 그 한도는 **reasoning 토큰까지 함께 소모**한다. 낮게 잡으면 `content`가 빈 문자열인 채로 **HTTP 200**이
  돌아온다. 에러가 아니라 성공으로 보이므로 엉뚱한 곳을 파게 된다. 여유 있게(수천) 줄 것.
- **Node 20은 `az webapp list-runtimes`에서 이미 제공 종료**됐다(24 / 22만 남음).
- **`az webapp deploy`의 `RuntimeSuccessful`은 동작 증명이 아니다.** 배포 후 `/healthz`와 실제
  `/api/chat` 200까지 확인해야 채점 대상이 된다.

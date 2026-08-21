# righthon

맞다톤 2026 참가작. **Azure Static Web Apps + 관리형 Functions** 최소 구성.

주제: 개인 생산성 향상 에이전트 앱 (세부 요구사항은 행사 당일 공개)

현장 Copilot 지시: [`.github/copilot-instructions.md`](.github/copilot-instructions.md) (Agent가 자동 첨부).

## 구조

```
index.html                    프론트 (빌드 없음)
staticwebapp.config.json      SPA 폴백 + 보안 헤더
api/
  host.json                   Functions 확장 번들 v4
  package.json                @azure/functions v4 (Node 20+)
  src/functions/chat.js       POST /api/chat → Azure OpenAI
```

**API 키는 반드시 서버(Functions) 측에만 둔다.** 프론트 JS에 넣으면 개발자도구에 그대로 노출된다.

## SWA 앱 설정 (Configuration → Application settings)

| 이름 | 값 |
|---|---|
| `AZURE_OPENAI_ENDPOINT` | `https://aif-matdathon-hale.cognitiveservices.azure.com/` |
| `AZURE_OPENAI_KEY` | `az cognitiveservices account keys list -n aif-matdathon-hale -g rg-matdathon --query key1 -o tsv` |
| `AZURE_OPENAI_DEPLOYMENT` | `gpt-5-mini` |
| `AZURE_OPENAI_API_VERSION` | `2025-04-01-preview` |

## 검증된 사실 (2026-08-17 실측)

- 배포: `gpt-5-mini` (`gpt-5-mini-2025-08-07`), GlobalStandard, capacity 100, koreacentral
- `api-version=2025-04-01-preview` + `max_completion_tokens` 로 종단 호출 성공
- ⚠️ **gpt-5 계열은 `max_tokens`를 거부한다** — `max_completion_tokens`를 쓸 것
- ⚠️ 이 한도는 **reasoning 토큰까지 함께 소모**한다. 너무 낮게 잡으면 `content`가 빈 문자열로
  돌아오면서 HTTP 200이 뜬다. 여유 있게(수천) 줄 것

## 로컬 실행

```bash
npm i -g @azure/static-web-apps-cli azure-functions-core-tools@4
cd api && npm install && cd ..
swa start . --api-location api
```

## 배포

SWA 생성 시 GitHub Actions 워크플로가 자동 주입된다.
`app_location: "/"`, `api_location: "api"`, `output_location: ""`.

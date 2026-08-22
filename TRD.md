# TRD — Perp_Machine

> 기술 설계 (심사 Source of Truth). 제품은 [`PRD.md`](./PRD.md).
> 2026-08-22 12:15. **라이브 Node와 채점용 Python을 섞어 쓰지 마라.**

## 0. 지금 vs 다음

| | 보험 Node | 채점 URL (지금) |
|---|---|---|
| URL | https://righthon-hale.azurewebsites.net | https://righthon-py.azurewebsites.net |
| 런타임 | `NODE:22-lts` | `PYTHON:3.12` FastAPI |
| 모델 | Azure `gpt-5-mini` 직접 | **같은 deployment.** `gpt-5.6-luna`는 이 구독 쿼터 0 |
| 도구 | 없음 | `fetch_macro` — Azure tool_calls 루프. MAF 패키지는 B1 pip가 502 |
| 스트리밍 | 없음 | 아직 JSON. SSE는 다음 |
| GitHub 토큰 | 없음 | **넣지 않음** (넣었다가 삭제) |

심사 에이전트는 **제출한 URL**과 이 문서의 채점 목표를 대조한다. Python이 뜨면 이 절의 “지금”을 갱신한다.

## 1. 리소스 (재생성 금지)

- RG `rg-matdathon` / 플랜 `asp-matdathon` B1+alwaysOn / koreacentral
- 모델 계정 `aif-matdathon-hale` deployment `gpt-5-mini` api-version `2025-04-01-preview`
- 앱 설정(기존, 값 출력 금지): `AZURE_OPENAI_ENDPOINT` `AZURE_OPENAI_KEY` `AZURE_OPENAI_DEPLOYMENT` `AZURE_OPENAI_API_VERSION`
- Python 앱에 **같은 값을** `AZURE_OPENAI_API_KEY` `AZURE_OPENAI_MODEL` 로 **추가**한다. 기존 키를 지우지 마.
- `SCM_DO_BUILD_DURING_DEPLOYMENT`: Node=`false`, Python=`true`

Aspire·새 Foundry·SWA·로그인 없음.

## 2. 채점 스택 (한 프로세스)

```
브라우저
  GET  /              public/index.html  (계기판 UI)
  GET  /api/board     서버가 WB/BIS/ECB fetch → JSON 카드
  GET  /healthz
  POST /api/chat      GitHubCopilotAgent
                        ├ instructions = doctrine/dalio.md (배포물에 포함)
                        ├ tools: 같은 fetch (보드와 공유)
                        └ BYOK azure → gpt-5-mini
```

77단 코드·델타·페도라는 **import하지 않는다.** 달리오 원전 PDF를 레포에 넣지 않는다(저작권). 우리가 쓴 `doctrine/dalio.md`만 zip에 넣는다.

패키지 (`requirements.txt` 루트):

```
agent-framework==1.15.0
agent-framework-github-copilot==1.0.3
fastapi
gunicorn
uvicorn
```

`copilot-sdk`라는 틀린 문서명을 설치하지 마. yfinance는 **넣지 마** (우선순위 아님, Azure IP에서 Yahoo가 자주 막힘).

## 3. 필수 기술 충족

| 필수 | 지금 |
|---|---|
| Microsoft Agent Framework | 코드에 `GitHubCopilotAgent` 경로 있음. **B1 Oryx pip가 502라 패키지 미설치.** import 실패 시 Azure tool loop |
| GitHub Copilot SDK | 동일. GitHub 토큰은 앱 설정에 **두지 않음** |
| 도구 호출 | `board.fetch_macro` + Azure `tool_calls` |
| 스트리밍 | **미구현** (JSON POST) |
| Azure | B1 + alwaysOn. `/healthz` |

GitHub 토큰 금지. Copilot 내장 shell/file은 deny. 우리가 준 함수만.

`provider.base_url` = 엔드포인트 **호스트만**. `max_tokens` 금지.

## 4. 지표 수급 (도구가 침)

| 지표 | 코드 | 비고 |
|---|---|---|
| 실질금리 | WB `FR.INR.RINR` | F1 핵심. 연간 |
| 인플레 | WB `FP.CPI.TOTL.ZG` | |
| GDP 성장 | WB `NY.GDP.MKTP.KD.ZG` | |
| 정부부채/GDP | WB `GC.DOD.TOTL.GD.ZS` | BC Ch.17 |
| 외환보유 | WB `FI.RES.TOTL.CD` | 단위 USD. 나눗셈 시 단위 명시 |
| 신용갭·DSR | BIS SDMX | 시차 큼 |
| 유로 정책금리 | ECB `FM`/`IRS` | |
| IMF | — | **호출 금지** (중단) |
| FRED 커브·VIX | 키 필요 | F1 제외 |
| yfinance 주가 | — | 비목표. 이후 |

국가 코드 ISO2: KR US JP DE CN GB BR. 실패 시 짧은 에러 문자열을 에이전트에 돌려 환각 숫자를 막는다.

단위: 명목/실질 혼용 금지. 퍼센트 vs 십억 혼용 금지 (77단 실측 함정).

## 5. HTTP

### `POST /api/chat`

요청: `{ "message": "한국 실질금리" }`
성공 200: `{ "reply": "..." }` 또는 SSE `text/event-stream`.

로그인 헤더 없음. 본문 1MB 상한. 업스트림 60s → 504.

### `GET /healthz`

`{ "ok": true, "runtime": "python", "agent": "GitHubCopilotAgent", "configured": true }`

(보험 Node는 당분간 `{ok, deployment, configured}` 유지.)

## 6. 프론트

`public/index.html` 한 장. textarea + 보내기 + 결과. 로딩·취소(AbortController)·“AI가 생성한 결과” 배지·양면 영역.
키·endpoint 없음. 반응형.

## 7. 배포

1. `az webapp create -n righthon-py ... --runtime PYTHON:3.12` (플랜 기존)
2. startup: `gunicorn -w 2 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000 main:app`
3. zip 루트: `main.py` `requirements.txt` `public/`
4. `/healthz` → `/api/chat` 200+도구 호출 로그 → 제출 URL 교체

`RuntimeSuccessful`은 증명이 아니다.

## 8. 책임 있는 AI

- 답에 출처 연도와 시리즈 ID
- 매매 문장 거부
- 프롬프트 인젝션: 도구 URL/키를 사용자 말로 바꾸지 않음
- 비밀은 앱 설정만

## 변경 이력

| 시각 | 내용 |
|---|---|
| 07:50 | Node 프록시 |
| 12:15 | 채점 목표 = Python MAF+SDK. 지표 수급. Node는 보험. |

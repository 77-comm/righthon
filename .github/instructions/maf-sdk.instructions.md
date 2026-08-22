---
applyTo: "**"
---

# MAF + Copilot SDK — 적용 명세 (다시 읽는 용)

작성: 2026-08-22 12:00. 구현 코드가 아니라 **어떻게 충족할지**의 정본.
배포 함정·패키지 핀은 `stack.instructions.md`. 배점은 `scoring.instructions.md`.

## 1. 왜 이 두 개인가

공식 README 필수요소:

- 웹앱
- **Microsoft Agent Framework** + **GitHub Copilot SDK**
- Azure 배포

심사 1번(25%): *에이전트 설계, 오케스트레이션, 도구 호출, 컨텍스트, 스트리밍. 기능 수보다 깊이.*

입력→모델→출력 프록시는 여기 점수가 거의 안 붙는다.

## 2. 한 줄 충족식

```python
from agent_framework.github import GitHubCopilotAgent
```

이 클래스 하나가 **MAF 에이전트이면서 Copilot SDK 런타임**이다.
모델은 **Azure BYOK**(`provider.type=azure`)로 이미 있는 `gpt-5-mini`에 붙인다.

- GitHub 토큰 **넣지 마.** 공개 URL이 개인 쿼터를 먹는다.
- 공식 문서 `pip install copilot-sdk`는 **틀린 이름**. 패키지는
  `agent-framework-github-copilot==1.0.3`이 `github-copilot-sdk==1.0.2`를 끌어온다.

## 3. 네 단을 한 프로세스에 접기

유저스틴 데모의 네 제품 ≠ 우리 서버 네 대.

| 단 | 데모 | 우리 (App Service 1개) |
|---|---|---|
| 모델 | Foundry | 기존 `aif-matdathon-hale` / `gpt-5-mini` |
| 오케스트레이션 | MAF | `GitHubCopilotAgent` + (여유 있으면) 역할 2–3 |
| 도구 | MCP 서버 | **파이썬 함수 도구** 1–2개. MCP 서버 신설 금지 |
| 호스팅 | Aspire | 기존 플랜. Aspire 금지 |

프론트 `public/` + FastAPI + 에이전트 + 도구가 **같은 프로세스**.

## 4. 채점에 보이게 할 최소 동작

첫 성공 슬라이스 (이 순서):

1. `GET /healthz` 200 — Python 앱이 떴다
2. `POST /api/chat` 가 `GitHubCopilotAgent` 를 탄다 (import·클래스명이 레포에 있다)
3. 에이전트가 **도구를 실제로 호출**한다 (거시 조회 1개)
4. 응답이 **스트리밍**되거나, 최소한 스트림 API를 서버가 노출한다
5. TRD에 위 네 줄이 적혀 있다 (안 적으면 심사 에이전트가 모를 수 있다)

그 다음 살:

- 달리오 / 소로스 / Taleb **같은 모델·다른 instructions**
- 사회자가 합의·이견을 묶음
- 매 요청마다 도구가 공개 API를 친다 (최신성)

하지 마: 벤더 3개, 라이브 백테스트, 로그인, 새 Foundry, Aspire, GitHub 토큰.

## 5. 코드 스케치 (아직 레포에 넣지 않음)

```python
from agent_framework.github import GitHubCopilotAgent

async def fetch_macro(indicator: str) -> str:
    """World Bank / BIS / ECB 중 키 없는 것 1개. 실패하면 짧은 에러 문자열."""
    ...

agent = GitHubCopilotAgent(
    instructions="reasoning aid. 매수/매도 금지. 도구 숫자를 인용할 것.",
    default_options={
        "model": "gpt-5-mini",
        "provider": {
            "type": "azure",
            "base_url": "<AZURE_OPENAI_ENDPOINT host only>",
            "api_key": "<AZURE_OPENAI_API_KEY>",
        },
    },
    tools=[fetch_macro],
)
```

- `base_url` = **호스트만.** `/openai/v1` 붙이지 마.
- `max_tokens` 금지. 한도 필요하면 `additional_chat_options.max_completion_tokens` 시도, 실패하면 생략.
- 공개 앱: Copilot 내장 shell/file 권한 **끄거나 deny.** 도구는 우리가 준 함수만.
- 세션/쿠키 없음. 요청마다 독립 (로그인 없이 심사 가능).

환경변수 두 벌 (`stack.instructions.md` 표): 어제 넣은 `AZURE_OPENAI_KEY` 와 MAF가 찾는 `AZURE_OPENAI_API_KEY` 를 **같은 값으로** 앱 설정에 더한다. 기존 4개를 지우거나 재생성하지 마.

## 6. 배포 순서 (Node 보험을 죽이지 않음)

1. 같은 플랜에 Python 웹앱을 **새로** 만든다 (`righthon-py`). `righthon-hale`은 200이 나올 때까지 유지.
2. `SCM_DO_BUILD_DURING_DEPLOYMENT=true`, startup `gunicorn ... main:app`
3. `COPILOT_CLI_EXTRACT_DIR=/home/copilot-cli` + 가능하면 `python -m copilot download-runtime`
4. `/healthz` → `/api/chat` 200+비공백 → 그때 제출 URL을 고른다

로컬: Python 3.12가 이상적. 맥에 3.13만 있으면 로컬은 3.13로 스모크, 앱은 `PYTHON:3.12`.

## 7. PRD/TRD에 박을 문장 (채점용)

PRD가 할 일 앱으로 남아 있으면 2번(18%)이 제품과 어긋난다. hale 피드백 후 바꿀 것. 초안:

- 대상: 포지션을 앱에 말할 수 없는 개인 (로그인 없음)
- 문제: 같은 실질금리가 채권자엔 매력, 채무자엔 비용
- F1: WB/BIS/ECB 조회 (`FR.INR.RINR` 등)
- F2: lender-creditor **와** borrower-debtor를 항상 같이. 올웨더 일변 금지
- 비목표: 매매, 로그인, yfinance(우선 아님), 라이브 백테스트, IMF

TRD: `GitHubCopilotAgent` + BYOK azure + 함수 도구 + 스트리밍 + B1 alwaysOn + `/healthz`.

## 8. 공식 링크

- https://learn.microsoft.com/en-us/agent-framework/integrations/by-component/agent-services/github-copilot
- https://docs.github.com/en/copilot/how-tos/copilot-sdk/integrations/microsoft-agent-framework
- https://github.com/matdaaiga-kr/matdathon-2026/blob/main/README.md
- https://github.com/matdaaiga-kr/matdathon-2026/blob/main/judgement/judgement-criteria.md

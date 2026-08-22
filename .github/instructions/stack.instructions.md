---
applyTo: "**"
---

# 🔴 스택 전환 지시 — 2026-08-22 10:50 필수요소 공개분

**이 파일이 `AGENTS.md`의 Node 서술과 충돌하면 이 파일이 이긴다.**
`AGENTS.md`의 스택·배포 절은 Node 전제라 **폐기**됐다. Azure 리소스·함정·공식 공지 절은 유효하다.

## 공개된 필수요소 (README)

```
- 반드시 웹 앱으로 개발할 것
- 반드시 Microsoft Agent Framework과 GitHub Copilot SDK 사용할 것
- 반드시 Azure 플랫폼으로 배포할 것
```

**Node.js로는 불가능하다.** Microsoft Agent Framework 1.0 GA는 **.NET·Python만** 지원한다(JS/TS 없음).
⇒ **Python으로 간다.**

## 🎯 두 요건을 한 번에 충족하는 형태

```python
from agent_framework.github import GitHubCopilotAgent
```

MAF 에이전트이면서 Copilot SDK를 쓰는 공식 래퍼다. 여기에 **Azure BYOK** provider를 물리면
**GitHub 토큰·Copilot 구독이 필요 없고** 과금은 우리 Azure OpenAI로 간다.

> 공식: *"a GitHub Copilot subscription is required … **unless you are using BYOK**"*
> *"Usage is tracked by **your provider**, not GitHub Copilot."*

🔴 **개인 GitHub 토큰을 App Setting에 넣지 마라.** 공개 앱이라 모든 방문자 호출이 개인 쿼터를 먹고,
자격증명이 공개 배포물에 들어간다. BYOK가 정공법이다.

## 패키지 — 정확히 이것만

> 🔴 **14:45 원인 정정 — B1이 아니라 PyPI가 문제다.**
> 래퍼 1.0.3이 핀한 `github-copilot-sdk==1.0.2`가 **PyPI에서 소멸**(1.0.4+만 생존) →
> requirements.txt에 MAF를 넣으면 **어떤 pip에서도 ResolutionImpossible** → Oryx 빌드 사망(503)은 그 증상.
> **해법(적용됨):** `deploy-py.sh`가 리눅스 cp312 wheel을 `packages/`에 조립해 zip 동봉.
> `agent-framework-core==1.15.0` + `github-copilot-sdk==1.0.4` 정상 설치, 래퍼는 `--no-deps`.
> 맥 venv에서 1.0.4+래퍼 조합 import·생성 검증 완료. `main.py`가 sys.path에 packages/를 얹는다.
> **requirements.txt에는 fastapi/uvicorn/gunicorn 3개만 남긴다(Oryx 담당). MAF를 되넣지 마라.**
> 메타패키지 `agent-framework==1.15.0`([all] 익스트라)도 크로스플랫폼 해석이 깨진다 — **core만** 써라.

```
agent-framework==1.15.0
agent-framework-github-copilot==1.0.3
fastapi
gunicorn
uvicorn
```

🔴 **함정 2개. 둘 다 실제로 밟게 되어 있다:**

1. **GitHub 공식 문서가 패키지명을 틀리게 적는다** — 문서는 `pip install copilot-sdk`라고 하지만
   **PyPI 정본은 `github-copilot-sdk`**. 문서를 근거로 치면 실패한다.
   그리고 우리는 **직접 설치하지 않는다** — `agent-framework-github-copilot==1.0.3`이 끌어온다.
2. **버전 핀 충돌** — `agent-framework-github-copilot==1.0.3`의 의존성이
   **`github-copilot-sdk==1.0.2`로 고정**돼 있다. `1.0.11`을 따로 핀하면 pip가 깨진다. **올리지 마라.**

Python은 **3.11 이상** 필요(Copilot SDK·MAF GitHub 패키지 요구). 우리는 **3.12**를 쓴다.

## 환경변수 — 이름이 두 벌이다

MAF가 찾는 이름과 우리가 어제 넣은 이름이 다르다. **양쪽 다 같은 값으로 주입돼 있다:**

| 우리가 넣은 것(어제) | MAF가 찾는 것 | 값 |
|---|---|---|
| `AZURE_OPENAI_KEY` | `AZURE_OPENAI_API_KEY` | (동일) |
| `AZURE_OPENAI_DEPLOYMENT` | `AZURE_OPENAI_MODEL` | `gpt-5-mini` |
| `AZURE_OPENAI_ENDPOINT` | 동일 | `https://aif-matdathon-hale.cognitiveservices.azure.com/` |
| `AZURE_OPENAI_API_VERSION` | 동일 | `2025-04-01-preview` |

⚠️ BYOK provider의 `base_url`은 **host만** 넣는다. `/openai/v1` 같은 경로를 붙이지 마라.
⚠️ `type`은 반드시 **`azure`** (`openai` 아님).
⚠️ `OPENAI_API_KEY`가 환경에 있으면 Azure env가 있어도 OpenAI로 샌다. `azure_endpoint`를 명시하라.

## 🔴 gpt-5-mini 파라미터

- **`max_tokens` 금지.** gpt-5 계열은 거부한다. `temperature`·`top_p`·penalty도 미지원.
- 한도를 걸어야 하면 `additional_chat_options={"max_completion_tokens": N}` 패스스루를 시도하되,
  **이 키가 실제로 통과하는지 미확인**이다. 안 되면 **한도를 생략하라.**
- 이 한도는 reasoning 토큰까지 소모해서, 낮으면 **HTTP 200에 빈 content**가 온다.

## 배포 — App Service Python

```bash
# 새 웹앱(기존 Node를 죽이지 않는다. B1 플랜은 앱 8개까지)
az webapp create -n righthon-py -g rg-matdathon -p asp-matdathon --runtime "PYTHON:3.12"

# startup — 3.12는 자동탐지가 안 된다. 반드시 지정
az webapp config set -n righthon-py -g rg-matdathon \
  --startup-file "gunicorn -w 2 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000 main:app"
```

🔴 **`SCM_DO_BUILD_DURING_DEPLOYMENT=true`** 여야 Oryx가 `requirements.txt`를 설치한다.
Node 때는 `false`였다. **false로 두면 `ModuleNotFoundError`가 난다.**

🔴 **Copilot SDK는 CLI 바이너리를 자식 프로세스로 실행한다.** App Service는 `/home`만 영속이라
`COPILOT_CLI_EXTRACT_DIR=/home/copilot-cli`를 주고, 가능하면
`POST_BUILD_COMMAND='python -m copilot download-runtime'`로 미리 받아둔다.
안 하면 **첫 채팅 요청이 30초 이상 멈춘다.**

- `requirements.txt`는 **zip 루트**에 있어야 한다. `venv`·`.git`을 zip에 넣지 마라.
- 배포: `az webapp deploy -g rg-matdathon -n righthon-py --src-path <zip> --type zip`

## 배포 실패 진단 순서

1. `ModuleNotFoundError` → `SCM_DO_BUILD_DURING_DEPLOYMENT` 확인. Oryx 로그에
   *"Not running pip install"* 이 있으면 이것이다.
2. 기본 Python 페이지 또는 502 → **startup 미설정**. `az webapp log tail`로 확인.
3. 첫 요청 hang → Copilot CLI 런타임 미다운로드. `az webapp ssh`로 `/home/copilot-cli` 확인.

## ⚠️ 변하지 않는 원칙

- **빈 껍데기를 먼저 배포해 200을 확인한 뒤 살을 붙인다.** 11:00에 에이전트부터 짜지 마라.
- **`az webapp deploy`의 `RuntimeSuccessful`은 동작 증명이 아니다.** `/healthz` + 실제 채팅 200까지 봐야 한다.
- 기존 Node 앱(`righthon-hale`)은 **성공할 때까지 살려둔다.** 제출 URL은 마지막에 정한다.
- 정적 파일은 `public/`에만. 루트를 서빙하면 소스가 노출된다.
- 인증(로그인·회원가입)을 붙이면 **전 평가항목 최저점 1점**이다.

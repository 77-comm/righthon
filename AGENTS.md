# righthon — 현장 메모리 (2026-08-22)

> 🔴 **10:50 필수요소 공개로 스택이 바뀌었다. 아래 「스택」 서술(Node·의존성 0)은 폐기.**
> **`.github/instructions/stack.instructions.md`를 먼저 읽어라.** 그 파일이 이 문서를 이긴다.
> MAF+SDK 충족식은 **`.github/instructions/maf-sdk.instructions.md`**.
> 살아 있는 절: **Azure 리소스 · 실측 함정 · 공식 공지 · 제출 이슈 3종.**

**라이브(제출 URL):** https://righthon-hale.azurewebsites.net  ← 지금 살아 있음.
**배포:** `./deploy.sh` 한 줄. zip(`public` `server.js` `package.json`) → `az webapp deploy` → `/healthz`. 약 40초. GitHub Actions 없음(CI 왕복 2~3분 회피).
**스택:** App Service Linux **B1 Basic + alwaysOn** · koreacentral · deployment `gpt-5-mini`.
🔴 ~~`NODE:22-lts` · 의존성 0~~ **폐기** — 필수요소가 MAF+Copilot SDK를 강제 → **Python**. `stack.instructions.md`.
**레포:** `77-comm/righthon` · `main` · 당일 베이스 `92baf6e`.
**Azure (전부 생성됨·재생성 금지):** RG `rg-matdathon` / 플랜 `asp-matdathon` / 웹앱 `righthon-hale` / 모델 `aif-matdathon-hale` · koreacentral.
앱 설정 6개 주입 완료: `AZURE_OPENAI_ENDPOINT` `AZURE_OPENAI_KEY` `AZURE_OPENAI_DEPLOYMENT` `AZURE_OPENAI_API_VERSION`(=2025-04-01-preview) `SCM_DO_BUILD_DURING_DEPLOYMENT=false` `WEBSITE_NODE_DEFAULT_VERSION=~22`.
**다시 넣지 마. 값을 stdout에 찍지 마.** 충돌하면 `.github/copilot-instructions.md`(F1 초안)보다 **이 파일이 이긴다.**

## 실측 함정 — 이유 없이 지키면 안 지켜진다

1. **`gpt-5-mini`는 `max_tokens`를 거절한다** → `max_completion_tokens`(현재 4000). 이 한도는 reasoning 토큰까지 같이 깎아서, 낮으면 **HTTP 200인데 `content`가 `""`**. 에러가 아니라 성공이라 프론트·라우팅을 파게 된다.
2. **`az webapp deploy`의 `RuntimeSuccessful`은 동작 증명이 아니다.** Kudu가 zip을 풀었다는 뜻일 뿐. 배포 후 `/healthz`와 실제 `POST /api/chat` 200(+ content 비공백)까지 봐야 채점 대상이다.
3. **Static Web Apps는 이 구독에서 생성 불가**(`RequestDisallowedByAzure`). 정책 허용 리전 ∩ SWA 지원 리전 = ∅. `api/`·`staticwebapp.config.json`·SWA로 되돌리면 어제처럼 시간만 태운다.
4. **정적 파일은 `public/`에만.** 루트에 두면 정적 루트가 레포 루트가 되어 `/server.js`가 200으로 소스를 뱉는다(실측).
5. **`%2e%2e` 방어는 `url.pathname`이 퍼센트 디코딩을 안 해서 성립한다.** 경로에 `decodeURIComponent`를 씌우면 `..`가 살아나 경로 이탈이 열린다.
6. **콜드스타트는 B1+alwaysOn으로 제거됨**(F1일 때 27.6초). 오늘 F1으로 내리면 심사 첫 요청이 타임아웃 난다. SKU 내리지 마.
7. **MAF는 Oryx pip 금지.** `github-copilot-sdk==1.0.2`는 PyPI에서 사라졌다. `deploy-py.sh`가 `packages/`(gitignore, ~26MB)에 wheel을 **한 번** 조립하고 다음부터 재사용한다. `PACKAGES_REBUILD=1`만 재조립. 배포가 이미 돌면 스크립트가 거부한다(겹치면 B1이 10분씩 죽는다). 업로드 자체는 수십 초. 남은 대기는 Kudu 기동이지 인터넷이 아니다. **requirements.txt에 MAF를 되넣지 마라.**

## 오늘 제약 (10:50 공개분 반영)

- 주제: **개인 생산성 향상 앱** (공식 README 표기. 메일의 "에이전트 앱"이 아니다)
- 🔴 **16:30 제출 마감. 초과 = 자동 탈락.** (종전 17:00은 **틀렸다** — 08-21 18:13 갱신됨)
- 필수요소: **Microsoft Agent Framework + GitHub Copilot SDK + Azure 배포**
- 기능은 **적게, 깊게.** 배점이 *"기능의 수보다 활용의 깊이"* → `scoring.instructions.md`
- **14:00 기능 동결 · 15:30 마지막 push · 16:00까지 제출 완료**(마감 30분 여유)
- **30분마다 배포 확인.** 링크가 살아야 채점된다
- 🔴 **새 Azure 서비스를 "더 좋아서" 추가하지 마 — 배점이 직접 감점한다**

## 명령 (복사해서 써라)

```bash
# 배포
./deploy.sh

# 헬스
curl -sS --max-time 30 https://righthon-hale.azurewebsites.net/healthz; echo

# 실제 채팅 경로 (200 + content 비어 있지 않은지)
curl -sS --max-time 60 -X POST https://righthon-hale.azurewebsites.net/api/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"ping"}'; echo

# 로그 (키·앱설정 값이 보이면 즉시 Ctrl+C. 채팅에 붙여넣지 마)
az webapp log tail -n righthon-hale -g rg-matdathon

# 로컬 :8080. 키는 az로 읽어 export만. echo/printf 하지 마.
export AZURE_OPENAI_ENDPOINT="https://aif-matdathon-hale.cognitiveservices.azure.com/"
export AZURE_OPENAI_DEPLOYMENT="gpt-5-mini"
export AZURE_OPENAI_API_VERSION="2025-04-01-preview"
export AZURE_OPENAI_KEY="$(az cognitiveservices account keys list -n aif-matdathon-hale -g rg-matdathon --query key1 -o tsv)"
node server.js
# 다른 터미널
curl -sS localhost:8080/healthz
```

## 파일 역할

| 경로 | 역할 |
|---|---|
| `public/index.html` | 프론트. 빌드 없음, 인라인 JS. `POST /api/chat`만 호출. |
| `server.js` | `node:http` 단일 프로세스. `public/` 정적 서빙 + `POST /api/chat` + `GET /healthz`. 의존성 0. |
| `package.json` | 🔴 **폐기**(Node용). Python은 `requirements.txt`. |
| `deploy.sh` | 화이트리스트 zip → 배포 → 헬스. 제외목록(`-x`)으로 바꾸지 마(새 파일이 새어나감). |
| `AGENTS.md` | 이 파일. Copilot CLI·VS Code Copilot이 읽는 당일 진실. |
| `.github/copilot-instructions.md` | 08-21 초안. **F1·Node·SWA 서술 전부 폐기.** |
| `.github/instructions/*.md` | 🎯 **자동 첨부 당일 정본.** scoring → stack → aspire 순 |
| `PRD.md` · `TRD.md` | 🎯 **AI 심사 Source of Truth.** 채점 대상 문서 |

🔴 이 절의 Node 전제(`server.js`·`npm`)는 폐기. **정적 파일은 `public/`에만** 두는 규칙은 유효하다.

## 공식 공지 — 여기가 정본이다

우리 레포는 무대일 뿐, 규칙·일정·제출의 정본은 공식 레포다. 운영진이 당일에도 갱신한다(어제 18:13 커밋으로 마감 17:00 → **16:30**). 한 번 읽었다고 끝내지 마라.

정본: https://github.com/matdaaiga-kr/matdathon-2026
- README: 시간표·도전과제·필수요소 — https://github.com/matdaaiga-kr/matdathon-2026/blob/main/README.md
- 규칙: https://github.com/matdaaiga-kr/matdathon-2026/blob/main/policies/policy-rules.md
- 심사: https://github.com/matdaaiga-kr/matdathon-2026/blob/main/judgement/judgement-criteria.md
- Discussions: [#7 GitHub 계정](https://github.com/matdaaiga-kr/matdathon-2026/discussions/7) · [#8 사전 준비](https://github.com/matdaaiga-kr/matdathon-2026/discussions/8) · [#2 Azure](https://github.com/matdaaiga-kr/matdathon-2026/discussions/2)

오늘 일정 (README): 09:00-09:30 체크인 | 09:30-09:40 오프닝 | 09:40-10:20 키노트 | 10:20-10:50 커뮤니티 | 10:50-11:00 도전과제 세부+심사 안내 | 11:00-16:30 해커톤(5시간 30분, 중식) | 16:30-17:30 심사·발표 | 17:30-18:00 시상

🔴 **제출할 이슈는 3개다** — https://matdaaiga.kr/matdathon/issues (빈 이슈 불가, 템플릿만)

| # | 템플릿 | **누가** | 언제 | 핵심 제약 |
|---|---|---|---|---|
| 1 | `01-github-handle` 🪪 | ⚠️ **운영진일 가능성이 높다** (아래 참조) | 체크인 시점 | 제목 `[handle] <핸들>`, `@` 없이. **Copilot 라이선스가 하나도 안 붙은 개인 계정** → **`hale-righthon`**. QR(`images/ghcp-check.png`)로 "라이선스 없음/Free" 화면 확인 |
| 2 | `02-team-building` 🏷️ | ✅ **참가자 본인(팀 리더)** | **결과 제출 전 아무 때나** | 제목 `[team] <팀이름>`. **마감 없으나 제출 전 필수.** 팀명 **고유**(대소문자 무시). **리더=이슈 작성자.** 단독은 멤버 공란. 재제출=**업데이트**(중복 생성 안 됨) → 이름은 나중에 바꿔도 된다 |
| 3 | `03-result-submission` 🚀 | ✅ **참가자 본인** | **~16:30** | 앱 제목 · **공개 레포 URL** · **커밋 해시** · **배포 URL** · (선택)설명 |

⚠️ **2번을 빼먹으면 3번이 무효다.** 팀 등록 없이 결과만 내면 안 된다. 체크인 직후 바로 걸어둬라.

### 1번은 누가 여는가 — **명시돼 있지 않다. 현장 안내를 따르라**

문서에 딱 잘라 쓰인 곳이 없다. 다만 **인칭이 갈린다**:
- `01`: *"입력한 핸들은 **체크인한 참가자의** GitHub 계정임을 확인했습니다"* → **3인칭 = 접수자의 언어**
- `02`: *"**나는** 팀 리더이며, **내** GitHub 계정으로 이 이슈를 열고 있습니다"* → **1인칭 = 참가자**

⇒ 1번은 **운영진이 체크인 접수하며 대신 여는 쪽**으로 읽힌다.
**체크인 데스크에서 시키는 대로 하라.** 핸들을 물어보면 **`hale-righthon`** 이라고 답하면 되고,
직접 열라고 하면 그때 열면 된다. **어느 쪽이든 2·3번은 본인이 연다.**
**마감 16:30. 초과 = 자동 탈락.** 결과 제출 최대 2회, 마지막 것으로 평가 → 중간에 1차 내고 마감 전 갱신하라.
AI 심사 에이전트가 자동 심사. 루트 `PRD.md`(제품)·`TRD.md`(기술)가 Source of Truth, `README.md`는 보조.
🔴 로그인·회원가입·계정·초대·권한을 요구하면 전 평가항목 최저점(1점). 인증 붙이지 마라.
레포는 **public**이어야 한다 (`77-comm/righthon` 08-22 08:05 전환 완료).

**✅ 11:00 공개분 확인 완료**
- [x] 필수요소 → **Microsoft Agent Framework + GitHub Copilot SDK** → `stack.instructions.md`
- [x] 심사 기준 → **7항목 배점 공개** → `scoring.instructions.md`

hale Instruction: 유저스틴의 키노트 참조할 것. 다른 모델로 검증 및 왜 이 결과가 나왔는지 체크할 필요 존재. 
메모리 적극적으로 활용할 것. 
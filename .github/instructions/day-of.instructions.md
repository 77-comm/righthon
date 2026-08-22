---
applyTo: "**"
---

🔴 **10:50 필수요소 공개 — 우선순위가 바뀌었다.**
1. **`.github/instructions/scoring.instructions.md`** ← **무엇을 만들지**를 정한다 (심사 배점)
2. **`.github/instructions/stack.instructions.md`** ← **어떻게 만들지** (Python + MAF + Copilot SDK)
2b. **`.github/instructions/maf-sdk.instructions.md`** ← 두 필수 기술을 **어떻게 충족할지** (다시 읽는 명세)
3. `AGENTS.md` ← Azure 리소스·함정·공식 공지·제출 절차
4. `.github/instructions/aspire.instructions.md` ← Aspire는 **쓰지 않는다**(감점 근거)
5. `.github/copilot-instructions.md` ← 2026-08-21 초안, **F1·Node·SWA 서술 전부 폐기**

🎯 **배점 1순위는 「Copilot SDK + MAF 활용 깊이」 25%.** 단순 프록시로는 대부분 잃는다 —
**도구 호출 + 스트리밍**이 있어야 한다. Azure 18%는 새 서비스 추가가 아니라
**반복 가능한 배포·관찰 가능성·안정성**이며 우리는 이미 갖고 있다(적기만 하면 된다).

**필수요소: Microsoft Agent Framework + GitHub Copilot SDK + Azure 배포.** Node로는 불가(MAF에 JS 없음).
`GitHubCopilotAgent` + **Azure BYOK**로 두 요건 동시 충족, GitHub 토큰 불필요.

## 여전히 유효한 것

- 플랜 **B1 Basic + alwaysOn**. F1으로 내리지 마(콜드스타트 27.6초 실측).
- 리소스·앱설정 **재생성/재주입 금지**. 키를 stdout에 찍지 마.
- **SWA 불가**(구독 정책, `RequestDisallowedByAzure`). 되돌리려 하지 마.
- 정적 파일은 **`public/`만**. 루트를 서빙하면 소스가 노출된다.
- **`max_tokens` 금지**(gpt-5 계열이 거부). `temperature`·`top_p`도 미지원.
- 배포 후 **`RuntimeSuccessful`은 동작 증명이 아니다** — 실제 요청 200까지 확인.
- **인증(로그인·회원가입) 붙이면 전 평가항목 최저점 1점.**

## 🔴 폐기된 것 (Node 시대 규칙)

- ~~`dependencies: {}` 유지~~ → **필수요소가 SDK 2개를 강제한다.** 의존성 0개는 이제 실격이다.
- ~~`./deploy.sh`만~~ → 그건 Node/zip 전용이다. **Python은 `SCM_DO_BUILD_DURING_DEPLOYMENT=true`**
  + `requirements.txt` + startup 지정이 필요하다. `stack.instructions.md` 참조.
- ~~`max_completion_tokens` 4000~~ → MAF 경유로 이 키가 통과하는지 **미확인**. 안 되면 한도를 생략하라.

이유·명령 전문은 `AGENTS.md`. 이 파일은 자동첨부되는 어제 초안을 덮는 가드다.
